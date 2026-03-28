"""HTTP-клиент Ollama: generate, JSON format, vision, ретраи."""

from __future__ import annotations

import base64
import logging
import time
from typing import Any, Optional

import requests

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.s = settings or get_settings()
        self.base = self.s.ollama_base_url.rstrip("/")

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base}/api/tags", timeout=15)
            if r.status_code != 200:
                return []
            return [m["name"] for m in r.json().get("models", [])]
        except Exception as e:
            logger.warning("list_models: %s", e)
            return []

    def resolve_model(self, base_name: str, available: list[str]) -> str:
        if not available:
            return base_name
        for m in available:
            if m == base_name or m.startswith(base_name + ":"):
                return m
        for m in available:
            if base_name.split(":")[0] in m:
                return m
        return available[0]

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        images: Optional[list[str]] = None,
        format_json: bool = False,
        options: Optional[dict[str, Any]] = None,
        timeout: int = 300,
    ) -> tuple[bool, str]:
        """Возвращает (ok, text). При ошибке ok=False, text=сообщение."""
        body: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            body["images"] = images
        if format_json:
            body["format"] = "json"
        opts = {"num_ctx": self.s.num_ctx_default}
        if options:
            opts.update(options)
        body["options"] = opts

        last_err = ""
        for attempt in range(self.s.retry_max + 1):
            try:
                r = requests.post(f"{self.base}/api/generate", json=body, timeout=timeout)
                if r.status_code == 200:
                    return True, (r.json().get("response") or "").strip()
                last_err = f"HTTP {r.status_code}"
            except Exception as e:
                last_err = str(e)
            if attempt < self.s.retry_max:
                time.sleep(self.s.retry_backoff_sec * (attempt + 1))
        logger.error("generate failed: %s", last_err)
        return False, f"Error: {last_err}"

    def generate_with_image_bytes(
        self,
        model: str,
        prompt: str,
        image_bytes: bytes,
        *,
        options: Optional[dict[str, Any]] = None,
        timeout: int = 300,
    ) -> tuple[bool, str]:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        opt = {"temperature": 0.5}
        if options:
            opt.update(options)
        return self.generate(model, prompt, images=[b64], options=opt, timeout=timeout)


def pick_model(available: list[str], *candidates: str) -> str:
    for c in candidates:
        for m in available:
            if m == c or m.startswith(c + ":"):
                return m
    return candidates[0] if candidates else (available[0] if available else "qwen2.5:72b")
