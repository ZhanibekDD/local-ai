# Модели

Настройки по умолчанию задаются в `app/config/settings.py` и переопределяются через `.env`.

| Назначение | Поле настроек | Пример имени в Ollama |
|------------|---------------|------------------------|
| Основной чат | `model_qwen_chat` | `qwen-pro` |
| Запасной текст | `model_qwen_fallback` | `qwen2.5:72b` |
| Код | `model_code` | `deepseek-coder:33b` |
| Vision | `model_vision` | `llama3.2-vision:90b` |

Имена вида `qwen-pro:latest` поддерживаются: `pick_model` ищет совпадение по префиксу.

## Профили Modelfile

В каталоге `modelfiles/` лежат черновики:

- `qwen-chat.Modelfile` — обычный диалог.
- `qwen-json.Modelfile` — уклон в строгий JSON.
- `qwen-rag.Modelfile` — ответ только по контексту.
- `qwen-judge.Modelfile` — внутренняя оценка.

Создание в Ollama: `ollama create qwen-chat -f modelfiles/qwen-chat.Modelfile`.

В Python профили дублируются через `app/llm/profiles.py` (system + temperature + `format=json` для JSON/judge).
