# Быстрый старт

1. Python 3.10+.
2. Установка зависимостей (единый способ, см. `pyproject.toml`):

```bash
pip install -e .
```

Опционально: инструменты разработки и SSH-скрипты (`paramiko`):

```bash
pip install -e ".[dev,ssh]"
```

3. Скопируйте `.env.example` в `.env` и задайте `TELEGRAM_BOT_TOKEN`. При необходимости — `OLLAMA_BASE_URL` (по умолчанию `http://localhost:11434`). Для внешнего OCR-сервиса — `OCR_REMOTE_URL` (например `http://localhost:8081/ocr/extract`); пустое значение отключает remote.
4. Убедитесь, что Ollama доступен (например SSH-туннель на порт 11434).
5. Запуск Telegram-бота из корня проекта:

```bash
python telegram-bot-advanced.py
```

Нужны переменные `TELEGRAM_BOT_TOKEN` и доступный Ollama (`OLLAMA_BASE_URL`, по умолчанию `http://localhost:11434`).

6. Опционально — локальный HTTP для проверки (health и список моделей через Ollama):

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8080
```

Откройте `http://127.0.0.1:8080/health` и `http://127.0.0.1:8080/v1/models`.

7. Eval (при работающем Ollama):

```bash
python eval/run_eval.py
python eval/generate_report.py
```

8. Профили Ollama: см. `modelfiles/*.Modelfile` — при желании `ollama create …` и имена в `.env`.
