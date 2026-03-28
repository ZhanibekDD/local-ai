# Маршрутизация

## Где код

- `app/router/classifier.py` — функции `classify_text`, `classify_incoming`.
- `app/router/types.py` — `TaskType`, `RouteDecision` с полями `reason_codes` и `debug`.

## Правила (эвристика)

- Подсказки «верни JSON», «json schema» → **JSON** (`qwen-json` / structured).
- Признаки кода (блоки \`\`\`, `def`, SQL, `import`) → **code** (`deepseek-coder`).
- Слова про чек/накладную/PDF в тексте без файла → сообщение «пришлите фото/PDF» (отдельный ответ в `process_text_chat`).
- Загрузка **документа** в Telegram → **OCR + JSON** (чек по умолчанию: схема `ReceiptExtraction`).
- **Фото**: подпись с документными ключевыми словами → OCR; иначе → **vision**.

## Отладка

В ответе на текстовое сообщение внизу добавляется строка вида: `модель: …; маршрут: …` (краткое объяснение из `reason_codes`).
