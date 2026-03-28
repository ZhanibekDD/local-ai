#!/usr/bin/env python3
"""
Выгрузка сэмпла из Hugging Face в единый JSONL с полем messages.

Требует: pip install "datasets" (см. pyproject optional train).

Примеры:
  python training/sample_hf_dataset.py --dataset HuggingFaceH4/no_robots --split train \\
    -o data/sft/build/no_robots.jsonl

  python training/sample_hf_dataset.py --dataset HuggingFaceTB/OpenHermes-2.5-H4 \\
    --split train_sft --max-samples 30000 --seed 42 \\
    -o data/sft/build/openhermes_30k.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any


def _messages_from_row(row: dict[str, Any]) -> list[dict[str, str]] | None:
    if "messages" in row and isinstance(row["messages"], list):
        return row["messages"]  # type: ignore[return-value]
    if "conversations" in row and isinstance(row["conversations"], list):
        # иногда sharegpt-стиль
        out: list[dict[str, str]] = []
        for turn in row["conversations"]:
            if not isinstance(turn, dict):
                continue
            h = turn.get("from") or turn.get("role")
            val = turn.get("value") or turn.get("content")
            if h in ("human", "user") and val:
                out.append({"role": "user", "content": str(val)})
            elif h in ("gpt", "assistant", "model") and val:
                out.append({"role": "assistant", "content": str(val)})
        return out if out else None
    p = row.get("prompt") or row.get("instruction") or row.get("question")
    c = row.get("completion") or row.get("response") or row.get("answer")
    if isinstance(p, str) and isinstance(c, str) and p.strip() and c.strip():
        return [{"role": "user", "content": p.strip()}, {"role": "assistant", "content": c.strip()}]
    return None


def main() -> None:
    try:
        from datasets import load_dataset  # type: ignore[import-untyped]
    except ImportError:
        print("Установите зависимость: pip install datasets", file=sys.stderr)
        sys.exit(2)

    ap = argparse.ArgumentParser(description="Сэмпл HF-датасета → JSONL (messages).")
    ap.add_argument("--dataset", required=True, help="Имя на HF, напр. HuggingFaceH4/no_robots")
    ap.add_argument(
        "--config",
        default=None,
        help="Подмножество (subset) датасета, если в карточке несколько configs; иначе не указывать",
    )
    ap.add_argument("--split", default="train", help="Сплит: train, train_sft и т.д. (см. карточку на HF)")
    ap.add_argument("--max-samples", type=int, default=None, help="Максимум строк (после shuffle индексов)")
    ap.add_argument("--seed", type=int, default=42, help="Seed для случайного сэмпла")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Выходной .jsonl")
    args = ap.parse_args()

    if args.config:
        ds = load_dataset(args.dataset, args.config, split=args.split, trust_remote_code=True)
    else:
        ds = load_dataset(args.dataset, split=args.split, trust_remote_code=True)
    n = len(ds)
    indices = list(range(n))
    if args.max_samples is not None and args.max_samples < n:
        rng = random.Random(args.seed)
        indices = rng.sample(indices, args.max_samples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.output.open("w", encoding="utf-8") as f:
        for i in indices:
            row = ds[i]
            msgs = _messages_from_row(row)
            if not msgs:
                continue
            rec: dict[str, Any] = {"messages": msgs}
            if isinstance(row.get("system"), str):
                rec["system"] = row["system"]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    print("Записано строк:", written, "из отобранных индексов:", len(indices), "dataset len:", n)


if __name__ == "__main__":
    main()
