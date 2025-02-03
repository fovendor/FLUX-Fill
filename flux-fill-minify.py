"""
title: Black Forest Labs: Flux inpainting
author: fovendor
version: 0.4.11
icon_url: data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgZmlsbD0ibm9uZSIKICAgdmlld0JveD0iMCAwIDI0IDI0IgogICBzdHJva2Utd2lkdGg9IjIuMyIKICAgc3Ryb2tlPSJjdXJyZW50Q29sb3IiCiAgIGNsYXNzPSJ3LTQgaC00IgogICB2ZXJzaW9uPSIxLjEiCiAgIGlkPSJzdmcxIgogICBzb2RpcG9kaTpkb2NuYW1lPSJ3My5zdmciCiAgIHhtbDpzcGFjZT0icHJlc2VydmUiCiAgIGlua3NjYXBlOnZlcnNpb249IjEuNCAoZTdjM2ZlYjEwMCwgMjAyNC0xMC0wOSkiCiAgIHhtbG5zOmlua3NjYXBlPSJodHRwOi8vd3d3Lmlua3NjYXBlLm9yZy9uYW1lc3BhY2VzL2lua3NjYXBlIgogICB4bWxuczpzb2RpcG9kaT0iaHR0cDovL3NvZGlwb2RpLnNvdXJjZWZvcmdlLm5ldC9EVEQvc29kaXBvZGktMC5kdGQiCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c3ZnPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnMKICAgICBpZD0iZGVmczEiIC8+PHNvZGlwb2RpOm5hbWVkdmlldwogICAgIGlkPSJuYW1lZHZpZXcxIgogICAgIHBhZ2Vjb2xvcj0iI2ZmZmZmZiIKICAgICBib3JkZXJjb2xvcj0iIzAwMDAwMCIKICAgICBib3JkZXJvcGFjaXR5PSIwLjI1IgogICAgIGlua3NjYXBlOnNob3dwYWdlc2hhZG93PSIyIgogICAgIGlua3NjYXBlOnBhZ2VvcGFjaXR5PSIwLjAiCiAgICAgaW5rc2NhcGU6cGFnZWNoZWNrZXJib2FyZD0iMCIKICAgICBpbmtzY2FwZTpkZXNrY29sb3I9IiNkMWQxZDEiCiAgICAgaW5rc2NhcGU6em9vbT0iMjIuNjI3NDE3IgogICAgIGlua3NjYXBlOmN4PSI5LjA1OTgwNTYiCiAgICAgaW5rc2NhcGU6Y3k9IjE0LjQwNzMwMSIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjE5MjAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iMTEzMSIKICAgICBpbmtzY2FwZTp3aW5kb3cteD0iMTQ0MCIKICAgICBpbmtzY2FwZTp3aW5kb3cteT0iMTM5MiIKICAgICBpbmtzY2FwZTp3aW5kb3ctbWF4aW1pemVkPSIxIgogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzEiIC8+PHBhdGgKICAgICBzdHlsZT0iZmlsbDojMDAwMDAwO3N0cm9rZS13aWR0aDowLjA2OTYxNDkzO29wYWNpdHk6MC43NTtzdHJva2UtZGFzaGFycmF5Om5vbmUiCiAgICAgZD0iTSAxNi4wNTg5MDUsMTEuNjM1ODkgQyAxNS42Njg2NjMsMTEuNTI4MjM2IDE1LjIxNzA2LDExLjIxNTc4MSAxNC45NjAzNjYsMTAuODc1ODQxIDE0LjExMDI4LDkuNzUwMDU3OSAxNC42NDA0MDIsOC4xMjI5OTY1IDE1Ljk5NjY2NSw3LjY5NTIwNjUgYyAwLjQzNzkwOSwtMC4xMzgxMjYyIDAuNzcyODU1LC0wLjEzNzg5MDIgMS4yMjIwNzcsOS4yNzNlLTQgMC42NDkzNjUsMC4yMDA1NzAyIDEuMTc2NzUyLDAuNzUyOTAzNyAxLjM3MTc1MywxLjQzNjYzNzIgMC4yMjE5MTksMC43NzgxMTQ3IC0wLjEwMDYwMiwxLjY3OTgyOCAtMC43NzgzMzIsMi4xNzYxMDYgLTAuNDg4MTU3LDAuMzU3NDUyIC0xLjE3NzE5MiwwLjQ4NjAwMiAtMS43NTMyNTgsMC4zMjcwODYgeiBtIDEuMDUxNzUxLC0xLjQ4NzY1MyBjIDAuMTU0MjQ0LC0wLjE1NDIzODIgMC4xNzE2NjcsLTAuMjA0NTYxNCAwLjE3MTY2NywtMC40OTU4MTgxIDAsLTAuMjkzNTk1NCAtMC4wMTY3NiwtMC4zNDA5MDA4IC0wLjE3Nzc2MiwtMC41MDE5MTYyIC0wLjE2MTAwOSwtMC4xNjEwMDUxIC0wLjIwODMxMiwtMC4xNzc3NTUxIC0wLjUwMTkxNSwtMC4xNzc3NTUxIC0wLjI5MzYwMywwIC0wLjM0MDkwNiwwLjAxNjgxMiAtMC41MDE5MTUsMC4xNzc3NTUxIC0wLjE2MDU5NCwwLjE2MDU5NzcgLTAuMTc3NzYyLDAuMjA4NzQ4OSAtMC4xNzc3NjIsMC40OTg1ODUxIDAsMC4yNjY5NTY1IDAuMDIyODIsMC4zNDUzNzA1IDAuMTM1OTM2LDAuNDY3MDgwMiAwLjE4NjYyOCwwLjIwMDgwMiAwLjMwOTc3OCwwLjI0NTMyIDAuNjE2NzU5LDAuMjIyOTMgMC4yMDg1NSwtMC4wMTUyNSAwLjI5OTAzOSwtMC4wNTQ5MyAwLjQzNDk5MiwtMC4xOTA4NjEgeiIKICAgICBpZD0icGF0aDkiIC8+PHBhdGgKICAgICBzdHlsZT0ib3BhY2l0eTowLjc1O2ZpbGw6IzAwMDAwMDtzdHJva2Utd2lkdGg6MC4wNjk2MTQ5O3N0cm9rZS1kYXNoYXJyYXk6bm9uZSIKICAgICBkPSJNIDIuNzQ5NjI3NCwxMS42Mzk5NTEgQyAxLjc0NTQ3NzIsMTEuMzk2NzgzIDAuODgzMjk4NDQsMTAuNTA3MTIgMC42NzYwMDUyNSw5LjUwMDIxNzIgMC41OTQyOTE0LDkuMTAzMzAxOSAwLjU5NDU3MzM0LDMuMjM5NjgxMiAwLjY3NjIzNzA4LDIuODQ0NzUxIDAuODk1NzcwMTEsMS43ODQyNDE5IDEuODEyOTI3NSwwLjg4MTA1OTkyIDIuODczMTEzOSwwLjY4MTM0NjAzIDMuMTAxOTU0NiwwLjYzODIzODcgNC4zNTE5NTczLDAuNjI0OTEzODYgNy4wNTk5MTI5LDAuNjM2NzAzNjMgbCAzLjg2MDU1NjEsMC4wMTY4MTI3IDAuMzY3NTg2LDAuMTQ3MzAzMiBjIDAuODQ1MDI5LDAuMzM4NjI5NDcgMS40MTY0NCwwLjk1MTY1MTY3IDEuNjg3MjkyLDEuODEwMTYxOTcgMC4xMTgxNTQsMC4zNzQ1MDUzIDAuMTIwMDg0LDAuNDMxNjkyNiAwLjEyMDA4NCwzLjU2MTQ5NzMgMCwzLjEzMjUzMzUgLTAuMDAxOSwzLjE4NjY5OTYgLTAuMTIwNDY2LDMuNTYzNzUzIC0wLjE0OTQyMywwLjQ3NDkyMzIgLTAuNDU2NDk3LDAuOTU3NjY2MiAtMC44MDc4MSwxLjI2OTkzMzIgLTAuMzE5NTgsMC4yODQwNjEgLTAuOTE2NTE2LDAuNTgwODMyIC0xLjMyMjA3NywwLjY1NzI2MSAtMC40NTY2NjYsMC4wODYwNSAtNy43MzAyODk0LDAuMDY0OTUgLTguMDk1NTQzNiwtMC4wMjM0OSB6IE0gMTEuMDYyMDcsOC44OTU0NDA1IEMgMTEuNDA0ODk4LDguNzE5Nzc0IDExLjUzMDA0Myw4LjIxNjgyMzkgMTEuMzE3NjE3LDcuODY4NDAwMiAxMS4xMTExNiw3LjUyOTc3MzggMTAuMDUzNjQ0LDcuNTMxODM1MiA2Ljg3NDk4MTcsNy41MzE4MzUyIGMgLTEuOTA4MDA4OCwwIC0zLjg3NzAwMjMsMC4wMTk1NyAtMy45Nzg0MTEsMC4wNTc5ODggLTAuNjQxNTg1OSwwLjI0MzA5MTggLTAuNjMwNDIzNywxLjE1NzI3OTMgMC4wMTY1MzEsMS4zNTQ3ODE0IDAuMDg2MTUxLDAuMDI2MzE2IDIuNDExMDAyMiwwLjA0MzQ0MiA0LjAxMDk1ODYsMC4wMzgwMTEgMi4zOTMxNzI5LC0wLjAwODM2IDQuMDEzODg3NywtMC4wMjM2IDQuMTM3OTk5NywtMC4wODcwOTIgeiBNIDExLjAyMDUwOCw0LjczNDg0MzMgQyAxMS40MDc5NDMsNC42MTU2MzI2IDExLjU0MjM1NSw0LjA1OTg0MTkgMTEuMzE2ODQzLDMuNjk0OTU5NCAxMS4wOTc1MjIsMy4zNDAwOTA1IDEwLjAxMDIxMSwzLjMzOTE5NzcgNi43NTg0OTM4LDMuMzU2NjIwMyAzLjU2MjM4LDMuMzczNzU2NiAyLjc0MjQxNSwzLjM2MDU4ODUgMi41MTc3MDE0LDMuNzAzNTA5OSBjIC0wLjEyNzA5ODcsMC4xOTM5Nzc4IC0wLjExODU4OSwwLjU4NzMwMTggMC4wMTY2OTgsMC43NzE4NjU1IDAuMjUyMDUyNSwwLjM0Mzg1NzEgMS4xMzQ1NzQzLDAuMzM3NTc5IDQuMzIzNDQ3MSwwLjMzNzY3NDEgMi4zOTg1NzU5LDUuMzJlLTUgNC4wMDE5NjQ1LC0wLjAyODc2MSA0LjE2MjY1NzUsLTAuMDc4MjA1IHoiCiAgICAgaWQ9InBhdGg4IgogICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0iY3NjY2Njc3NzY3NjY2NjY3NjY2NjY3NzY2NjY3NzIiAvPjxwYXRoCiAgICAgc3R5bGU9ImZpbGw6IzAwMDAwMDtzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MC42MDk7c3Ryb2tlLWRhc2hhcnJheTpub25lO3N0cm9rZS1vcGFjaXR5OjE7b3BhY2l0eTowLjc1IgogICAgIGQ9Ik0gNi45NTI3ODg5LDIyLjgwNDc0OSBDIDYuNDkzMjU4NCwyMi43Mzc4MTEgNS44NjM1NTIsMjIuNTE3NDQgNS40NTMzNzg3LDIyLjI3OTk4NCA1LjAyMDA5MTYsMjIuMDI5MTYyIDQuMjQxNzY2MywyMS4yNTkzMjggMy45OTIwNDM1LDIwLjgzNDYxNCAzLjc0MTE5NjEsMjAuNDA3OTc5IDMuNTE4NzI4NiwxOS43NjEwMjUgMy40NDc5OTYzLDE5LjI1MjQ3NyAzLjQxMjY1ODMsMTguOTk4NDE3IDMuMzg5NzU3NSwxNy43MTI3NTkgMy4zODk3NTc1LDE1Ljk4MzA2NiB2IC0yLjg1MDcxMiBoIDAuNjc5Njc0NiAwLjY3OTY3NTQgdiAyLjk1MTk2NSBjIDAsMy4xNDExMTIgMC4wMDYzNywzLjIzIDAuMjczNTIzOCwzLjgzNDAwNCBsIDAuMTA2NDc0NSwwLjI0MDcxNCAwLjQ3NjA4MzEsLTAuNDQ5OTAyIGMgMC4yNjE4NDQ3LC0wLjI0NzQzOSAxLjc4NTEzNjIsLTEuNzM4MTMgMy4zODUwOTI2LC0zLjMxMjY2NCAxLjgwMjE2MTUsLTEuNzAwNzEgMy4xOTM5MzM1LC0zLjE4MjU0OSA0LjEzMjQyNTUsLTMuMTgyNTQ5IDAuOTM0MjY2LDAgMi4wMTk3MzQsMS4wMjc0NDkgMy45MzE0NDEsMi45ODc0MjggMC43OTY5OSwtMC42MTAxNTQgMS40NjA4NjEsLTEuMjQ0ODI1IDIuMjE1NDQxLC0xLjg2OTMzMiBsIDMuMDg4OTExLDIuNzkzMzEyIC0xLjEzNTQxNCwyLjc5MjMwMyBjIC0wLjI2MTU1MiwwLjY0MzIzIDAuMjczMjE5LC0wLjQ0NDIzMSAwLjI3MzIxOSwtNi43ODUyNzkgMCwtNi40MzY2NzE1IDAuMDExNTUsLTYuMTgxNjkxOCAtMC4zMTAxMzksLTYuODUxMTIyMSBDIDIwLjk5NzM1NCw1Ljg4ODMxMiAyMC4zNjY3NTUsNS4yNTc3MDk3IDE5Ljk3MzgzNSw1LjA2ODkgMTkuMzU2OTc1LDQuNzcyNDc3NiAxOS4yMTU3NjMsNC43NTg3NTggMTYuNzgxNTMxLDQuNzU4NzU4IEggMTQuNTM2NDMzIFYgNC4wNzkwODQ2IDMuMzk5NDA4IGggMi4xNDM4MzcgYyAxLjIyNzE5MiwwIDIuMzIyODczLDAuMDI0OTA2IDIuNTYyNTYsMC4wNTgyMzkgMC41MDg1NDcsMC4wNzA3MjggMS4xNTU0OTUsMC4yOTMxOTk4IDEuNTgyMTMsMC41NDQwNDczIDAuNDA3MjI2LDAuMjM5NDM4OCAxLjE4ODk3NCwxLjAyMTE4NjIgMS40Mjg0MTEsMS40Mjg0MTI2IDAuMjUwODUxLDAuNDI2NjM1MSAwLjQ3MzMxNSwxLjA3MzU4NDQgMC41NDQwNDcsMS41ODIxMjk3IDAuMDc5MjYsMC41Njk4NTIxIDAuMDgwMzYsMTEuNjYyNTEwNCAwLjAwMTEsMTIuMjMxNTUyNCAtMC4xMjc3MDYsMC45MTgxNjEgLTAuNTI0NTA2LDEuNzEwODUzIC0xLjE4OTA3NCwyLjM3NTQxNCAtMC42NjQ1NjUsMC42NjQ1NzEgLTEuNDU3MjU3LDEuMDYxMzcyIC0yLjM3NTQyNCwxLjE4OTA3NSAtMC41MDMwMzUsMC4wNjk5NyAtMTEuNzk5MDM1MSwwLjA2NjczIC0xMi4yODEzNDMzLC0wLjAwMzEgeiBNIDE5LjM0NzMwMSwyMS40MjI0MzIgYyAwLjE3NjM2NywtMC4wNDU5NSAwLjQzMjMwOCwtMC4xMzM2OTggMC41Njg3NTcsLTAuMTk1MDI3IGwgMC4yNDgwODUsLTAuMTExNTE3IC0xLjI2MTkyMywtMS4yMzIyNzcgYyAtMC42OTQwNTcsLTAuNjc3NzYgLTIuMjAwMjI3LC0yLjE1Mjk4NSAtMy4zNDcwNDMsLTMuMjc4Mjc2IC0xLjU4OTk0NSwtMS41NjAwOTMgLTIuMTI2MzY3LC0yLjA1NTAzNCAtMi4yNTg3OTcsLTIuMDg0MTE2IC0wLjM5NTQxNSwtMC4wODY4OCAtMC40MDU3MjMsLTAuMDc4NTMgLTIuNzk5NDMxLDIuMjc0OTAzIC0xLjI1MDc3NjIsMS4yMjk2OTggLTIuNzU1OTg1MiwyLjcwNDYxOSAtMy4zNDQ5MDk4LDMuMjc3NTk4IGwgLTEuMDcwNzY3LDEuMDQxNzgxIDAuMjUwNjA2MiwwLjExMjgyMyBjIDAuNjE4NTg0OSwwLjI3ODQ3NCAwLjQxNDkzODMsMC4yNzAyMjUgNi43NjU4MTM2LDAuMjc0MDU3IDUuMTY0NTg3LDAuMDAzMSA1Ljk3MDI3NiwtMC4wMDczIDYuMjQ5NjA5LC0wLjA3OTk5IHoiCiAgICAgaWQ9InBhdGgyIgogICAgIHNvZGlwb2RpOm5vZGV0eXBlcz0iY2Njc3NjY2NzY2NjY3NjY2Nzc3Nzc2NjY3Njc3NzY2NzY2NjY2NjY2NjY2NzY2NjIiAvPjwvc3ZnPgo=
github: https://github.com/fovendor/FLUX-Fill
license: MIT
requirements: asyncio, uuid, requests, pydantic, pathlib, pydantic
required_open_webui_version: 0.5.4
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


"""
Note!
- If you encounter a bug with the plugin, feel free to open an issue on GitHub: https://github.com/fovendor/FLUX-Fill

To easily create and modify images created with FLUX, the following approach is recommended:
- Install FLUX Gen and use it to generate images.
- Install FLUX Fill and use it to modify the generated images.

Hacks. You can put ANY image in the catalog with the generated images and transfer it to FLUX Fill. To do this: 
- Go into edit mode of the chat message you received from FLUX Gen.
- Paste the name <new image>.png instead of ![BFL Image](/cache/image/generations/<generated image>.png).
- Save your changes and call the FLUX Fill function.
- Enjoy!
"""


class Action:
    class Valves(BaseModel):
        FLUX_API_URL: str = Field(
            default="https://api.bfl.ml/v1",
            description="Basic URL of the FLUX API (without / at the end)",
        )
        FLUX_API_KEY: str = Field(
            default="YOUR-FLUX-API-KEY",
            description="API key for authentication",
        )
        STEPS: int = Field(
            default=50,
            description="Number of generation iterations steps: 1,5..100",
        )
        GUIDANCE: int = Field(
            default=50,
            description="Guidance scale: 15..50",
        )
        SAFETY_TOLERANCE: int = Field(
            default=6,
            description="Moderation: 0..6",
        )
        OUTPUT_FORMAT: str = Field(
            default="jpeg",
            description="Output format for the generated image. Can be 'jpeg' or 'png'.",
            enum=["jpeg", "png"],
        )
        POLL_INTERVAL: int = Field(
            default=2,
            description="Interval in sec between requests for get_result",
        )
        MAX_POLL_ATTEMPTS: int = Field(
            default=60,
            description="Maximum number of attempts to pick up a picture",
        )

    def __init__(self):
        self.valves = self.Valves()

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
        Looking for the last generated image in the format: ![BFL Image](...)
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
        We are looking for the last message with HTML/JSON code (artifact),
        to update it via edit_message if necessary.
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
        Download the image from the link and save it locally
        in the /cache/image/generations folder.
        Return the path where the image is then available.
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
            raise RuntimeError(f"Error downloading an image: {e}")

    async def action(
        self,
        body: dict,
        __id__: str = None,  # action ID
        __user__: dict = None,
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> Optional[dict]:
        """
        Basic plugin method.
        1) If there is an image/mask/prompt => do inpainting via FLUX
           - Send request to flux-pro-1.0-fill
           - Wait for Ready status
           - Download result.sample and display in chat.
        2) Otherwise -> render/update HTML to select area and enter prompt.
        """

        body.setdefault("model", "flux_test_7.flux-1-1-pro")
        body.setdefault("chat_id", "dummy_chat_id")
        body.setdefault("session_id", "dummy_session_id")
        body.setdefault("id", "dummy_message_id")

        if DEBUG:
            print(f"\n[DEBUG] A request was received in {__id__} action. Body = {body}")

        messages = body.get("messages", [])

        if __event_emitter__:
            await __event_emitter__(
                self.status_object("Processing request...", "in_progress", False)
            )

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
                    "[DEBUG] Inpainting-request:",
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

            # Form payload for inpainting
            payload = {
                "image": image_b64,
                "mask": mask_b64,
                "prompt": prompt_str,
                "steps": steps_val,
                "guidance": guidance_val,
                "output_format": output_format_val,
                "safety_tolerance": safety_val,
            }

            # POST request to create an inpainting task
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
                msg = f"Error when querying FLUX: {e}"
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            flux_json = flux_response.json()
            task_id = flux_json.get("id")
            if not task_id:
                msg = f"Flux did not return the task id: {flux_json}"
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # -----------------------------------------------------------------
            # 3. Polling the result
            # -----------------------------------------------------------------
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
                        timeout=30,
                    )
                    check_resp.raise_for_status()
                except requests.exceptions.RequestException as e:
                    msg = f"Error when receiving the result FLUX: {e}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
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

                # Checking to see if it's ready
                if status_ == "Ready":
                    result_obj = rjson.get("result", {})
                    # Now look for “sample” - a link to the result
                    image_url = result_obj.get("sample")
                    break

                elif status_ in [
                    "Error",
                    "Content Moderated",
                    "Request Moderated",
                    "Task not found",
                ]:
                    msg = f"Flux has returned the status: {status_}"
                    if DEBUG:
                        print(msg)
                    if __event_emitter__:
                        await __event_emitter__(self.status_object(msg, "error", True))
                    return {"status": "error", "message": msg}
                # Otherwise (Pending / Processing) - continue polling

            if not image_url:
                msg = "Flux did not return a result in the time allotted"
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # -----------------------------------------------------------------
            # 4. Download the final image from the link
            # -----------------------------------------------------------------
            if __event_emitter__:
                await __event_emitter__(
                    self.status_object("Uploading the final image...", "in_progress")
                )

            try:
                local_image_path = self.save_url_image(image_url)
            except Exception as e:
                msg = f"Image download error: {e}"
                if DEBUG:
                    print(msg)
                if __event_emitter__:
                    await __event_emitter__(self.status_object(msg, "error", True))
                return {"status": "error", "message": msg}

            # Generate a message with the result
            content_msg = f"Result inpainting:\n\n![BFL Image]({local_image_path})"

            # -----------------------------------------------------------------
            # 5. Display the finished image in the chat room
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
                        "Done! The result of inpainting is obtained.", "complete", True
                    )
                )

            return {"status": "ok", "message": "Inpainting is complete"}

        # ---------------------------------------------------------------------
        # 3. Otherwise, if there is no image/mask/prompt => render/update the HTML form
        # ---------------------------------------------------------------------
        if DEBUG:
            print("[DEBUG] No image/mask/prompt => render HTML tool")

        if __event_emitter__:
            await __event_emitter__(
                self.status_object("Prepare/update HTML...", "in_progress", False)
            )

        # Trying to find the last image generated
        image_path = self.find_generated_image_path(messages)
        if not image_path:
            error_msg = "The last generated image was not found in the posts!"
            if DEBUG:
                print("[DEBUG]", error_msg)
            if __event_emitter__:
                await __event_emitter__(self.status_object(error_msg, "error", True))
            return {"status": "error", "message": error_msg}

        filename = os.path.basename(image_path)
        full_file_path = IMAGE_CACHE_DIR / filename
        if not full_file_path.exists():
            error_msg = f"File not found: {full_file_path}"
            if DEBUG:
                print("[DEBUG]", error_msg)
            if __event_emitter__:
                await __event_emitter__(self.status_object(error_msg, "error", True))
            return {"status": "error", "message": error_msg}

        # Default values
        steps_val = self.valves.STEPS
        guidance_val = self.valves.GUIDANCE
        safety_val = self.valves.SAFETY_TOLERANCE
        output_fmt = self.valves.OUTPUT_FORMAT

        # Generate an HTML page to draw the mask and send a request for inpainting
        artifact_html = f"""
```html
<head><meta charset="UTF-8"><title>Inpainting Helper</title><style>body {{font-family: Arial, sans-serif;margin: 20px;background-color: #262626;display: flex;flex-direction: column;align-items: center;}}h1 {{padding-top: 1em;color: #ececec;}}.main-container {{width: 100%;max-width: 1000px;margin: 0 auto;}}.canvas-container {{position: relative;width: 100%;margin: 10px 0;background-color: #1a1a1a;border-radius: .75rem;border: 1px solid #333;}}#baseCanvas {{display: block;border-radius: .75rem;max-width: 100%;}}#overlayCanvas {{position: absolute;top: 0;left: 0;border-radius: .75rem;max-width: 100%;cursor: crosshair;display: block;}}.controls-container {{width: 100%;display: flex;justify-content: space-between;margin: 15px 0;}}.controls-left {{display: flex;flex-direction:row;width: 20em;flex-grow:1;gap: 10px;align-items: center;}}.controls-right {{display: flex;gap: 15px;align-items: center;margin-left:1em;}}.brush-controls {{display: flex;gap: 20px;align-items: center;}}.control-group {{display: flex;flex-direction: column;gap: 5px;}}.control-group label {{color: #ececec;font-size: 14px;}}.value-display {{color: #ececec;font-size: 14px;margin-left: 10px;min-width: 40px;}}input[type="range"] {{-webkit-appearance: none;width: 150px;height: 8px;background: #4b4b4b;border-radius: 4px;outline: none;}}input[type="range"]::-webkit-slider-thumb {{-webkit-appearance: none;width: 16px;height: 16px;background: #ececec;border-radius: 50%;cursor: pointer;}}input[type="range"]:hover {{background: #686868;}}button {{flex-grow: 1;padding: .7em 2em;font-size: 17px;cursor: pointer;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;font-weight: 500;transition: background-color 0.15s;opacity: 1;}}button:hover {{background: #686868;}}button:disabled {{background-color: #a9a9a9;color: #6d6d6d;cursor: not-allowed;opacity: 0.6;}}.btn-generate {{background-color: #ececec;color: black;}}.btn-generate:hover {{background: #ffffff;}}.input-group {{position: relative;margin: 10px 0;width: 100%;max-width: 1000px;}}.prompt-label {{color: #ececec;font-size: 16px;margin-bottom: 5px;display: block;}}.prompt-textarea {{width: 100%;height: 150px;margin: 10px 0;resize: vertical;border-radius: .75rem;background-color: #2f2f2f;color: #ececec;border: 1px solid transparent;padding: 10px;padding-right: 50px;box-sizing: border-box;font-family: Arial, sans-serif;font-size: 18px;transition: box-shadow 0.15s cubic-bezier(.4, 0, .2, 1), border-color 0.15s cubic-bezier(.4, 0, .2, 1);}}.prompt-textarea::placeholder {{font-size: 16px;color: #bfbfbf;}}.prompt-textarea:hover {{border-color: #686868;}}.prompt-textarea:focus {{outline: none;box-shadow: 0 0 5px #686868;border-color: #686868;}}.clear-btn {{position: absolute;top: 40px;right: 5px;background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;padding: 0.3em 0.6em;font-size: 14px;cursor: pointer;transition: background-color 0.15s, color 0.15s;}}.clear-btn:hover {{background-color: #686868;color: #ececec;}}.file-loader {{display: flex;align-items: center;}}.file-label {{background-color: #4b4b4b;color: white;border: none;border-radius: .5rem;padding: .7em 2em;font-size: 17px;font-weight: 500;cursor: pointer;transition: background-color 0.15s;}}.file-label:hover {{background: #686868;}}.file-input {{display: none;}}@media (max-width: 750px) {{.controls-container {{flex-direction: column;gap: 6px; align-items: stretch;}}.controls-left,.controls-right {{display: flex;flex-direction: row;margin: 0;width: 100%;gap: 10px;justify-content: space-between;align-items: start;}}.controls-left button {{flex: 1;}}.controls-right > * {{flex: 1;}}.brush-controls {{display: flex;justify-content: space-between;gap: 10px;}}.brush-controls .control-group {{flex: 1; }}.file-loader {{display: flex;justify-content: flex-end;}}}}@media (max-width: 500px) {{.brush-controls {{flex-wrap: wrap;}}}}</style></head><body><h1>Inpainting Helper</h1><div class="main-container"><div class="canvas-container"><canvas id="baseCanvas"></canvas><canvas id="overlayCanvas"></canvas></div><div class="controls-container"><div class="controls-left"><button id="generateMaskBtn" class="btn-generate" disabled>Send</button><button id="resetBtn">Reset</button></div><div class="controls-right"><div class="brush-controls"><div class="control-group"><label>Brush Size:<span id="brushSizeDisplay" class="value-display">20px</span></label><input type="range" id="brushSize" min="1" max="100" value="20"></div><div class="control-group"><label>Brush Hardness:<span id="brushHardnessDisplay" class="value-display">50%</span></label><input type="range" id="brushHardness" min="0" max="100" value="50"></div></div><div class="file-loader"><label for="imageInput" class="file-label">Load</label><input id="imageInput" type="file" accept="image/*" class="file-input"></div></div></div><div class="input-group"><label for="promptInput" class="prompt-label">Enter prompt:</label><textarea id="promptInput" class="prompt-textarea"   placeholder="What needs to be changed in the selected area?"></textarea><button class="clear-btn" id="clearBtn">Clear out</button></div></div><script>const stepsVal = {steps_val};const guidanceVal = {guidance_val};const safetyVal = {safety_val};const outputFmt = "{output_fmt}";const modelName = "{body.get("model", "flux_test_7.flux-1-1-pro")}";const chatId = "{body.get("chat_id", "dummy_chat_id")}";const sessionId = "{body.get("session_id", "dummy_session_id")}";const messageId = "{body.get("id", "dummy_message_id")}";const messagesData = {json.dumps(messages)};const pluginAction = "{__id__}";const fileUrl = "/cache/image/generations/{filename}";const baseCanvas = document.getElementById("baseCanvas");const baseCtx = baseCanvas.getContext("2d", {{ willReadFrequently: true }});const overlayCanvas = document.getElementById("overlayCanvas");const overlayCtx = overlayCanvas.getContext("2d", {{ willReadFrequently: true }});let maskCanvas = document.createElement('canvas');let maskCtx = maskCanvas.getContext('2d', {{ willReadFrequently: true }});const imageInput = document.getElementById("imageInput");const generateMaskBtn = document.getElementById("generateMaskBtn");const resetBtn = document.getElementById("resetBtn");const promptInput = document.getElementById("promptInput");const clearBtn = document.getElementById("clearBtn");const brushSizeInput = document.getElementById("brushSize");const brushHardnessInput = document.getElementById("brushHardness");const brushSizeDisplay = document.getElementById("brushSizeDisplay");const brushHardnessDisplay = document.getElementById("brushHardnessDisplay");let isDrawing = false;let overlayOpacity = 0.7;let originalBase64 = "";let promptText = "";let originalImage = new Image();let brushSize = 20;let brushHardness = 0.5;let lastX = 0;let lastY = 0;function initCanvasDimensions(width, height) {{baseCanvas.width = width;baseCanvas.height = height;overlayCanvas.width = width;overlayCanvas.height = height;maskCanvas.width = width;maskCanvas.height = height;baseCtx.clearRect(0, 0, width, height);baseCtx.drawImage(originalImage, 0, 0, width, height);overlayCtx.clearRect(0, 0, width, height);overlayCtx.globalCompositeOperation = 'source-over';overlayCtx.fillStyle = `rgba(255,255,255,${{overlayOpacity}})`;overlayCtx.fillRect(0, 0, width, height);maskCtx.clearRect(0, 0, width, height);maskCtx.fillStyle = "rgba(0,0,0,1)";maskCtx.fillRect(0, 0, width, height);}}function getCanvasCoords(e) {{const rect = overlayCanvas.getBoundingClientRect();const sx = overlayCanvas.width / rect.width;const sy = overlayCanvas.height / rect.height;return {{ x: (e.clientX - rect.left) * sx, y: (e.clientY - rect.top) * sy }};}}function drawBrushCircle(ctx, x, y) {{if (brushHardness === 1) {{ctx.fillStyle = 'rgba(255,255,255,1)';ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}} else {{const innerRadius = brushSize * brushHardness;if (innerRadius >= brushSize - 1) {{ctx.fillStyle = 'rgba(255,255,255,1)';ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}} else {{const gradient = ctx.createRadialGradient(x, y, innerRadius, x, y, brushSize);gradient.addColorStop(0, 'rgba(255,255,255,1)');gradient.addColorStop(1, 'rgba(255,255,255,0)');ctx.fillStyle = gradient;ctx.beginPath();ctx.arc(x, y, brushSize, 0, 2 * Math.PI);ctx.fill();}}}}}}function drawStrokeTo(x, y) {{overlayCtx.globalCompositeOperation = 'destination-out';drawBrushCircle(overlayCtx, x, y);overlayCtx.globalCompositeOperation = 'source-over';maskCtx.globalCompositeOperation = 'source-over';drawBrushCircle(maskCtx, x, y);}}function isCanvasBlank(cnvs) {{const context = cnvs.getContext('2d');const pixelBuffer = new Uint32Array(context.getImageData(0, 0, cnvs.width, cnvs.height).data.buffer);return !pixelBuffer.some(color => color !== 0);}}function updateControls() {{const promptValid = promptInput.value.trim().length >= 3;const maskValid = !isCanvasBlank(maskCanvas);generateMaskBtn.disabled = !maskValid || !promptValid;}}function stripBase64Prefix(dataURL) {{if (!dataURL) return "";const match = dataURL.match(/^data:.*?;base64,(.*)$/);return (match && match[1]) ? match[1] : dataURL;}}imageInput.addEventListener('change', function(e) {{const file = e.target.files[0];if (!file) return;const reader = new FileReader();reader.onload = (event) => {{originalImage.onload = () => {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);originalBase64 = baseCanvas.toDataURL('image/png');updateControls();}};originalImage.src = event.target.result;}};reader.readAsDataURL(file);}});overlayCanvas.addEventListener("mousedown", (e) => {{if (!originalImage.complete) return;isDrawing = true;const coords = getCanvasCoords(e);lastX = coords.x;lastY = coords.y;drawStrokeTo(lastX, lastY);updateControls();}});overlayCanvas.addEventListener("mousemove", (e) => {{if (!isDrawing) return;const coords = getCanvasCoords(e);const dx = coords.x - lastX;const dy = coords.y - lastY;const distance = Math.sqrt(dx * dx + dy * dy);const stepSize = 2;const steps = Math.max(Math.floor(distance / stepSize), 1);for (let i = 0; i < steps; i++) {{const t = i / steps;const x = lastX + dx * t;const y = lastY + dy * t;drawStrokeTo(x, y);}}lastX = coords.x;lastY = coords.y;updateControls();}});overlayCanvas.addEventListener("mouseup", () => {{ isDrawing = false; }});overlayCanvas.addEventListener("mouseleave", () => {{ isDrawing = false; }});brushSizeInput.addEventListener("input", (e) => {{brushSize = parseInt(e.target.value);brushSizeDisplay.textContent = brushSize + 'px';}});brushHardnessInput.addEventListener("input", (e) => {{brushHardness = parseInt(e.target.value) / 100;brushHardnessDisplay.textContent = e.target.value + '%';}});promptInput.addEventListener("input", updateControls);clearBtn.addEventListener("click", () => {{promptInput.value = "";promptInput.focus();updateControls();}});resetBtn.addEventListener("click", () => {{if (originalImage.complete && originalImage.naturalWidth > 0) {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);promptText = "";updateControls();}}}});generateMaskBtn.addEventListener("click", async () => {{const maskBase64 = stripBase64Prefix(maskCanvas.toDataURL('image/png'));const rawImage = stripBase64Prefix(originalBase64);promptText = promptInput.value.trim();const payload = {{model: modelName,chat_id: chatId,session_id: sessionId,id: messageId,messages: messagesData,image: rawImage,mask: maskBase64,prompt: promptText,steps: stepsVal,guidance: guidanceVal,output_format: outputFmt,safety_tolerance: safetyVal,}};console.log("[JS] Send payload into plugin:", payload);try {{const resp = await fetch("/api/chat/actions/" + pluginAction, {{method: "POST",headers: {{ "Content-Type": "application/json" }},body: JSON.stringify(payload)}});if (!resp.ok) {{const t = await resp.text();alert("Plugin error: " + t);}}}} catch (err) {{console.error("Fetch error:", err);alert("Fetch error: " + err);}}}});fetch(fileUrl).then(r => {{if (!r.ok) throw new Error("Loading error: " + r.status);return r.blob();}}).then(blob => {{const reader = new FileReader();reader.onload = e => {{originalImage.onload = () => {{initCanvasDimensions(originalImage.naturalWidth, originalImage.naturalHeight);originalBase64 = baseCanvas.toDataURL('image/png');console.log("[JS] Original base64 uploaded");updateControls();}};originalImage.src = e.target.result;}};reader.readAsDataURL(blob);}}).catch(e => {{console.warn("Fetch error (maybe no last image found?):", e);}});</script></body>
```
"""

        existing_artifact_msg = self.find_existing_artifact_message(messages)

        # With a slight delay to allow for rendering
        await asyncio.sleep(1)

        if not existing_artifact_msg:
            # If there was no HTML block for the mask before, send a new message
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {"role": "assistant", "content": artifact_html},
                    }
                )
                await __event_emitter__(
                    self.status_object(
                        "HTML artifact created, open it in chat", "complete", True
                    )
                )
        else:
            # Update an existing message so you don't have to draw the web page twice, three times, etc.
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
                        self.status_object("HTML artifact updated", "complete", True)
                    )
            else:
                # If ID => display the status
                if __event_emitter__:
                    await __event_emitter__(
                        self.status_object(
                            "The artifact already exists, but there is no ID to update. Open an existing artifact in the chat context menu",
                            "complete",
                            True,
                        )
                    )

        return {"status": "ok"}
