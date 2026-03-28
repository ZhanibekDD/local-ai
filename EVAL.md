# Оценка качества (eval)

## Файлы

- `eval/data/cases.jsonl` — кейсы (одна строка = JSON).
- Поля: `id`, `suite`, `input`, опционально `context`, для `vision_docs_eval`: `fixture_path`, `fixture_name`, `extra_hint`.

## Suites

- `text_support_eval` — `process_text_chat` (маршрут, fallback).
- `text_json_eval` — `FlexibleExtraction` + valid_json.
- `code_eval` — маршрут code или ответ с кодом.
- `vision_docs_eval` — если задан существующий `fixture_path`, прогоняется OCR+extract; иначе кейс помечается `skipped` с пояснением.

## Запуск

```bash
python eval/run_eval.py --cases eval/data/cases.jsonl --out eval/reports/last_run.jsonl
python eval/generate_report.py --run eval/reports/last_run.jsonl
python eval/compare_outputs.py eval/reports/run_a.jsonl eval/reports/run_b.jsonl
```

## Метрики (`summary.json`)

- `ok_rate`, `valid_json_rate`, `fallback_rate`
- `average_latency_ms`, `latency_p50_ms`, `latency_p95_ms`
- `by_suite` — разбивка по `suite`

`compare_outputs.py` возвращает сводки по обоим прогонам и дельты `ok_rate` и средней задержки.

Это **каркас для регрессий**, а не полный бенчмарк качества: для «галлюцинаций» и точности полей нужны отдельные эталоны и ручная разметка.
