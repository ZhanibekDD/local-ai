"""Схема извлечения чека."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReceiptExtraction(BaseModel):
    merchant: Optional[str] = None
    date: Optional[str] = None
    total: Optional[str] = None
    currency: Optional[str] = None
    items: list[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(None, ge=0, le=1)
