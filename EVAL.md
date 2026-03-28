# Оценка качества (eval)

## Файлы

- `eval/data/cases.jsonl` — кейсы (одна строка = один JSON-объект).
- Поля: `id`, `suite`, `input`, опционально `context`.

Поддерживаемые `suite`:

- `text_support_eval` — обычный диалог через `process_text_chat`.
- `text_json_eval` — structured output (`FlexibleExtraction`).
- `code_eval` — проверка маршрута/ответа с кодом.
- `vision_docs_eval` — заглушка (нужны бинарные фикстуры; основной прогон документов — через бота).

## Запуск

```bash
python eval/run_eval.py --cases eval/data/cases.jsonl --out eval/reports/last_run.jsonl
python eval/generate_report.py --run eval/reports/last_run.jsonl
python eval/compare_outputs.py eval/reports/run_a.jsonl eval/reports/run_b.jsonl
```

Метрики в `eval/reports/summary.json`: `ok_rate`, `valid_json_rate` (если есть поля), `average_latency_ms`.
