"""Классификация документа / тикета."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DocumentClassification(BaseModel):
    category: str = ""
    subcategory: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class SupportTicketClassification(BaseModel):
    intent: str = ""
    urgency: str = "low"  # low|medium|high
    product_area: Optional[str] = None
    summary: Optional[str] = None
