"""Выбор Pydantic-схемы для документа по имени файла и подписи."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from app.schemas.invoice import InvoiceExtraction
from app.schemas.receipt import ReceiptExtraction

_INVOICE_KEYS = (
    "накладн",
    "invoice",
    "счёт-факт",
    "счет-факт",
    "упд",
    "универсал",
    "акт",
    "bill",
)


def pick_document_schema(filename: str, caption: str) -> Type[BaseModel]:
    fn = (filename or "").lower()
    cap = (caption or "").lower()
    blob = fn + " " + cap
    if any(k in blob for k in _INVOICE_KEYS):
        return InvoiceExtraction
    return ReceiptExtraction
