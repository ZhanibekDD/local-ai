"""Взвешенные признаки для маршрута (устойчивее одного regex на класс)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from app.router.types import TaskType

_ROUTE_RULES: list[tuple[re.Pattern, TaskType, float, str]] = [
    (
        re.compile(
            r"(json\s*schema|верни\s+json|только\s+json|structured\s+output|"
            r"классифицируй\s+в\s+json|поля\s*:|extract\s+json|openapi|"
            r"массив\s+объект|валидн\w*\s+json|по\s+схеме)",
            re.I,
        ),
        TaskType.JSON_EXTRACTION,
        0.55,
        "kw_json",
    ),
    (
        re.compile(r"(\{\s*\"|\"\s*:\s*|yaml\s+в\s+json)", re.I),
        TaskType.JSON_EXTRACTION,
        0.25,
        "json_syntax_hint",
    ),
    (
        re.compile(
            r"(```|def\s+\w+\s*\(|class\s+\w+|import\s+\w+|SELECT\s+[\w\*]+\s+FROM|"
            r"curl\s+|docker\s+|kubectl\s+|npm\s+|pip\s+install|pytest\s+|"
            r"git\s+clone|makefile|cmake|gcc\b|powershell|bash\s+-c|"
            r"sqlalchemy|asyncio|typescript|javascript|kubernetes)",
            re.I,
        ),
        TaskType.CODE,
        0.5,
        "kw_code",
    ),
    (
        re.compile(r"(ошибк\w*\s+(компил|syntax)|stack\s*trace|traceback)", re.I),
        TaskType.CODE,
        0.35,
        "kw_error_dev",
    ),
    (
        re.compile(
            r"(чек|квитанц|накладн|счёт|счет|invoice|receipt|упд|универсал|"
            r"доверенност|договор|акт\s+выполн|pdf|скан\s+документ|"
            r"паспорт|снилс|инн\s+организац)",
            re.I,
        ),
        TaskType.DOCUMENT_OCR,
        0.45,
        "kw_document",
    ),
]


@dataclass
class ScoredRoute:
    scores: dict[TaskType, float] = field(default_factory=dict)
    reasons: dict[TaskType, list[str]] = field(default_factory=dict)


def score_text_for_routing(text: Optional[str]) -> ScoredRoute:
    t = (text or "").strip()
    out = ScoredRoute()
    if not t:
        out.scores[TaskType.UNKNOWN] = 1.0
        out.reasons[TaskType.UNKNOWN] = ["empty"]
        return out

    tl = t.lower()
    out.scores[TaskType.CHAT] = 0.2
    out.reasons[TaskType.CHAT] = ["prior_chat"]

    for rx, task, w, code in _ROUTE_RULES:
        if rx.search(tl):
            out.scores[task] = out.scores.get(task, 0.0) + w
            if task not in out.reasons:
                out.reasons[task] = []
            out.reasons[task].append(code)

    if max(out.scores.values()) <= 0.21:
        out.reasons[TaskType.CHAT].append("default_chat")

    return out


def pick_task_from_scores(sr: ScoredRoute) -> tuple[TaskType, list[str], float]:
    items = sorted(sr.scores.items(), key=lambda x: -x[1])
    if not items:
        return TaskType.CHAT, ["fallback"], 1.0
    best_t, best_s = items[0]
    second_s = items[1][1] if len(items) > 1 else 0.0
    margin = best_s - second_s
    reasons = list(sr.reasons.get(best_t, []))
    if not reasons:
        reasons = [f"score={best_s:.2f}"]
    return best_t, reasons, margin
