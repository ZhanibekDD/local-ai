"""Эвристическая классификация без лишних вызовов LLM."""

from __future__ import annotations

import re
from typing import Optional

from app.router.types import RouteDecision, TaskType

_CODE_HINT = re.compile(
    r"(```|def\s+\w+\s*\(|class\s+\w+|import\s+\w+|SELECT\s+|FROM\s+\w+|curl\s+|docker\s+|npm\s+)",
    re.I,
)
_JSON_HINT = re.compile(
    r"(json\s*schema|верни\s+json|только\s+json|structured\s+output|классифицируй\s+в\s+json|поля\s*:)",
    re.I,
)
_DOC_HINT = re.compile(
    r"(чек|квитанц|накладн|счёт|счет|invoice|receipt|pdf|скан\s+документ)",
    re.I,
)


def classify_text(text: str) -> tuple[TaskType, list[str]]:
    t = (text or "").strip()
    reasons: list[str] = []
    if not t:
        return TaskType.UNKNOWN, ["empty"]

    if _JSON_HINT.search(t):
        reasons.append("keyword_json")
        return TaskType.JSON_EXTRACTION, reasons

    if _CODE_HINT.search(t):
        reasons.append("keyword_code")
        return TaskType.CODE, reasons

    if _DOC_HINT.search(t):
        reasons.append("keyword_document")
        return TaskType.DOCUMENT_OCR, reasons

    reasons.append("default_chat")
    return TaskType.CHAT, reasons


def classify_incoming(
    *,
    text: Optional[str],
    has_photo: bool,
    has_document: bool,
    mime: Optional[str],
) -> RouteDecision:
    """Определяет маршрут до генерации."""
    reasons: list[str] = []
    dbg: dict = {}

    if has_document:
        reasons.append("telegram_document")
        return RouteDecision(
            TaskType.DOCUMENT_OCR,
            "ocr_then_json",
            "qwen-json",
            reason_codes=reasons,
            debug={**dbg, "mime": mime},
        )

    if has_photo:
        # Фото без явного «документ/чек» — vision; документные ключевые слова в подписи → OCR
        cap = (text or "").strip()
        if _DOC_HINT.search(cap):
            reasons.append("photo_caption_document")
            return RouteDecision(
                TaskType.DOCUMENT_OCR,
                "ocr_then_json",
                "qwen-json",
                reason_codes=reasons,
                debug=dbg,
            )
        reasons.append("photo")
        return RouteDecision(
            TaskType.VISION_SCENE,
            "vision",
            "vision",
            reason_codes=reasons,
            debug=dbg,
        )

    task, r = classify_text(text or "")
    reasons.extend(r)

    if task == TaskType.JSON_EXTRACTION:
        return RouteDecision(task, "json", "qwen-json", reason_codes=reasons, debug=dbg)
    if task == TaskType.CODE:
        return RouteDecision(task, "code", "deepseek", reason_codes=reasons, debug=dbg)
    if task == TaskType.DOCUMENT_OCR:
        return RouteDecision(task, "ocr_then_json", "qwen-json", reason_codes=reasons, debug=dbg)

    return RouteDecision(TaskType.CHAT, "chat", "qwen-chat", reason_codes=reasons, debug=dbg)
