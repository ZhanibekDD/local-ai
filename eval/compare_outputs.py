#!/usr/bin/env python3
"""Сравнение двух прогонов eval (JSONL): считает дельту ok_rate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_run(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    args = ap.parse_args()
    ra, rb = load_run(args.a), load_run(args.b)
    oka = sum(1 for r in ra if r.get("ok")) / max(len(ra), 1)
    okb = sum(1 for r in rb if r.get("ok")) / max(len(rb), 1)
    print(json.dumps({"ok_rate_a": oka, "ok_rate_b": okb, "delta": okb - oka}, indent=2))


if __name__ == "__main__":
    main()
