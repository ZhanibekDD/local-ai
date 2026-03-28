"""Универсальный JSON для свободного извлечения."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FlexibleExtraction(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    labels: list[str] = Field(default_factory=list)
