"""Типы задач и решение маршрутизатора."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskType(str, Enum):
    CHAT = "chat"
    JSON_EXTRACTION = "json"
    CODE = "code"
    VISION_SCENE = "vision"
    DOCUMENT_OCR = "ocr_doc"
    UNKNOWN = "unknown"


@dataclass
class RouteDecision:
    task: TaskType
    model_key: str  # chat | json | code | vision | ocr_then_json
    profile: str  # qwen-chat, qwen-json, ...
    reason_codes: list[str] = field(default_factory=list)
    debug: dict[str, Any] = field(default_factory=dict)

    def explain(self) -> str:
        return "; ".join(self.reason_codes) if self.reason_codes else self.task.value
