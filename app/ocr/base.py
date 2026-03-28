"""Абстракция OCR-движка."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class OcrResult:
    text: str
    engine: str
    warning: Optional[str] = None


class OcrEngine(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def image_to_text(self, image_bytes: bytes) -> OcrResult:
        pass
