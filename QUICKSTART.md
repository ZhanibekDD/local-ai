# Быстрый старт

1. Python 3.10+.
2. Установка зависимостей:

```bash
pip install -r requirements-app.txt
```

3. Скопируйте `.env.example` в `.env` и задайте `TELEGRAM_BOT_TOKEN`. При необходимости — `OLLAMA_BASE_URL` (по умолчанию `http://localhost:11434`).
4. Убедитесь, что Ollama доступен (например SSH-туннель на порт 11434).
5. Запуск бота из корня проекта:

```bash
python telegram-bot-advanced.py
```

6. Опционально: создать профили Ollama из `modelfiles/*.Modelfile` и при желании сменить имена моделей в настройках.
