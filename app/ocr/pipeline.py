"""PDF/изображение → текст → qwen-json → pydantic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.ocr.pdf_text import extract_pdf_text
from app.ocr.tesseract_backend import TesseractEngine
from app.structured.output import generate_structured

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


@dataclass
class OcrPipelineResult:
    raw_text: str
    structured: Optional[BaseModel]
    status: str
    engine_trace: list[str]


def _bytes_looks_pdf(b: bytes) -> bool:
    return b[:4] == b"%PDF"


def extract_text_from_file(
    data: bytes,
    filename: str,
) -> tuple[str, list[str]]:
    trace: list[str] = []
    s = get_settings()
    if _bytes_looks_pdf(data) or filename.lower().endswith(".pdf"):
        text, pages = extract_pdf_text(data)
        trace.append(f"pymupdf_pages={pages}")
        if len(text.strip()) >= 40:
            trace.append("used_native_pdf_text")
            return text, trace
        trace.append("pdf_low_text_try_ocr")
        eng = TesseractEngine()
        try:
            import fitz

            doc = fitz.open(stream=data, filetype="pdf")
            chunks: list[str] = []
            for i in range(min(doc.page_count, 20)):
                pix = doc.load_page(i).get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                r = eng.image_to_text(img_bytes)
                chunks.append(r.text)
                trace.append(f"page_{i}_ocr={eng.name()}")
            doc.close()
            return "\n".join(chunks), trace
        except Exception as e:
            trace.append(f"pdf_ocr_fail:{e}")
            return text, trace

    eng = TesseractEngine()
    r = eng.image_to_text(data)
    trace.append(f"image_ocr={eng.name()}")
    if r.warning:
        trace.append(f"warn:{r.warning}")
    return r.text, trace


def run_document_extraction(
    client: OllamaClient,
    data: bytes,
    filename: str,
    model_cls: Type[T],
    extra_hint: str = "",
) -> OcrPipelineResult:
    raw, trace = extract_text_from_file(data, filename)
    models = client.list_models()
    qwen = pick_model(
        models,
        get_settings().model_qwen_chat,
        get_settings().model_qwen_fallback,
    )
    hint = (
        "Ниже текст документа после OCR/извлечения. Извлеки поля в JSON по схеме.\n"
        + (extra_hint + "\n" if extra_hint else "")
        + "---\n"
        + raw[:8000]
    )
    obj, st, tries = generate_structured(client, qwen, hint, model_cls)
    status = f"{st}_tries={tries}"
    if obj is None:
        logger.warning("document extraction failed: %s", status)
        return OcrPipelineResult(raw_text=raw, structured=None, status=status, engine_trace=trace)
    return OcrPipelineResult(raw_text=raw, structured=obj, status="ok", engine_trace=trace)
