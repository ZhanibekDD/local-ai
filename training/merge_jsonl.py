#!/usr/bin/env python3
"""Объединение нескольких JSONL в один файл; опционально shuffle."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Слияние JSONL без парсинга (построчно).")
    ap.add_argument("inputs", nargs="+", type=Path, help="Входные .jsonl")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Выходной файл")
    ap.add_argument("--seed", type=int, default=None, help="Seed для shuffle (после merge)")
    args = ap.parse_args()
    lines: list[str] = []
    for p in args.inputs:
        if not p.is_file():
            print("Нет файла:", p, file=sys.stderr)
            sys.exit(2)
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    if args.seed is not None:
        rng = random.Random(args.seed)
        rng.shuffle(lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print("Строк:", len(lines), "->", args.output)


if __name__ == "__main__":
    main()
