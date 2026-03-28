"""PaddleOCR — опционально; при ошибке импорта/инференса вызывающий код уходит в fallback."""

from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def paddle_image_to_text(data: bytes) -> tuple[str, list[str]]:
    trace = ["paddle_image"]
    try:
        import numpy as np
        from paddleocr import PaddleOCR  # type: ignore[import-untyped]
    except ImportError as e:
        trace.append(f"import_error:{e}")
        raise RuntimeError("paddleocr не установлен") from e

    img = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
    ocr = PaddleOCR(use_angle_cls=True, lang="ru", show_log=False)
    res = ocr.ocr(img, cls=True)
    lines: list[str] = []
    if res and res[0]:
        for line in res[0]:
            if line and len(line) >= 2 and line[1]:
                lines.append(str(line[1][0]))
    text = "\n".join(lines).strip()
    trace.append("ok")
    return text, trace


def paddle_pdf_to_text(data: bytes) -> tuple[str, list[str]]:
    import fitz

    trace: list[str] = ["paddle_pdf"]
    doc = fitz.open(stream=data, filetype="pdf")
    mat = fitz.Matrix(2.0, 2.0)
    parts: list[str] = []
    for i in range(min(doc.page_count, 10)):
        pix = doc.load_page(i).get_pixmap(matrix=mat)
        b = pix.tobytes("png")
        t, tr = paddle_image_to_text(b)
        parts.append(t)
        trace.append(f"p{i}")
        trace.extend(tr)
    doc.close()
    return "\n".join(parts), trace
