"""Опциональное уточнение маршрута через короткий JSON-ответ модели (когда эвристика неуверенна)."""

from __future__ import annotations

import logging
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.router.types import TaskType
from app.structured.output import generate_structured

logger = logging.getLogger(__name__)


class _RouterPick(BaseModel):
    task: Literal["chat", "json", "code", "doc_hint"]
    confidence: float = Field(default=0.7, ge=0, le=1)


_TASK_MAP = {
    "chat": TaskType.CHAT,
    "json": TaskType.JSON_EXTRACTION,
    "code": TaskType.CODE,
    "doc_hint": TaskType.DOCUMENT_OCR,
}


def disambiguate_with_llm(
    client: OllamaClient,
    user_text: str,
    *,
    heuristic_guess: TaskType,
    margin: float,
) -> Optional[TaskType]:
    """
    Если включено в настройках — один короткий вызов Qwen-json.
    Возвращает None при сбое (оставить эвристику).
    """
    s = get_settings()
    if not s.router_llm_disambiguate:
        return None
    models = client.list_models()
    if not models:
        return None
    m = pick_model(models, s.model_qwen_chat, s.model_qwen_fallback)
    hint = (
        f"Классифицируй запрос пользователя. Эвристика дала {heuristic_guess.value}, "
        f"margin={margin:.2f}.\n\n"
        f"Текст:\n{user_text[:4000]}"
    )
    obj, st, _ = generate_structured(client, m, hint, _RouterPick)
    if obj is None:
        logger.warning("router LLM disambiguate failed: %s", st)
        return None
    t = _TASK_MAP.get(obj.task)
    if t is None:
        return None
    if obj.confidence < s.router_llm_min_confidence:
        logger.info("router LLM low confidence %.2f", obj.confidence)
        return None
    return t
