import asyncio
import re
import os
import json
import time
import base64
import uuid
import requests
import mimetypes
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, Optional, List
from pathlib import Path

from open_webui.config import CACHE_DIR

DEBUG = True

IMAGE_CACHE_DIR = Path(CACHE_DIR).joinpath("image/generations/")
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class Action:
    class Valves(BaseModel):
        FLUX_API_URL: str = Field(
            default="https://api.bfl.ml/v1",
            description="Basic URL of the FLUX API (без завершающего /)",
        )
        FLUX_API_KEY: str = Field(
            default="YOUR-FLUX-API-KEY",
            description="API key для аутентификации",
        )
        STEPS: int = Field(
            default=50,
            description="Число итераций при генерации: 1..100",
        )
        GUIDANCE: int = Field(
            default=50,
            description="Guidance scale: 15..50",
        )
        SAFETY_TOLERANCE: int = Field(
            default=6,
            description="Модерация: 0..6",
        )
        OUTPUT_FORMAT: str = Field(
            default="jpeg",
            description="Формат вывода (jpeg или png).",
            enum=["jpeg", "png"],
        )
        POLL_INTERVAL: int = Field(
            default=2,
            description="Интервал (сек) между запросами get_result",
        )
        MAX_POLL_ATTEMPTS: int = Field(
            default=60,
            description="Макс. число попыток при опросе (пока генерируется картинка).",
        )

    def __init__(self):
        self.valves = self.Valves()
        # Флаг, показывающий, что HTML-артефакт «в процессе» (активен)
        self._artifact_in_use = False

    def status_object(
        self, description: str, status: str = "in_progress", done: bool = False
    ) -> Dict:
        return {
            "type": "status",
            "data": {
                "status": status,
                "description": description,
                "done": done,
            },
        }

    def find_generated_image_path(self, messages: List[Dict]) -> Optional[str]:
        """
        Ищем последнюю сгенерированную картинку формата: ![BFL Image](...)
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and "![BFL Image](" in msg.get(
                "content", ""
            ):
                match = re.search(r"!\[BFL Image\]\(([^)]+)\)", msg["content"])
                if match:
                    return match.group(1)
        return None

    def find_existing_artifact_message(self, messages: List[Dict]) -> Optional[Dict]:
        """
        Ищем последнее сообщение с HTML/JSON кодом (artifact),
        чтобы при необходимости обновлять его через edit_message.
        Ищем по наличию маркера "Inpainting Helper" или блоков кода.
        """
        for msg in reversed(messages):
            content = msg.get("content", "")
            if msg.get("role") == "assistant" and (
                "Inpainting Helper" in content
                or "```html" in content
                or "```json" in content
            ):
                return msg
        return None

    def save_url_image(self, url: str) -> str:
        """
        Скачиваем картинку по ссылке и сохраняем локально в /cache/image/generations.
        Возвращаем путь, по которому потом картинка доступна.
        """
        image_id = str(uuid.uuid4())
        try:
            response = requests.get(url)
            response.raise_for_status()
            mime_type = response.headers.get("content-type", "")
            ext = mimetypes.guess_extension(mime_type) or ".jpg"
            file_path = IMAGE_CACHE_DIR / f"{image_id}{ext}"
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return f"/cache/image/generations/{file_path.name}"
        except Exception as e:
            raise RuntimeError(f"Ошибка при скачивании картинки: {e}")

    async def action(
        self,
        body: dict,
        __id__: str = None,  # action ID
        __user__: dict = None,
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> Optional[dict]:
        """
        Основной метод плагина.
        1) Если есть image/mask/prompt => выполняем inpainting (FLUX).
        2) Если нет — рендерим/обновляем HTML-артефакт для рисования маски
           (но не даём делать это повторно, пока артефакт активен).
        """

        # Значения по умолчанию (Open WebUI их требует)
        body.setdefault("model", "flux_test_7.flux-1-1-pro")
        body.setdefault("chat_id", "dummy_chat_id")
        body.setdefault("session_id", "dummy_session_id")
        body.setdefault("id", "dummy_message_id")

        if DEBUG:
            print(f"\n[DEBUG] action {__id__} получил запрос. body = {body}")

        messages = body.get("messages", [])

        # Первичный статус
        if __event_emitter__:
            await __event_emitter__(
                self.status_object("Processing request...", "in_progress", False)
            )

        # Проверяем, какой сценарий: inpainting или запрос на рендер артефакта
        is_inpainting_call = all(k in body for k in ("image", "mask", "prompt"))

        # ---------------------------------------------------------------------
        # ЕСЛИ ВЫЗВАН ИНПЕЙНТИНГ
        # ---------------------------------------------------------------------
        if is_inpainting_call:
            if DEBUG:
                print("[DEBUG] Обнаружены image/mask/prompt => запускаем inpainting")

            # Разрешаем многократные вызовы inpainting, т.к. пользователь может нажать несколько раз
            # Но по завершении сбрасываем _artifact_in_use, т.к. артефакт более не актуален.
            try:
                image_b64 = body["image"]
                mask_b64 = body["mask"]
                prompt_str = body["prompt"]

                steps_val = body.get("steps", self.valves.STEPS)
                guidance_val = body.get("guidance", self.valves.GUIDANCE)
                output_format_val = body.get("output_format", self.valves.OUTPUT_FORMAT)
                safety_val = body.get("safety_tolerance", self.valves.SAFETY_TOLERANCE)

                if DEBUG:
                    print(
                        "[DEBUG] Параметры inpainting:",
                        {
                            "prompt": prompt_str,
                            "steps": steps_val,
                            "guidance": guidance_val,
                            "format": output_format_val,
                            "safety": safety_val,
                        },
                    )

                if __event_emitter__:
                    await __event_emitter__(
                        self.status_object("Sending the task to FLUX...", "in_progress")
                    )

                # 1) POST-запрос к FLUX
                try:
                    flux_response = requests.post(
                        f"{self.valves.FLUX_API_URL}/flux-pro-1.0-fill",
                        headers={
                            "Content-Type": "application/json",
                            "x-key": self.valves.FLUX_API_KEY,
                        },
                        json={
                            "image": image_b64,
                            "mask": mask_b64,
                            "prompt": prompt_str,
                            "steps": steps_val,
                            "guidance": guidance_val,
                            "output_format": output_format_val,
                            "safety_tolerance": safety_val,
                        },
                        timeout=30,
                    )
                    flux_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    msg = f"Ошибка при запросе к FLUX: {e}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}

                flux_json = flux_response.json()
                task_id = flux_json.get("id")
                if not task_id:
                    msg = f"Flux не вернул id задачи: {flux_json}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}

                # 2) Пулинг результата
                max_attempts = self.valves.MAX_POLL_ATTEMPTS
                poll_interval = self.valves.POLL_INTERVAL
                image_url = None

                for attempt in range(max_attempts):
                    time.sleep(poll_interval)

                    if DEBUG:
                        print(
                            f"[DEBUG] Polling FLUX (attempt {attempt+1}/{max_attempts}) task_id={task_id}"
                        )

                    try:
                        check_resp = requests.get(
                            f"{self.valves.FLUX_API_URL}/get_result",
                            headers={
                                "Content-Type": "application/json",
                                "x-key": self.valves.FLUX_API_KEY,
                            },
                            params={"id": task_id},
                            timeout=60,
                        )
                        check_resp.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        msg = f"Ошибка при получении результата FLUX: {e}"
                        if DEBUG:
                            print(msg)
                        if __event_emitter__:
                            await __event_emitter__(
                                self.status_object(msg, "error", True)
                            )
                        return {"status": "error", "message": msg}

                    rjson = check_resp.json()
                    status_ = rjson.get("status")

                    if DEBUG:
                        print(f"[DEBUG] Flux status={status_}")

                    if __event_emitter__ and status_ not in ["Pending", "Processing"]:
                        await __event_emitter__(
                            self.status_object(
                                f"Flux status: {status_}", "in_progress", done=False
                            )
                        )

                    if status_ == "Ready":
                        result_obj = rjson.get("result", {})
                        image_url = result_obj.get("sample")  # ссылка на итог
                        break
                    elif status_ in [
                        "Error",
                        "Content Moderated",
                        "Request Moderated",
                        "Task not found",
                    ]:
                        msg = f"Flux вернул статус: {status_}"
                        if DEBUG:
                            print(msg)
                        if __event_emitter__:
                            await __event_emitter__(
                                self.status_object(msg, "error", True)
                            )
                        return {"status": "error", "message": msg}
                    # иначе крутим цикл дальше

                if not image_url:
                    msg = "Flux не вернул результат за отведённое время"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}

                # 3) Скачиваем итоговую картинку
                if __event_emitter__:
                    await __event_emitter__(
                        self.status_object(
                            "Uploading the final image...", "in_progress"
                        )
                    )
                try:
                    local_image_path = self.save_url_image(image_url)
                except Exception as e:
                    msg = f"Ошибка при загрузке картинки: {e}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}

                # 4) Выводим готовую картинку в чат
                content_msg = f"Result inpainting:\n\n![BFL Image]({local_image_path})"
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {"role": "assistant", "content": content_msg},
                        }
                    )
                    await __event_emitter__(
                        self.status_object(
                            "Done! The result of inpainting is obtained.",
                            "complete",
                            True,
                        )
                    )

                return {"status": "ok", "message": "Inpainting is complete"}

            finally:
                # По завершении инпейнтинга (даже при ошибках) сбрасываем флаг.
                # Артефакт более неактуален.
                self._artifact_in_use = False

        # ---------------------------------------------------------------------
        # ЕСЛИ НЕТ ИНПЕЙНТИНГ-ДАННЫХ => РЕНДЕР/ОБНОВЛЕНИЕ HTML АРТЕФАКТА
        # ---------------------------------------------------------------------
        else:
            # Проверяем: если артефакт уже активен, не даём снова его вызвать
            if self._artifact_in_use:
                msg = (
                    "Артефакт уже активен. Дождитесь завершения или используйте "
                    "существующий, прежде чем снова вызывать action."
                )
                if DEBUG:
                    print("[DEBUG]", msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # Если артефакт не активен, включаем "режим занятости"
            self._artifact_in_use = True
            try:
                if DEBUG:
                    print("[DEBUG] Нет image/mask/prompt => отобразим HTML-инструмент")

                if __event_emitter__:
                    # Промежуточный статус
                    await __event_emitter__(
                        self.status_object(
                            "Prepare/update HTML...", "in_progress", False
                        )
                    )

                # Пытаемся найти последнюю сгенерированную картинку
                image_path = self.find_generated_image_path(messages)
                if not image_path:
                    error_msg = "Не найдена последняя сгенерированная картинка!"
                    if DEBUG:
                        print("[DEBUG]", error_msg)
                    if __event_emitter__:
                        await __event_emitter__(
                            self.status_object(error_msg, "error", True)
                        )
                    return {"status": "error", "message": error_msg}

                filename = os.path.basename(image_path)
                full_file_path = IMAGE_CACHE_DIR / filename
                if not full_file_path.exists():
                    error_msg = f"Файл не найден: {full_file_path}"
                    if DEBUG:
                        print("[DEBUG]", error_msg)
                    if __event_emitter__:
                        await __event_emitter__(
                            self.status_object(error_msg, "error", True)
                        )
                    return {"status": "error", "message": error_msg}

                steps_val = self.valves.STEPS
                guidance_val = self.valves.GUIDANCE
                safety_val = self.valves.SAFETY_TOLERANCE
                output_fmt = self.valves.OUTPUT_FORMAT

                # Содержимое HTML (artifact_html) – как было в оригинале.
                # ---------------------------------------------------------
                artifact_html = f"""
```html
<head><meta charset="UTF-8"><title>Inpainting Helper</title><style>body {{font-family: Arial, sans-serif;margin: 20px;background-color: #262626;display: flex;flex-direction: column;align-items: center;}}h1 {{padding-top: 1em;color: #ececec;}}.main-container {{width: 100%;max-width: 1000px;margin: 0 auto;}}.canvas-container {{position: relative;width: 100%;margin: 10px 0;background-color: #1a1a1a;border-radius: .75rem;border: 1px solid #333;}}#baseCanvas {{display: block;border-radius: .75rem;max-width: 100%;}}#overlayCanvas {{position: absolute;top: 0;left: 0;border-radius: .75rem;max-width: 100%;cursor: crosshair;display: block;}}.controls-container {{width: 100%;display: flex;justify-content: space-between;margin: 15px 0;}}.controls-left {{display: flex;flex-direction:row;width: 20em;flex-grow:1;gap: 10px;align-items: center;}}.controls-right {{display: flex;gap: 15px;align-items: center;margin-left:1em;}}.brush-controls {{display: flex;gap: 20px;align-items: center;}}.control-group {{display: flex;flex-direction: column;gap: 5px;}}.control-group label {{color: #ececec;font-size: 14px;}}.value-display {{color: #ececec;font-size: 14px;margin-left: 10px;min-width: 40px;}}input[type="range"] {{-webkit-appearance: none;width: 150px;height: 8px;background: #4b4b4b;border-radius: 4px;outline: none;}}input[type="range"]::-webkit-slider-thumb {{-webkit-appearance: none;width: 16px;height: 16px;background: #ececec;border-radius: 50%;cursor: pointer;}}input[type="range"]:hover {{background: #686868;}}button {{flex-grow: 1;padding: .7em 2em;font-size: 17px;cursor: pointer;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;font-weight: 500;transition: background-color 0.15s;opacity: 1;}}button:hover {{background: #686868;}}button:disabled {{background-color: #a9a9a9;color: #6d6d6d;cursor: not-allowed;opacity: 0.6;}}.btn-generate {{background-color: #ececec;color: black;}}.btn-generate:hover {{background: #ffffff;}}.input-group {{position: relative;margin: 10px 0;width: 100%;max-width: 1000px;}}.prompt-label {{color: #ececec;font-size: 16px;margin-bottom: 5px;display: block;}}.prompt-textarea {{width: 100%;height: 150px;margin: 10px 0;resize: vertical;border-radius: .75rem;background-color: #2f2f2f;color: #ececec;border: 1px solid transparent;padding: 10px;padding-right: 50px;box-sizing: border-box;font-family: Arial, sans-serif;font-size: 18px;transition: box-shadow 0.15s cubic-bezier(.4, 0, .2, 1), border-color 0.15s cubic-bezier(.4, 0, .2, 1);}}.prompt-textarea::placeholder {{font-size: 16px;color: #bfbfbf;}}.prompt-textarea:hover {{border-color: #686868;}}.prompt-textarea:focus {{outline: none;box-shadow: 0 0 5px #686868;border-color: #686868;}}.clear-btn {{position: absolute;top: 40px;right: 5px;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;padding: 0.3em 0.6em;font-size: 14px;cursor: pointer;transition: background-color 0.15s, color 0.15s;}}.clear-btn:hover {{background-color: #686868;color: #ececec;}}.file-loader {{display: flex;align-items: center;}}.file-label {{background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;padding: .7em 2em;font-size: 17px;font-weight: 500;cursor: pointer;transition: background-color 0.15s;}}.file-label:hover {{background: #686868;}}.file-input {{display: none;}}@media (max-width: 750px) {{.controls-container {{flex-direction: column;gap: 6px; align-items: stretch;}}.controls-left,.controls-right {{display: flex;flex-direction: row;margin: 0;width: 100%;gap: 10px;justify-content: space-between;align-items: start;}}.controls-left button {{flex: 1;}}.controls-right > * {{flex: 1;}}.brush-controls {{display: flex;justify-content: space-between;gap: 10px;}}.brush-controls .control-group {{flex: 1; }}.file-loader {{display: flex;justify-content: flex-end;}}}}@media (max-width: 500px) {{.brush-controls {{flex-wrap: wrap;}}}}</style></head><body><h1>Inpainting Helper</h1><div class="main-container"><div class="canvas-container"><canvas id="baseCanvas"></canvas><canvas id="overlayCanvas"></canvas></div><div class="controls-container"><div class="controls-left"><button id="generateMaskBtn" class="btn-generate" disabled>Send</button><button id="resetBtn">Reset</button></div><div class="controls-right"><div class="brush-controls"><div class="control-group"><label>Brush Size:<span id="brushSizeDisplay" class="value-display">20px</span></label><input type="range" id="brushSize" min="1" max="100" value="20"></div><div class="control-group"><label>Brush Hardness:<span id="brushHardnessDisplay" class="value-display">50%</span></label><input type="range" id="brushHardness" min="0" max="100" value="50"></div></div><div class="file-loader"><label for="imageInput" class="file-label">Load</label><input id="imageInput" type="file" accept="image/*" class="file-input"></div></div></div><div class="input-group"><label for="promptInput" class="prompt-label">Enter prompt:</label><textarea id="promptInput" class="prompt-textarea"   placeholder="What needs to be changed in the selected area?"></textarea><button class="clear-btn" id="clearBtn">Clear out</button></div></div><script>const stepsVal = {steps_val};const guidanceVal = {guidance_val};const safetyVal = {safety_val};const outputFmt = "{output_fmt}";const modelName = "{body.get("model", "flux_test_7.flux-1-1-pro")}";const chatId = "{body.get("chat_id", "dummy_chat_id")}";const sessionId = "{body.get("session_id", "dummy_session_id")}";const messageId = "{body.get("id", "dummy_message_id")}";const messagesData = {json.dumps(messages)};const pluginAction = "{__id__}";const fileUrl = "/cache/image/generations/{filename}";const baseCanvas = document.getElementById("baseCanvas");const baseCtx = baseCanvas.getContext("2d", {{ willReadFrequently: true }});const overlayCanvas = document.getElementById("overlayCanvas");const overlayCtx = overlayCanvas.getContext("2d", {{ willReadFrequently: true }});let maskCanvas = document.createElement('canvas');let maskCtx = maskCanvas.getContext('2d', {{ willReadFrequently: true }});const imageInput = document.getElementById("imageInput");const generateMaskBtn = document.getElementById("generateMaskBtn");const resetBtn = document.getElementById("resetBtn");const promptInput = document.getElementById("promptInput");const clearBtn = document.getElementById("clearBtn");const brushSizeInput = document.getElementById("brushSize");const brushHardnessInput = document.getElementById("brushHardness");const brushSizeDisplay = document.getElementById("brushSizeDisplay");const brushHardnessDisplay = document.getElementById("brushHardnessDisplay");let isDrawing = false;let overlayOpacity = 0.7;let originalBase64 = "";let promptText = "";let originalImage = new Image();let brushSize = 20;let brushHardness = 0.5;let lastX = 0;let lastY = 0;function initCanvasDimensions(width, height) {{baseCanvas.width = width;baseCanvas.height = height;overlayCanvas.width = width;overlayCanvas.height = height;maskCanvas.width = width;maskCanvas.height = height;baseCtx.clearRect(0, 0, width, height);baseCtx.drawImage(originalImage, 0, 0, width, height);overlayCtx.clearRect(0, 0, width, height);overlayCtx.globalCompositeOperation = 'source-over';overlayCtx.fillStyle = `rgba(255,255,255,${{overlayOpacity}})`;overlayCtx.fillRect(0, 0, width, height);maskCtx.clearRect(0, 0, width, height);maskCtx.fillStyle = "rgba(0,0,0,1)";maskCtx.fillRect(0, 0, width, height);}}function getCanvasCoords(e) {{const rect = overlayCanvas.getBoundingClientRect();const sx = overlayCanvas.width / rect.width;const sy = overlayCanvas.height / rect.height;return {{ x: (e.clientX - rect.left) * sx, y: (e.clientY - rect.top) * sy }};}}function drawBrushCircle(ctx, x, y) {{if (brushHardness === 1) {{ctx.fillStyle = 'rgba(255,255,255,1)';ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}} else {{const innerRadius = brushSize * brushHardness;if (innerRadius >= brushSize - 1) {{ctx.fillStyle = 'rgba(255,255,255,1)';ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}} else {{const gradient = ctx.createRadialGradient(x, y, innerRadius, x, y, brushSize);gradient.addColorStop(0, 'rgba(255,255,255,1)');gradient.addColorStop(1, 'rgba(255,255,255,0)');ctx.fillStyle = gradient;ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}}}}}}function drawStrokeTo(x, y) {{overlayCtx.globalCompositeOperation = 'destination-out';drawBrushCircle(overlayCtx, x, y);overlayCtx.globalCompositeOperation = 'source-over';maskCtx.globalCompositeOperation = 'source-over';drawBrushCircle(maskCtx, x, y);}}function isCanvasBlank(cnvs) {{const context = cnvs.getContext('2d');const pixelBuffer = new Uint32Array(context.getImageData(0, 0, cnvs.width, cnvs.height).data.buffer);return !pixelBuffer.some(color => color !== 0);}}function updateControls() {{const promptValid = promptInput.value.trim().length >= 3;const maskValid = !isCanvasBlank(maskCanvas);generateMaskBtn.disabled = !maskValid || !promptValid;}}function stripBase64Prefix(dataURL) {{if (!dataURL) return "";const match = dataURL.match(/^data:.*?;base64,(.*)$/);return (match && match[1]) ? match[1] : dataURL;}}imageInput.addEventListener('change', function(e) {{const file = e.target.files[0];if (!file) return;const reader = new FileReader();reader.onload = (event) => {{originalImage.onload = () => {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);originalBase64 = baseCanvas.toDataURL('image/png');updateControls();}};originalImage.src = event.target.result;}};reader.readAsDataURL(file);}});overlayCanvas.addEventListener("mousedown", (e) => {{if (!originalImage.complete) return;isDrawing = true;const coords = getCanvasCoords(e);lastX = coords.x;lastY = coords.y;drawStrokeTo(lastX, lastY);updateControls();}});overlayCanvas.addEventListener("mousemove", (e) => {{if (!isDrawing) return;const coords = getCanvasCoords(e);const dx = coords.x - lastX;const dy = coords.y - lastY;const distance = Math.sqrt(dx * dx + dy * dy);const stepSize = 2;const steps = Math.max(Math.floor(distance / stepSize), 1);for (let i = 0; i < steps; i++) {{const t = i / steps;const x = lastX + dx * t;const y = lastY + dy * t;drawStrokeTo(x, y);}}lastX = coords.x;lastY = coords.y;updateControls();}});overlayCanvas.addEventListener("mouseup", () => {{ isDrawing = false; }});overlayCanvas.addEventListener("mouseleave", () => {{ isDrawing = false; }});brushSizeInput.addEventListener("input", (e) => {{brushSize = parseInt(e.target.value);brushSizeDisplay.textContent = brushSize + 'px';}});brushHardnessInput.addEventListener("input", (e) => {{brushHardness = parseInt(e.target.value) / 100;brushHardnessDisplay.textContent = e.target.value + '%';}});promptInput.addEventListener("input", updateControls);clearBtn.addEventListener("click", () => {{promptInput.value = "";promptInput.focus();updateControls();}});resetBtn.addEventListener("click", () => {{if (originalImage.complete && originalImage.naturalWidth > 0) {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);promptText = "";updateControls();}}}});generateMaskBtn.addEventListener("click", async () => {{const maskBase64 = stripBase64Prefix(maskCanvas.toDataURL('image/png'));const rawImage = stripBase64Prefix(originalBase64);promptText = promptInput.value.trim();const payload = {{model: modelName,chat_id: chatId,session_id: sessionId,id: messageId,messages: messagesData,image: rawImage,mask: maskBase64,prompt: promptText,steps: stepsVal,guidance: guidanceVal,output_format: outputFmt,safety_tolerance: safetyVal,}};console.log("[JS] Send payload into plugin:", payload);try {{const resp = await fetch("/api/chat/actions/" + pluginAction, {{method: "POST",headers: {{ "Content-Type": "application/json" }},body: JSON.stringify(payload)}});if (!resp.ok) {{const t = await resp.text();alert("Plugin error: " + t);}}}} catch (err) {{console.error("Fetch error:", err);alert("Fetch error: " + err);}}}});fetch(fileUrl).then(r => {{if (!r.ok) throw new Error("Loading error: " + r.status);return r.blob();}}).then(blob => {{const reader = new FileReader();reader.onload = e => {{originalImage.onload = () => {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);originalBase64 = baseCanvas.toDataURL('image/png');console.log("[JS] Original base64 uploaded");updateControls();}};originalImage.src = e.target.result;}};reader.readAsDataURL(blob);}}).catch(e => {{console.warn("Fetch error (maybe no last image found?):", e);}});</script></body>
```
"""

                # Проверяем, есть ли в чате уже "ассистентское" сообщение с артефактом
                existing_artifact_msg = self.find_existing_artifact_message(messages)
                if existing_artifact_msg:
                    # Обновляем контент через edit_message
                    edit_event = {
                        "type": "edit_message",
                        "data": {
                            "id": existing_artifact_msg.get("id", __id__),
                            "content": artifact_html,
                        },
                    }
                    await __event_emitter__(edit_event)
                else:
                    # Создаем новое сообщение с артефактом
                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {"role": "assistant", "content": artifact_html},
                        }
                    )

                await asyncio.sleep(90)
                # await __event_emitter__(
                #     {
                #         "type": "status",
                #         "data": {"description": "process done !", "done": True},
                #     }
                # )

                if DEBUG:
                    print("[DEBUG] Артефакт был успешно обновлён/создан в чате.")

                return body
                await asyncio.sleep(1)
            finally:
                # Освобождаем флаг, чтобы не блокировать будущие вызовы,
                # если пользователь повторит операцию позже
                self._artifact_in_use = False
