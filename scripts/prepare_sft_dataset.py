#!/usr/bin/env python3
"""Конвертация простого JSONL (system/user/assistant) в train jsonl."""

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
        out_lines.append(
            json.dumps(
                {
                    "system": row.get("system", ""),
                    "messages": row.get("messages", []),
                },
                ensure_ascii=False,
            )
        )
    args.out.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("OK:", args.out)


if __name__ == "__main__":
    main()
