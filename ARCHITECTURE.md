# Архитектура

## Слои

- **`app/config/settings.py`** — `pydantic-settings`: URL Ollama, токен Telegram, пути SQLite, имена моделей, лимиты контекста и ретраи.
- **`app/llm/`** — `OllamaClient` (generate, vision, `format=json`), профили Qwen (`profiles.py`), опционально `judge.py` для внутренней проверки.
- **`app/router/`** — эвристический классификатор (`classifier.py`) и `RouteDecision` (`types.py`): чат / JSON / код / vision / OCR-документ.
- **`app/structured/output.py`** — привязка ответа к Pydantic-схеме, ретраи с текстом ошибки, `generate_structured_with_image` для vision+JSON.
- **`app/schemas/`** — Pydantic-модели: чек, накладная, классификация, гибкое JSON (`flexible.py`).
- **`app/memory/`** — SQLite (`store.py`) и сборка контекста с лимитами (`context.py`).
- **`app/ocr/`** — абстракция OCR, PyMuPDF для текста PDF, Tesseract при низком тексте или для изображений (`pipeline.py`).
- **`app/vision/service.py`** — описание сцены через vision-модель (не основной путь для русских реквизитов).
- **`app/bot/`** — `pipeline.py` (текстовая оркестрация), `reasoning.py`, `telegram_app.py` (handlers, фото, документы).
- **`eval/`** — JSONL-кейсы, `run_eval.py`, отчёты.
- **`modelfiles/`** — шаблоны Ollama для профилей `qwen-chat`, `qwen-json`, `qwen-rag`, `qwen-judge`.

## Потоки данных

1. **Текст** → router → `process_text_chat` → Qwen / DeepSeek / structured JSON.
2. **Фото** → router → vision **или** OCR+JSON (если подпись/маршрут указывает на документ).
3. **Файл (PDF/изображение)** → `run_document_extraction` → текст → `generate_structured` → Pydantic.

## Точка входа

`telegram-bot-advanced.py` добавляет корень проекта в `sys.path` и вызывает `app.bot.telegram_app:main`.
