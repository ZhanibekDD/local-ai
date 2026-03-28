"""Извлечение текста из PDF без OCR (PyMuPDF)."""

from __future__ import annotations

from typing import Tuple


def extract_pdf_text(pdf_bytes: bytes) -> Tuple[str, int]:
    import fitz  # pymupdf

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    parts: list[str] = []
    for i in range(doc.page_count):
        parts.append(doc.load_page(i).get_text("text"))
    doc.close()
    full = "\n".join(parts).strip()
    return full, len(parts)
