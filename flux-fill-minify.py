"""
title: Flux inpainting
author: fovendor
version: 0.0.6
license: MIT
required_open_webui_version: 0.4.4
"""

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
            default="https://your-flux-host/api",
            description="Базовый URL API FLUX (без / на конце).",
        )
        FLUX_API_KEY: str = Field(
            default="YOUR-FLUX-API-KEY",
            description="API-ключ для аутентификации (дальше передаём в x-key).",
        )
        STEPS: int = Field(
            default=50,
            description="Кол-во итераций генерации (steps)",
        )
        GUIDANCE: int = Field(
            default=60,
            description="Интенсивность guidance",
        )
        SAFETY_TOLERANCE: int = Field(
            default=6,
            description="Уровень толерантности к Safety-модерации (0..6)",
        )
        OUTPUT_FORMAT: str = Field(
            default="jpeg",
            description="Формат финального изображения (jpeg/png)",
        )
        POLL_INTERVAL: int = Field(
            default=2,
            description="Интервал (сек) между запросами на get_result.",
        )
        MAX_POLL_ATTEMPTS: int = Field(
            default=30,
            description="Максимальное кол-во попыток поллинга (status=Ready).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def status_object(
        self, description: str, status: str = "in_progress", done: bool = False
    ) -> Dict:
        """
        Унифицированная структура для статусов в Open WebUI.
        """
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
        Ищем последнее сгенерированное изображение в формате ![BFL Image](...)
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
        Ищем последнее сообщение с HTML/JSON-кодом (artifact),
        чтобы при необходимости обновить его через edit_message.
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and (
                "```html" in msg.get("content", "")
                or "```json" in msg.get("content", "")
            ):
                return msg
        return None

    def save_url_image(self, url: str) -> str:
        """
        Скачиваем изображение по ссылке и сохраняем локально
        в папку /cache/image/generations.
        Возвращаем путь, по которому это изображение потом доступно.
        """
        image_id = str(uuid.uuid4())
        try:
            response = requests.get(url)
            response.raise_for_status()

            # Определим тип контента и расширение
            mime_type = response.headers.get("content-type", "")
            ext = mimetypes.guess_extension(mime_type) or ".jpg"

            file_path = IMAGE_CACHE_DIR / f"{image_id}{ext}"
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return f"/cache/image/generations/{file_path.name}"
        except Exception as e:
            raise RuntimeError(f"Ошибка при скачивании изображения: {e}")

    async def action(
        self,
        body: dict,
        __user__: dict = None,
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> Optional[dict]:
        """
        Основной метод плагина.
        1) Если есть image/mask/prompt => делаем inpainting через FLUX
           - Отправляем запрос на flux-pro-1.0-fill
           - Ждём статус Ready
           - Скачиваем result.sample и выводим в чате
        2) Иначе -> рендерим/обновляем HTML для выбора области и ввода prompt.
        """

        # ---------------------------------------------------------------------
        # 1. Подстановка заглушек для обязательных полей (чтобы Open WebUI не дал 400)
        # ---------------------------------------------------------------------
        body.setdefault("model", "flux_test_7.flux-1-1-pro")
        body.setdefault("chat_id", "dummy_chat_id")
        body.setdefault("session_id", "dummy_session_id")
        body.setdefault("id", "dummy_message_id")

        if DEBUG:
            print(f"\n[DEBUG] Поступил запрос в flux_inpainting action. Body = {body}")

        # Сообщения чата
        messages = body.get("messages", [])

        # Выводим стартовый статус
        if __event_emitter__:
            await __event_emitter__(
                self.status_object("Обработка запроса...", "in_progress", False)
            )

        # ---------------------------------------------------------------------
        # 2. Если есть image/mask/prompt => inpainting
        # ---------------------------------------------------------------------
        if all(k in body for k in ("image", "mask", "prompt")):
            image_b64 = body["image"]
            mask_b64 = body["mask"]
            prompt_str = body["prompt"]

            steps_val = body.get("steps", self.valves.STEPS)
            guidance_val = body.get("guidance", self.valves.GUIDANCE)
            output_format_val = body.get("output_format", self.valves.OUTPUT_FORMAT)
            safety_val = body.get("safety_tolerance", self.valves.SAFETY_TOLERANCE)

            if DEBUG:
                print(
                    "[DEBUG] Inpainting-запрос:",
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
                    self.status_object("Отправляем задачу в FLUX...", "in_progress")
                )

            # Формируем payload для inpainting
            payload = {
                "image": image_b64,  # base64 без префикса data:image...
                "mask": mask_b64,  # base64 без префикса
                "prompt": prompt_str,
                "steps": steps_val,
                "guidance": guidance_val,
                "output_format": output_format_val,
                "safety_tolerance": safety_val,
            }

            # POST-запрос на создание задачи inpainting
            try:
                flux_response = requests.post(
                    f"{self.valves.FLUX_API_URL}/flux-pro-1.0-fill",
                    headers={
                        "Content-Type": "application/json",
                        "x-key": self.valves.FLUX_API_KEY,
                    },
                    json=payload,
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

            # -----------------------------------------------------------------
            # 3. Поллинг результата
            # -----------------------------------------------------------------
            max_attempts = self.valves.MAX_POLL_ATTEMPTS
            poll_interval = self.valves.POLL_INTERVAL
            image_url = None

            for attempt in range(max_attempts):
                time.sleep(poll_interval)

                if DEBUG:
                    print(
                        f"[DEBUG] Поллинг FLUX (попытка {attempt+1}/{max_attempts}) task_id={task_id}"
                    )

                try:
                    check_resp = requests.get(
                        f"{self.valves.FLUX_API_URL}/get_result",
                        headers={
                            "Content-Type": "application/json",
                            "x-key": self.valves.FLUX_API_KEY,
                        },
                        params={"id": task_id},
                        timeout=30,
                    )
                    check_resp.raise_for_status()
                except requests.exceptions.RequestException as e:
                    msg = f"Ошибка при получении результата FLUX: {e}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}

                rjson = check_resp.json()
                status_ = rjson.get("status")

                if DEBUG:
                    print(f"[DEBUG] Flux status={status_}")

                # Обновим статус в чат (по желанию)
                if __event_emitter__ and status_ not in ["Pending", "Processing"]:
                    await __event_emitter__(
                        self.status_object(
                            f"Flux status: {status_}", "in_progress", done=False
                        )
                    )

                # Проверяем, готово ли
                if status_ == "Ready":
                    result_obj = rjson.get("result", {})
                    # Теперь ищем "sample" — ссылка на результат
                    image_url = result_obj.get("sample")
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
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}
                # Иначе (Pending / Processing) – продолжаем поллинг

            if not image_url:
                msg = "Flux не вернул результат в отведённое время."
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # -----------------------------------------------------------------
            # 4. Скачиваем финальное изображение по ссылке
            # -----------------------------------------------------------------
            if __event_emitter__:
                await __event_emitter__(
                    self.status_object(
                        "Загружаем финальное изображение...", "in_progress"
                    )
                )

            try:
                local_image_path = self.save_url_image(image_url)
            except Exception as e:
                msg = f"Ошибка скачивания изображения: {e}"
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # Формируем сообщение с результатом
            content_msg = f"Результат inpainting:\n\n![BFL Image]({local_image_path})"

            # -----------------------------------------------------------------
            # 5. Выводим готовое изображение в чат
            # -----------------------------------------------------------------
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {"role": "assistant", "content": content_msg},
                    }
                )
                await __event_emitter__(
                    self.status_object(
                        "Готово! Результат inpainting получен.", "complete", True
                    )
                )

            return {"status": "ok", "message": "Inpainting завершён"}

        # ---------------------------------------------------------------------
        # 3. Иначе, если нет image/mask/prompt => отрисовываем/обновляем HTML-форму
        # ---------------------------------------------------------------------
        if DEBUG:
            print("[DEBUG] Нет image/mask/prompt => рендерим HTML-инструмент")

        if __event_emitter__:
            await __event_emitter__(
                self.status_object(
                    "Подготавливаем/обновляем HTML...", "in_progress", False
                )
            )

        # Пытаемся найти последнее сгенерированное изображение
        image_path = self.find_generated_image_path(messages)
        if not image_path:
            error_msg = "В сообщениях не найдено последнее сгенерированное изображение!"
            if DEBUG:
                print("[DEBUG]", error_msg)
            if __event_emitter__:
                await __event_emitter__(self.status_object(error_msg, "error", True))
            return {"status": "error", "message": error_msg}

        filename = os.path.basename(image_path)
        full_file_path = IMAGE_CACHE_DIR / filename
        if not full_file_path.exists():
            error_msg = f"Файл не найден: {full_file_path}"
            if DEBUG:
                print("[DEBUG]", error_msg)
            if __event_emitter__:
                await __event_emitter__(self.status_object(error_msg, "error", True))
            return {"status": "error", "message": error_msg}

        # Значения по умолчанию
        steps_val = self.valves.STEPS
        guidance_val = self.valves.GUIDANCE
        safety_val = self.valves.SAFETY_TOLERANCE
        output_fmt = self.valves.OUTPUT_FORMAT

        # Генерируем HTML для маски
        artifact_html = f"""
```html
<head><meta charset="UTF-8"><title>Inpainting Helper</title><style>body {{font-family: Arial, sans-serif;margin: 20px;max-width: 1000px;background-color: #262626;}}h1 {{padding-top: 1em;color: #ececec;}}canvas {{border-radius: .75rem;max-width: 100%;height: auto;border: 1px solid #ccc;margin: 10px 0;}}.input-group {{position: relative;margin: 10px 0;}}.input-group label {{color: #ececec;font-size: 16px;margin-bottom: 5px;display: block;}}textarea {{width: 100%;height: 150px;margin: 10px 0;resize: vertical;border-radius: .75rem;background-color: #2f2f2f;color: #ececec;border: 1px solid transparent;padding: 10px;padding-right: 50px;box-sizing: border-box;font-family: Arial, sans-serif;font-size: 14px;transition: box-shadow 0.15s cubic-bezier(.4, 0, .2, 1), border-color 0.15s cubic-bezier(.4, 0, .2, 1);}}textarea::placeholder {{font-size: 16px;color: #bfbfbf;}}textarea:hover,.input-group:hover textarea {{border-color: #686868;}}textarea:focus {{outline: none;box-shadow: 0 0 5px #686868;border-color: #686868;}}.input-group:hover .clear-btn {{background-color: #686868;color: #ececec;}}button {{padding: .7em 3em;font-size: 17px;cursor: pointer;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;font-weight: 500;transition-timing-function: cubic-bezier(.4, 0, .2, 1);transition-duration: .15s;opacity: 1;}}button:hover {{background: #686868;}}button:disabled {{background-color: #a9a9a9;color: #6d6d6d;cursor: not-allowed;opacity: 0.6;}}#resetBtn {{margin-left: 5px;}}#generateMaskBtn {{background-color: #ececec;color: black;}}#generateMaskBtn:hover {{background: #ffffff;}}.clear-btn {{position: absolute;top: 40px;right: 5px;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;padding: 0.3em 0.6em;font-size: 14px;cursor: pointer;transition: background-color 0.15s cubic-bezier(.4, 0, .2, 1), color 0.15s cubic-bezier(.4, 0, .2, 1);}}.clear-btn:hover {{background-color: #686868;color: #ececec;}}</style></head><body><h1>Inpainting Helper</h1><canvas id="imageCanvas"></canvas><div><button id="generateMaskBtn" disabled>Сформировать</button><button id="resetBtn">Сброс</button></div><div class="input-group"><label for="promptInput">Введите промт:</label><textarea id="promptInput" placeholder="Что вы хотите дорисовать в области?"></textarea><button class="clear-btn" id="clearBtn">Стереть</button></div><script>const stepsVal = {steps_val};const guidanceVal = {guidance_val};const safetyVal = {safety_val};const outputFmt = "{output_fmt}";const canvas = document.getElementById("imageCanvas");const ctx = canvas.getContext("2d");const originalImage = new Image();let isDrawing = false;let startX, startY;let currentRect = null;let overlayOpacity = 0.7;let originalBase64 = "";let maskBase64 = "";let promptText = "";const generateMaskBtn = document.getElementById("generateMaskBtn");const resetBtn = document.getElementById("resetBtn");const promptInput = document.getElementById("promptInput");const clearBtn = document.getElementById("clearBtn");function stripBase64Prefix(dataURL) {{if (!dataURL) return "";const match = dataURL.match(/^data:.*?;base64,(.*)$/);if (match && match[1]) {{return match[1];}}return dataURL;}}function getCanvasCoords(e) {{const r = canvas.getBoundingClientRect();const sx = canvas.width / r.width;const sy = canvas.height / r.height;return {{ x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sy }};}}function drawFadedBackground() {{ctx.drawImage(originalImage, 0, 0);ctx.fillStyle = "rgba(255,255,255," + overlayOpacity + ")";ctx.fillRect(0, 0, canvas.width, canvas.height);}}function drawSelection() {{if (!currentRect) return;ctx.save();ctx.beginPath();ctx.rect(currentRect.x, currentRect.y, currentRect.w, currentRect.h);ctx.clip();ctx.drawImage(originalImage, 0, 0);ctx.restore();ctx.strokeStyle = "#ff0000";ctx.lineWidth = 2;ctx.strokeRect(currentRect.x, currentRect.y, currentRect.w, currentRect.h);}}function redrawCanvas() {{ctx.clearRect(0, 0, canvas.width, canvas.height);drawFadedBackground();if (currentRect) drawSelection();updateControls();}}function updateControls() {{const promptValid = promptInput.value.trim().length >= 3;generateMaskBtn.disabled = !currentRect || !promptValid;generateMaskBtn.style.cursor = (currentRect && promptValid) ? "pointer" : "not-allowed";}}canvas.addEventListener("mousedown", e => {{const c = getCanvasCoords(e);startX = c.x;startY = c.y;isDrawing = true;}});canvas.addEventListener("mousemove", e => {{if (!isDrawing) return;const c = getCanvasCoords(e);currentRect = {{x: Math.min(startX, c.x),y: Math.min(startY, c.y),w: Math.abs(c.x - startX),h: Math.abs(c.y - startY)}};redrawCanvas();}});canvas.addEventListener("mouseup", () => {{isDrawing = false;updateControls();}});canvas.addEventListener("mouseleave", () => isDrawing = false);promptInput.addEventListener("input", updateControls);clearBtn.addEventListener("click", () => {{promptInput.value = "";promptInput.focus();updateControls();}});generateMaskBtn.addEventListener("click", async () => {{if (!currentRect) {{alert("Сначала выделите область на изображении.");return;}}console.log("[JS] Создаём маску по прямоугольнику", currentRect);const m = document.createElement("canvas");m.width = originalImage.naturalWidth;m.height = originalImage.naturalHeight;const mx = m.getContext("2d");mx.fillStyle = "#000000";mx.fillRect(0, 0, m.width, m.height);mx.fillStyle = "#ffffff";mx.fillRect(currentRect.x, currentRect.y, currentRect.w, currentRect.h);const rawMask = m.toDataURL("image/png");maskBase64 = stripBase64Prefix(rawMask);const rawImage = stripBase64Prefix(originalBase64);promptText = promptInput.value.trim();console.log("[JS] Prompt:", promptText);const payload = {{model: '{body.get("model", "flux_test_7.flux-1-1-pro")}',chat_id: '{body.get("chat_id", "dummy_chat_id")}',session_id: '{body.get("session_id", "dummy_session_id")}',id: '{body.get("id", "dummy_message_id")}',messages: {json.dumps(messages)},image: rawImage,mask: maskBase64,prompt: promptText,steps: stepsVal,guidance: guidanceVal,output_format: outputFmt,safety_tolerance: safetyVal,}};console.log("[JS] Отправляем payload в плагин:", payload);try {{const resp = await fetch("/api/chat/actions/flux_inpainting", {{method: "POST",headers: {{"Content-Type": "application/json"}},body: JSON.stringify(payload)}});if (!resp.ok) {{const t = await resp.text();alert("Ошибка плагина: " + t);}}}} catch (err) {{console.error("Fetch error:", err);alert("Fetch error: " + err);}}}});resetBtn.addEventListener("click", () => {{currentRect = null;redrawCanvas();maskBase64 = "";promptText = "";updateControls();}});const fileUrl="/cache/image/generations/{filename}";fetch(fileUrl).then(r => {{if (!r.ok) throw new Error("Ошибка загрузки: " + r.status);return r.blob();}}).then(b => {{const rd = new FileReader();rd.onload = e => {{originalBase64 = e.target.result;console.log("[JS] Оригинал base64 загружен");originalImage.onload = () => {{canvas.width = originalImage.naturalWidth;canvas.height = originalImage.naturalHeight;redrawCanvas();}};originalImage.src = originalBase64;}};rd.readAsDataURL(b);}}).catch(e => {{alert("Fetch error: " + e);}});</script></body>
```
"""

        existing_artifact_msg = self.find_existing_artifact_message(messages)

        # С небольшой задержкой, чтобы успеть отрендерить
        await asyncio.sleep(1)

        if not existing_artifact_msg:
            # Если раньше не было HTML-блока для маски, отправляем новое сообщение
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {"role": "assistant", "content": artifact_html},
                    }
                )
                await __event_emitter__(
                    self.status_object(
                        "HTML-артефакт создан, откройте в чате!", "complete", True
                    )
                )
        else:
            # Обновляем существующее сообщение
            msg_id = existing_artifact_msg.get("id")
            if msg_id:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "edit_message",
                            "data": {
                                "message_id": msg_id,
                                "role": "assistant",
                                "content": artifact_html,
                            },
                        }
                    )
                    await __event_emitter__(
                        self.status_object("HTML-артефакт обновлён", "complete", True)
                    )
            else:
                # Нет ID => просто выводим статус
                if __event_emitter__:
                    await __event_emitter__(
                        self.status_object(
                            "Арт уже существует, но нет ID для обновления",
                            "complete",
                            True,
                        )
                    )

        return {"status": "ok"}
