"""Очистка и парсинг JSON из ответа модели."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def strip_json_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
        t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def parse_json_loose(raw: str) -> Optional[Any]:
    s = strip_json_fences(raw)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # иногда модель добавляет текст после JSON
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def validate_model(data: Any, model: Type[T]) -> tuple[Optional[T], Optional[str]]:
    try:
        return model.model_validate(data), None
    except ValidationError as e:
        return None, str(e)


def repair_and_validate(raw: str, model: Type[T]) -> tuple[Optional[T], str]:
    """Парсинг + pydantic; при ошибке возвращает (None, reason)."""
    data = parse_json_loose(raw)
    if data is None:
        return None, "invalid_json"
    obj, err = validate_model(data, model)
    if obj is not None:
        return obj, "ok"
    return None, err or "validation"
