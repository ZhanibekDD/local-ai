# Сделай сам: сервер + данные SFT

Всё ниже выполняешь **ты** по SSH на своей машине (Ubuntu). Подставь свои `хост`, `порт`, `пользователя` — **не** вставляй пароли в скрипты и не коммить их.

## 1. Подключение

```bash
ssh -p <ПОРТ> <ПОЛЬЗОВАТЕЛЬ>@<ХОСТ>
```

## 2. Код репозитория

Если репо ещё нет:

```bash
cd ~
git clone https://github.com/ZhanibekDD/local-ai.git
cd local-ai
git pull
```

Если уже клонировал — зайди в каталог и `git pull`.

## 3. Окружение Python и зависимости для данных

```bash
cd ~/local-ai   # или твой путь
bash training/bootstrap_on_server.sh
```

Либо вручную:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e ".[train]"
```

## 4. Проверка, что формат данных ок

```bash
source .venv/bin/activate
python training/validate_sft_jsonl.py data/sft/custom.example.jsonl
```

Должно быть: `OK, записей: 5`.

## 5. Выгрузка публичных датасетов (нужен интернет на сервере)

```bash
mkdir -p data/sft/build

python training/sample_hf_dataset.py \
  --dataset HuggingFaceH4/no_robots \
  --split train \
  -o data/sft/build/no_robots.jsonl

python training/sample_hf_dataset.py \
  --dataset HuggingFaceTB/OpenHermes-2.5-H4 \
  --split train_sft \
  --max-samples 30000 \
  --seed 42 \
  -o data/sft/build/openhermes_30k.jsonl
```

Если `load_dataset` ругается на сплит — открой карточку датасета на Hugging Face и поправь `--split` или добавь `--config …`.

## 6. Свой слой + склейка

1. Положи свой файл, например `data/sft/my_custom.jsonl` (тот же формат, что `custom.example.jsonl`).
2. Слей всё в один файл для тренера:

```bash
python training/merge_jsonl.py \
  data/sft/build/no_robots.jsonl \
  data/sft/build/openhermes_30k.jsonl \
  data/sft/my_custom.jsonl \
  -o data/sft/build/merged_sft.jsonl \
  --seed 42
```

3. При желании проверь целиком:

```bash
python training/validate_sft_jsonl.py data/sft/build/merged_sft.jsonl
```

Каталог `data/sft/build/` в `.gitignore` — большие файлы в git не коммить.

## 7. Обучение (не в этом репо)

Дальше на **GPU-машине** ставишь отдельно **LLaMA-Factory** или **TRL**, указываешь базовую модель `Qwen/Qwen2.5-14B-Instruct` и путь к `merged_sft.jsonl`. Детали смотри в официальных гайдах Qwen / выбранного тренера — версии пакетов меняются.

## 8. Полезные ссылки

- Стратегия первого цикла: [FINETUNING.md](FINETUNING.md)
- Формат строк: [../data/sft/README.md](../data/sft/README.md)
