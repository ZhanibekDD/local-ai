"""Vision: описание, UI, тип сцены — отдельно от документного OCR."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.schemas.image_analysis import ImageAnalysisSummary
from app.structured.output import generate_structured_with_image

logger = logging.getLogger(__name__)


class VisionMode(str, Enum):
    BASE = "base"
    OBJECT_TYPE = "object_type"
    UI_SCREENSHOT = "ui"
    EXTRACTION_SUMMARY = "extract_summary"


_PROMPTS = {
    VisionMode.BASE: "Опиши изображение кратко на русском: что на нём, основные объекты, настроение/сцена.",
    VisionMode.OBJECT_TYPE: "Определи тип сцены: фото, скриншот интерфейса, документ, другое. Перечисли ключевые объекты.",
    VisionMode.UI_SCREENSHOT: (
        "Это скриншот интерфейса. Кратко: какое приложение/сайт, основные области, видимый текст (если есть)."
    ),
    VisionMode.EXTRACTION_SUMMARY: (
        "Дай краткое резюме содержимого изображения для последующей обработки (не выдумывай текст с мелких деталей)."
    ),
}


def vision_analyze(
    client: OllamaClient,
    image_bytes: bytes,
    mode: VisionMode = VisionMode.BASE,
    *,
    structured: bool = False,
) -> str:
    s = get_settings()
    models = client.list_models()
    vm = pick_model(models, s.model_vision, "llama3.2-vision")
    prompt = _PROMPTS.get(mode, _PROMPTS[VisionMode.BASE])
    full = f"Ты AI ассистент. Отвечай ТОЛЬКО на русском. {prompt}"
    ok, text = client.generate_with_image_bytes(vm, full, image_bytes)
    if not ok:
        logger.error("vision: %s", text)
        return text
    return text


def vision_structured_summary(client: OllamaClient, image_bytes: bytes) -> Optional[ImageAnalysisSummary]:
    s = get_settings()
    models = client.list_models()
    vm = pick_model(models, s.model_vision, "llama3.2-vision")
    extra = (
        "По изображению заполни поля JSON. scene_type: ui_screenshot|photo|document_scan|other. "
        "description — кратко по-русски."
    )
    obj, st, _ = generate_structured_with_image(
        client, vm, image_bytes, ImageAnalysisSummary, extra_instruction=extra
    )
    if obj is None:
        logger.warning("vision structured failed: %s", st)
        return None
    return obj
