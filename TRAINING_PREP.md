# Подготовка к SFT / DPO

## Каталоги

- `data/sft/` — пары/диалоги для дообучения.
- `data/dpo/` — предпочтения (chosen / rejected).
- `data/sft/template.jsonl`, `data/dpo/template.jsonl` — формат примеров.

## Скрипты

- `scripts/prepare_sft_dataset.py` — нормализация JSONL.
- `scripts/prepare_dpo_dataset.py` — проверка полей `prompt`, `chosen`, `rejected`.
- `scripts/validate_dataset.py` — базовая проверка файла.

## Рекомендации (когда будете учить)

- Сначала отдельно собирайте данные под **qwen-chat** и **qwen-json**; не смешивайте «свободный диалог» и «только JSON» в одном батче без явной метки.
- LoRA/QLoRA: используйте стек вроде `axolotl` / `llama-factory` / `unsloth` на той же машине с A40; тяжёлый запуск не автоматизирован в этом репозитории.
