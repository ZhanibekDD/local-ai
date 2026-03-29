# Состояние проекта и продолжение работы

Документ для человека и для ИИ: **на чём остановились**, **что уже сделано**, **куда двигаться**.

Обновляй дату внизу при существенных изменениях.

## Репозиторий

- **GitHub:** `https://github.com/ZhanibekDD/local-ai` (ветка `main`).
- **Пакет:** `local-ai`, точка входа бота: `python telegram-bot-advanced.py`.
- Секреты в истории git ранее чистились (`git filter-repo`); при утечке — **ротация паролей/ключей**.

## Что уже реализовано (кратко)

- **Telegram-бот** (`app/bot/telegram_app.py`): чаты в SQLite, роутер, vision, OCR→JSON, `/reason`, меню.
- **Режим OCR** хранится **на пользователя** в SQLite (`force_ocr` в `user_settings`): кнопка «📄 OCR: ВКЛ/ВЫКЛ», callback `toggle_ocr`, команда `/ocr`.
- **Remote OCR:** `OCR_REMOTE_URL` (дефолт `http://localhost:8081/ocr/extract`), POST `multipart`, поле `file`. Клиент **терпимый** к JSON: `text`, вложенные `res`/`result`/`data`, `rec_texts`, `raw_text_excerpt`, `fields`, и т.д. — см. `app/ocr/extract_text.py`, `OCR_PIPELINE.md`.
- **Настройки** (`app/config/settings.py`): `.env` только из **корня репозитория** (если файл есть); без `.env` работают дефолты `OLLAMA_BASE_URL` и `OCR_REMOTE_URL`; `OCR_ENGINE` через env-алиас.
- **Eval, training-скрипты** (`eval/`, `training/`), **доки** SFT: `docs/FINETUNING.md`, серверный runbook: `docs/RUNBOOK-SERVER.md`.
- **Тесты:** `pytest`, smoke в `tests/smoke/`.

## Локальный ПК (типичный сценарий)

1. Клонировать репо, `pip install -e ".[dev]"` (при необходимости `train`).
2. Скопировать `.env.example` → `.env`, задать **`TELEGRAM_BOT_TOKEN`**.
3. SSH-туннели (пример): Ollama `11434`, OCR API `8081` → `localhost`.
4. Запуск: `python telegram-bot-advanced.py`.

В `.env` ожидаемый минимум для туннелей:

```env
OLLAMA_BASE_URL=http://localhost:11434
OCR_REMOTE_URL=http://localhost:8081/ocr/extract
OCR_ENGINE=auto
```

## На чём остановились / риски

- **Серверный OCR API** должен отдавать осмысленный текст в одном из поддерживаемых полей (`text`, вложенные структуры, `rec_texts`…). Если в ответе «мусор» или пустой текст — downstream (Qwen JSON) будет слабым; править **контракт API на сервере** — предпочтительно.
- При ошибке remote OCR бот **падает в локальный** пайплайн (PyMuPDF/Tesseract и т.д.). Если **Tesseract не установлен** на ПК — в trace будут предупреждения; либо ставить Tesseract, либо в перспективе флаг «только remote» (пока не внедрён — см. обсуждение в чате).
- Проверка API с **Linux-сервера:** `curl` (не `curl.exe`), путь к файлу в стиле Linux, см. ответы в переписке.

## Логичные следующие шаги

1. Зафиксировать на сервере **стабильный JSON** ответа OCR (`text` + `trace` + `filename`).
2. Прогнать `curl` с ПК на `localhost:8081` и убедиться, что бот в trace видит `engine=remote_http`, без лишнего fallback.
3. **SFT / LLaMA-Factory** — по `docs/FINETUNING.md` и `training/` (данные, не код бота).
4. При работе **с другого устройства:** `git clone`, тот же `.env`, те же туннели к своему серверу.

## Ключевые пути кода

| Область | Файлы |
|--------|--------|
| Бот, меню, OCR-режим | `app/bot/telegram_app.py` |
| Настройки | `app/config/settings.py` |
| Remote/local OCR | `app/ocr/extract_text.py`, `app/ocr/pipeline.py` |
| SQLite | `app/memory/store.py` |
| Роутер | `app/router/classifier.py`, `scoring.py` |
| Ollama | `app/llm/ollama_client.py` |

---

*Последнее обновление заметок: 2026-03-28*
