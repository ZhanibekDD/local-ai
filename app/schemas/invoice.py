"""Накладная / счёт."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class InvoiceExtraction(BaseModel):
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    total: Optional[str] = None
    vat: Optional[str] = None
    lines: list[str] = Field(default_factory=list)
