"""Поля после OCR (универсально)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class OcrParsedFields(BaseModel):
    raw_text_excerpt: str = ""
    language_guess: Optional[str] = None
    fields: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
