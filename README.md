# local-ai

Локальная AI-система вокруг **Ollama**: Telegram-бот, маршрутизация задач, structured output (Pydantic), OCR документов, vision, eval и опциональный HTTP API.

Всё работает **без облачных LLM API** — инференс на вашем железе (типично: сервер с GPU + Ollama).

## Возможности

| Компонент | Описание |
|-----------|----------|
| **`app/bot/`** | Telegram: диалоги, SQLite, режим рассуждения, фото/документы |
| **`app/router/`** | Скоринг + опциональное LLM-уточнение маршрута |
| **`app/ocr/`** | PDF/изображения → текст (`OCR_ENGINE`: auto / pymupdf / tesseract / paddle) |
| **`app/vision/`** | Описание сцен через vision-модель |
| **`app/structured/`** | JSON + Pydantic-валидация и ретраи |
| **`eval/`** | Прогоны и отчёты по кейсам |
| **`app/api/`** | FastAPI: `/health`, `/v1/models` |

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md), [ROUTING.md](ROUTING.md), [OCR_PIPELINE.md](OCR_PIPELINE.md), [EVAL.md](EVAL.md), [QUICKSTART.md](QUICKSTART.md), [docs/FINETUNING.md](docs/FINETUNING.md) (первый цикл SFT: Qwen2.5-14B-Instruct, датасеты, объёмы). Данные и скрипты под SFT: [data/sft/README.md](data/sft/README.md), каталог `training/`. **Пошагово на своём сервере:** [docs/RUNBOOK-SERVER.md](docs/RUNBOOK-SERVER.md).

## Требования

- Python 3.10+
- Установленный и доступный **Ollama** (локально или по SSH-туннелю, например `localhost:11434`)
- Для бота: токен от [@BotFather](https://t.me/BotFather) в переменной окружения

## Установка

Из корня репозитория:

```bash
pip install -e .
```

Опционально: `pip install -e ".[dev,ssh]"` — dev-инструменты и `paramiko` для старых SSH-скриптов.

Скопируйте [`.env.example`](.env.example) в `.env` и задайте `TELEGRAM_BOT_TOKEN`, при необходимости `OLLAMA_BASE_URL`.

## Запуск Telegram-бота

```bash
python telegram-bot-advanced.py
```

## Локальный HTTP (опционально)

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8080
```

## Eval

```bash
python eval/run_eval.py
python eval/generate_report.py
```

## Документация по железу и серверу

Частные шаги установки ОС/GPU/Ollama на конкретной машине вынесены в **[docs/server/](docs/server/)** — там только **шаблоны** (подставьте свои IP, пользователей и секреты локально). **Не коммитьте** реальные пароли и адреса.

## Безопасность

См. [docs/SECURITY.md](docs/SECURITY.md). Реальные учётные данные не должны быть в репозитории; при утечке в истории — смена секретов и очистка истории.

## Лицензия

[MIT](LICENSE).

## Тесты (smoke)

```bash
pip install -e ".[dev]"
pytest
```
