# OCR pipeline

## Цепочка

1. **PDF**: PyMuPDF (`fitz`) — извлечение текстового слоя.
2. Если текста мало — рендер страниц в растр и **Tesseract** (если установлены `pytesseract` и бинарник Tesseract в PATH).
3. **Изображение**: Tesseract через `app/ocr/tesseract_backend.py`.
4. Сырой текст + опциональная подсказка из подписи → **Qwen** с `format=json` и Pydantic-схемой (`app/structured/output.py` через `run_document_extraction` в `app/ocr/pipeline.py`).

## Настройки

- `ocr_lang` в `Settings` (по умолчанию `rus+eng`).
- Замена движка: реализовать `OcrEngine` в `app/ocr/base.py` и подключить в `pipeline.py`.

## Зависимости

- Обязательно: `pymupdf`, `Pillow`.
- Опционально: `pytesseract` + установка [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) в систему.

PaddleOCR можно добавить отдельным backend-классом без смены контрактов.
