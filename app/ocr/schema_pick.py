"""Выбор Pydantic-схемы для документа по имени файла и подписи."""

from __future__ import annotations

from typing import Type

from pydantic import BaseModel

from app.schemas.classification import DocumentClassification, SupportTicketClassification
from app.schemas.invoice import InvoiceExtraction
from app.schemas.ocr_fields import OcrParsedFields
from app.schemas.receipt import ReceiptExtraction

_INVOICE_KEYS = (
    "накладн",
    "invoice",
    "счёт-факт",
    "счет-факт",
    "упд",
    "универсал",
    "bill",
    "счет-фактур",
)

_RECEIPT_KEYS = (
    "чек",
    "квитанц",
    "receipt",
    "покупк",
    "касс",
    "pos",
    "фиск",
)

_SUPPORT_KEYS = (
    "тикет",
    "ticket",
    "жалоб",
    "support",
    "обращен",
    "helpdesk",
    "служб",
    "поддержк",
)

_CLASSIFY_KEYS = (
    "классифиц",
    "тип документ",
    "какой документ",
    "категор",
)


def pick_document_schema(filename: str, caption: str) -> Type[BaseModel]:
    fn = (filename or "").lower()
    cap = (caption or "").lower()
    blob = fn + " " + cap

    if any(k in blob for k in _INVOICE_KEYS):
        return InvoiceExtraction
    if any(k in blob for k in _RECEIPT_KEYS):
        return ReceiptExtraction
    if any(k in blob for k in _SUPPORT_KEYS):
        return SupportTicketClassification
    if any(k in blob for k in _CLASSIFY_KEYS):
        return DocumentClassification

    # Универсальные поля вместо принудительного «чека»
    return OcrParsedFields
