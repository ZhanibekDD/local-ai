# Маршрутизация

## Код

- `app/router/scoring.py` — взвешенные шаблоны, суммарные score по `TaskType`, `margin` между 1-м и 2-м местом.
- `app/router/classifier.py` — `classify_incoming` (текст / фото / документ); опционально LLM-уточнение.
- `app/router/llm_disambiguate.py` — короткий Qwen-json при `ROUTER_LLM_DISAMBIGUATE=true` и низком `margin`.
- `app/router/types.py` — `TaskType`, `RouteDecision`; в `debug` попадают `scores`, `margin`, флаг `llm_override`.

## Поведение

1. Текст: скоринг по JSON / код / документ «без файла» / базовый чат.
2. Если включено LLM-уточнение и `margin < ROUTER_AMBIGUOUS_MARGIN` — один вызов с классификацией `chat|json|code|doc_hint` (при `confidence >= ROUTER_LLM_MIN_CONFIDENCE`).
3. Документ в Telegram → OCR-пайплайн.
4. Фото + «документная» подпись → OCR; иначе vision.

## Подсказка пользователю

В текстовом ответе бота внизу: `модель: …; маршрут: …`.
