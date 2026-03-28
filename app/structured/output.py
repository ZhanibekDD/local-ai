"""Structured output: Ollama `format=json` + текстовая JSON Schema в промпте + Pydantic post-validation.

Это не «жёсткая» схема на стороне движка генерации: модель может ошибиться, ретраи и
`repair_and_validate` снижают риск. Для максимальной строгосты смотрите версии Ollama с
нативной привязкой schema (если доступны для вашей версии) и дублируйте проверку в Python.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.llm.profiles import QwenProfile, profile_config, wrap_prompt
from app.validators.json_utils import repair_and_validate
from app.validators.retry_policy import log_structured_retry

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def schema_prompt(model_cls: Type[BaseModel]) -> str:
    schema = model_cls.model_json_schema()
    return (
        "Верни JSON строго по этой JSON Schema (только JSON, без markdown):\n"
        + json.dumps(schema, ensure_ascii=False, indent=2)
    )


def generate_structured(
    client: OllamaClient,
    qwen_model: str,
    user_prompt: str,
    model_cls: Type[T],
    *,
    rag_context: Optional[str] = None,
) -> tuple[Optional[T], str, int]:
    """
    Ретраи с подсказкой об ошибке валидации.
    Возвращает (объект|None, статус, число попыток).
    """
    s = get_settings()
    base = wrap_prompt(QwenProfile.JSON, user_prompt + "\n\n" + schema_prompt(model_cls), rag_context)
    cfg = profile_config(QwenProfile.JSON)
    opts = {"temperature": cfg.temperature, "num_predict": cfg.num_predict}

    last_status = "fail"
    for attempt in range(s.retry_max + 2):
        ok, text = client.generate(
            qwen_model,
            base,
            format_json=True,
            options=opts,
        )
        if not ok:
            last_status = text
            continue
        obj, st = repair_and_validate(text, model_cls)
        if obj is not None:
            return obj, "ok", attempt + 1
        last_status = st
        base = (
            wrap_prompt(QwenProfile.JSON, user_prompt + "\n\n" + schema_prompt(model_cls), rag_context)
            + f"\n\nПредыдущий ответ невалиден: {st}. Исправь JSON."
        )
        log_structured_retry(attempt + 1, st)

    return None, last_status, s.retry_max + 2


def generate_structured_with_image(
    client: OllamaClient,
    vision_model: str,
    image_bytes: bytes,
    model_cls: Type[T],
    *,
    extra_instruction: str = "",
) -> tuple[Optional[T], str, int]:
    """Vision + JSON schema (Ollama format=json + pydantic)."""
    import base64

    s = get_settings()
    b64 = base64.b64encode(image_bytes).decode("ascii")
    user_block = (
        (extra_instruction.strip() + "\n\n" if extra_instruction else "")
        + schema_prompt(model_cls)
    )
    base = wrap_prompt(QwenProfile.JSON, user_block)
    cfg = profile_config(QwenProfile.JSON)
    opts = {"temperature": cfg.temperature, "num_predict": cfg.num_predict}
    last_status = "fail"
    for attempt in range(s.retry_max + 2):
        ok, text = client.generate(
            vision_model,
            base,
            images=[b64],
            format_json=True,
            options=opts,
        )
        if not ok:
            last_status = text
            continue
        obj, st = repair_and_validate(text, model_cls)
        if obj is not None:
            return obj, "ok", attempt + 1
        last_status = st
        log_structured_retry(attempt + 1, st)
        base = (
            wrap_prompt(QwenProfile.JSON, user_block)
            + f"\n\nПредыдущий ответ невалиден: {st}. Исправь JSON."
        )
    return None, last_status, s.retry_max + 2
