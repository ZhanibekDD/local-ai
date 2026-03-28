"""Извлечение текста из PDF/изображения с учётом ocr_engine (настройка = фактическое поведение)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import requests

from app.config.settings import get_settings
from app.ocr.pdf_text import extract_pdf_text
from app.ocr.tesseract_backend import TesseractEngine

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _extract_via_remote(url: str, data: bytes, filename: str) -> tuple[str, list[str]]:
    """POST multipart/form-data, поле ``file``. Ответ: JSON с text/raw_text/extracted_text/content или text/plain."""
    trace = [f"remote_post={url}"]
    safe_name = filename.strip() or "document.bin"
    r = requests.post(
        url,
        files={"file": (safe_name, data)},
        timeout=(15, 180),
    )
    r.raise_for_status()
    try:
        body = r.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        for key in ("text", "raw_text", "extracted_text", "ocr_text", "content"):
            val = body.get(key)
            if isinstance(val, str) and val.strip():
                trace.append(f"remote_json_key={key}")
                return val, trace
        raise ValueError("remote OCR JSON без текстового поля")
    text = r.text.strip()
    if not text:
        raise ValueError("remote OCR пустой ответ")
    trace.append("remote_body=plain")
    return text, trace


def _bytes_looks_pdf(b: bytes) -> bool:
    return len(b) >= 4 and b[:4] == b"%PDF"


def _pdf_render_tesseract(data: bytes) -> tuple[str, list[str]]:
    import fitz

    eng = TesseractEngine()
    trace: list[str] = []
    doc = fitz.open(stream=data, filetype="pdf")
    mat = fitz.Matrix(2.0, 2.0)
    chunks: list[str] = []
    for i in range(min(doc.page_count, 20)):
        pix = doc.load_page(i).get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        r = eng.image_to_text(img_bytes)
        chunks.append(r.text)
        trace.append(f"page_{i}_ocr={eng.name()}")
    doc.close()
    return "\n".join(chunks), trace


def extract_text_from_file(data: bytes, filename: str) -> tuple[str, list[str]]:
    """
    ocr_engine:
      auto — текстовый слой PDF; если мало текста — растр + Tesseract; изображения — Tesseract.
      pymupdf — только текстовый слой PDF; изображения без Tesseract (пусто + предупреждение в trace).
      tesseract — для PDF всегда растр+OCR; изображения — Tesseract.
      paddle — если установлен PaddleOCR; иначе trace paddle_fallback и режим как auto.

    Если задан OCR_REMOTE_URL — сначала HTTP POST (поле file); при ошибке — fallback на локальный OCR_ENGINE.
    """
    trace: list[str] = []
    s = get_settings()
    remote = (s.ocr_remote_url or "").strip()
    if remote:
        try:
            text, tr = _extract_via_remote(remote, data, filename)
            return text, tr + ["engine=remote_http"]
        except Exception as e:
            logger.warning("remote OCR failed, local fallback: %s", e)
            trace.append(f"remote_ocr_error:{type(e).__name__}:{e}")

    mode = (s.ocr_engine or "auto").strip().lower()

    if mode == "paddle":
        try:
            from app.ocr.paddle_backend import paddle_image_to_text, paddle_pdf_to_text

            if _bytes_looks_pdf(data) or filename.lower().endswith(".pdf"):
                text, tr = paddle_pdf_to_text(data)
                trace.extend(tr)
                return text, trace
            text, tr = paddle_image_to_text(data)
            trace.extend(tr)
            return text, trace
        except Exception as e:
            trace.append(f"paddle_fallback:{e}")
            mode = "auto"

    if _bytes_looks_pdf(data) or filename.lower().endswith(".pdf"):
        text, pages = extract_pdf_text(data)
        trace.append(f"pymupdf_pages={pages}")

        if mode == "pymupdf":
            trace.append("engine=pymupdf_text_only")
            return text, trace

        if mode == "tesseract":
            trace.append("engine=tesseract_raster_pdf")
            t2, tr2 = _pdf_render_tesseract(data)
            trace.extend(tr2)
            return t2 if t2.strip() else text, trace

        # auto
        if len(text.strip()) >= 40:
            trace.append("used_native_pdf_text")
            return text, trace
        trace.append("pdf_low_text_try_ocr")
        try:
            t2, tr2 = _pdf_render_tesseract(data)
            trace.extend(tr2)
            return t2 if t2.strip() else text, trace
        except Exception as e:
            trace.append(f"pdf_ocr_fail:{e}")
            return text, trace

    # изображение
    if mode == "pymupdf":
        trace.append("engine=pymupdf_skip_image")
        return "", trace

    eng = TesseractEngine()
    r = eng.image_to_text(data)
    trace.append(f"image_ocr={eng.name()}_mode={mode}")
    if r.warning:
        trace.append(f"warn:{r.warning}")
    return r.text, trace
