#!/usr/bin/env python3
"""Проверка/нормализация DPO jsonl (prompt, chosen, rejected)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out_lines = []
    for line in args.inp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        for k in ("prompt", "chosen", "rejected"):
            if k not in row:
                raise SystemExit(f"нет поля {k}")
        out_lines.append(json.dumps(row, ensure_ascii=False))
    args.out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("OK:", args.out)


if __name__ == "__main__":
    main()
