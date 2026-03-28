#!/usr/bin/env python3
"""Базовая валидация JSONL датасета (SFT или DPO)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--mode", choices=("sft", "dpo"), default="sft")
    args = ap.parse_args()
    n = 0
    for line in args.file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        n += 1
        if args.mode == "dpo":
            assert "prompt" in row and "chosen" in row and "rejected" in row
        else:
            assert "messages" in row or "system" in row
    print("строк:", n, "OK")


if __name__ == "__main__":
    main()
