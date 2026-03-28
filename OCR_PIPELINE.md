# OCR pipeline

## Реализация (`app/ocr/extract_text.py`)

Переменная **`OCR_REMOTE_URL`** (см. `.env.example`): если задана непустая строка, сначала выполняется **POST** файла на этот URL (`multipart/form-data`, поле **`file`**). Ответ: JSON с одним из полей `text` / `raw_text` / `extracted_text` / `ocr_text` / `content`, либо обычный текст. При ошибке HTTP/формата — **fallback** на локальные движки ниже.

Переменная **`OCR_ENGINE`** (см. `Settings.ocr_engine`) задаёт локальное поведение (если remote не задан или упал):

| Значение | PDF | Изображение |
|----------|-----|-------------|
| **auto** | Текстовый слой PyMuPDF; если текста мало — растр страниц + Tesseract | Tesseract |
| **pymupdf** | Только текстовый слой | Пустой текст (в trace — `pymupdf_skip_image`) |
| **tesseract** | Всегда растр + Tesseract | Tesseract |
| **paddle** | PaddleOCR (`app/ocr/paddle_backend.py`), если установлен `paddleocr`; иначе trace `paddle_fallback` и режим как **auto** | То же |

Дальше: сырой текст → `run_document_extraction` → Qwen `format=json` + Pydantic (`app/ocr/pipeline.py`).

## Зависимости

- Обязательно: `pymupdf`, `Pillow`, `numpy` (для опционального Paddle).
- Tesseract: бинарник в PATH + пакет `pytesseract` (опционально).
- PaddleOCR: установка вручную (`paddleocr` / `paddlepaddle`), не входит в базовые зависимости `pyproject.toml`.

## Схемы извлечения

См. `app/ocr/schema_pick.py`: накладная, чек, тикет, классификация документа или универсальный `OcrParsedFields`.
