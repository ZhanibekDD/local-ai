"""OCR через Tesseract (если установлен pytesseract + tesseract binary)."""

from __future__ import annotations

import io
import logging

from PIL import Image

from app.config.settings import get_settings
from app.ocr.base import OcrEngine, OcrResult

logger = logging.getLogger(__name__)


class TesseractEngine(OcrEngine):
    def __init__(self) -> None:
        self.lang = get_settings().ocr_lang

    def name(self) -> str:
        return "tesseract"

    def image_to_text(self, image_bytes: bytes) -> OcrResult:
        try:
            import pytesseract
        except ImportError:
            return OcrResult("", "tesseract", "pytesseract не установлен")
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            text = pytesseract.image_to_string(img, lang=self.lang.replace("+", "+"))
            return OcrResult(text.strip(), "tesseract", None)
        except Exception as e:
            logger.warning("tesseract: %s", e)
            return OcrResult("", "tesseract", str(e))
