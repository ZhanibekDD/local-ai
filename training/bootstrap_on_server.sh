#!/usr/bin/env bash
# Запускать НА СЕРВЕРЕ (Ubuntu), уже после входа по SSH.
# Репозиторий: https://github.com/ZhanibekDD/local-ai — подставьте свой fork при необходимости.
set -euo pipefail

REPO_URL="${LOCAL_AI_REPO_URL:-https://github.com/ZhanibekDD/local-ai.git}"
TARGET="${LOCAL_AI_HOME:-$HOME/local-ai}"

if [[ ! -d "$TARGET/.git" ]]; then
  git clone "$REPO_URL" "$TARGET"
else
  git -C "$TARGET" pull --ff-only
fi

cd "$TARGET"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip wheel
pip install -e ".[train]"

echo "Готово: $TARGET"
echo "Активация: source $TARGET/.venv/bin/activate"
echo "Проверка JSONL: python training/validate_sft_jsonl.py data/sft/custom.example.jsonl"
echo "Выгрузка HF (нужен интернет): python training/sample_hf_dataset.py --dataset HuggingFaceH4/no_robots --split train -o data/sft/build/no_robots.jsonl"
