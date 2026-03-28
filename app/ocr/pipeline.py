"""PDF/изображение → текст → qwen-json → pydantic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.ocr.extract_text import extract_text_from_file
from app.structured.output import generate_structured

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


@dataclass
class OcrPipelineResult:
    raw_text: str
    structured: Optional[BaseModel]
    status: str
    engine_trace: list[str]


def run_document_extraction(
    client: OllamaClient,
    data: bytes,
    filename: str,
    model_cls: Type[T],
    extra_hint: str = "",
) -> OcrPipelineResult:
    raw, trace = extract_text_from_file(data, filename)
    models = client.list_models()
    qwen = pick_model(
        models,
        get_settings().model_qwen_chat,
        get_settings().model_qwen_fallback,
    )
    hint = (
        "Ниже текст документа после OCR/извлечения. Извлеки поля в JSON по схеме.\n"
        + (extra_hint + "\n" if extra_hint else "")
        + "---\n"
        + raw[:8000]
    )
    obj, st, tries = generate_structured(client, qwen, hint, model_cls)
    status = f"{st}_tries={tries}"
    if obj is None:
        logger.warning("document extraction failed: %s", status)
        return OcrPipelineResult(raw_text=raw, structured=None, status=status, engine_trace=trace)
    return OcrPipelineResult(raw_text=raw, structured=obj, status="ok", engine_trace=trace)
