"""Маршрутизация: скоринг + опциональное уточнение через LLM."""

from __future__ import annotations

import re
from typing import Optional

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient
from app.router.llm_disambiguate import disambiguate_with_llm
from app.router.scoring import pick_task_from_scores, score_text_for_routing
from app.router.types import RouteDecision, TaskType

# Подпись к фото / документ — отдельные эвристики (короткий текст)
_DOC_CAPTION = re.compile(
    r"(чек|квитанц|накладн|счёт|счет|invoice|receipt|pdf|скан|документ|упд)",
    re.I,
)


def classify_text(text: str) -> tuple[TaskType, list[str]]:
    """Совместимость: тип + причины (без margin / LLM)."""
    sr = score_text_for_routing(text)
    task, reasons, _ = pick_task_from_scores(sr)
    return task, reasons


def classify_incoming(
    *,
    text: Optional[str],
    has_photo: bool,
    has_document: bool,
    mime: Optional[str],
    ollama_client: Optional[OllamaClient] = None,
) -> RouteDecision:
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
        cap = (text or "").strip()
        if _DOC_CAPTION.search(cap):
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

    sr = score_text_for_routing(text or "")
    task, r, margin = pick_task_from_scores(sr)
    reasons.extend(r)
    dbg["scores"] = {k.value: round(v, 3) for k, v in sr.scores.items()}
    dbg["margin"] = round(margin, 3)

    s = get_settings()
    if (
        ollama_client
        and s.router_llm_disambiguate
        and margin < s.router_ambiguous_margin
        and task not in (TaskType.UNKNOWN,)
    ):
        alt = disambiguate_with_llm(
            ollama_client,
            text or "",
            heuristic_guess=task,
            margin=margin,
        )
        if alt is not None:
            task = alt
            reasons.append("llm_disambiguate")
            dbg["llm_override"] = True

    if task == TaskType.UNKNOWN:
        return RouteDecision(TaskType.CHAT, "chat", "qwen-chat", reason_codes=reasons, debug=dbg)

    if task == TaskType.JSON_EXTRACTION:
        return RouteDecision(task, "json", "qwen-json", reason_codes=reasons, debug=dbg)
    if task == TaskType.CODE:
        return RouteDecision(task, "code", "deepseek", reason_codes=reasons, debug=dbg)
    if task == TaskType.DOCUMENT_OCR:
        return RouteDecision(task, "ocr_then_json", "qwen-json", reason_codes=reasons, debug=dbg)

    return RouteDecision(TaskType.CHAT, "chat", "qwen-chat", reason_codes=reasons, debug=dbg)
