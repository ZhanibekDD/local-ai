#!/usr/bin/env python3
"""Проверка JSONL для SFT: одна запись = messages с user + assistant."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_record(obj: dict, line_no: int) -> list[str]:
    errs: list[str] = []
    messages = obj.get("messages")
    if not isinstance(messages, list) or not messages:
        errs.append(f"строка {line_no}: нет непустого поля messages")
        return errs
    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if "user" not in roles:
        errs.append(f"строка {line_no}: в messages нет role=user")
    if "assistant" not in roles:
        errs.append(f"строка {line_no}: в messages нет role=assistant")
    for i, m in enumerate(messages):
        if not isinstance(m, dict):
            errs.append(f"строка {line_no}: messages[{i}] не объект")
            continue
        if "content" not in m or not isinstance(m.get("content"), str):
            errs.append(f"строка {line_no}: messages[{i}] без строкового content")
    if "system" in obj and not isinstance(obj["system"], str):
        errs.append(f"строка {line_no}: system должен быть строкой")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser(description="Валидация SFT JSONL (messages + user/assistant).")
    ap.add_argument("path", type=Path, help="Путь к .jsonl")
    args = ap.parse_args()
    if not args.path.is_file():
        print("Файл не найден:", args.path, file=sys.stderr)
        sys.exit(2)
    all_errs: list[str] = []
    n = 0
    for line_no, line in enumerate(args.path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        n += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            all_errs.append(f"строка {line_no}: JSON: {e}")
            continue
        if not isinstance(obj, dict):
            all_errs.append(f"строка {line_no}: корень не объект")
            continue
        all_errs.extend(validate_record(obj, line_no))
    if all_errs:
        for e in all_errs:
            print(e, file=sys.stderr)
        print(f"Ошибок: {len(all_errs)} (просмотрено записей: {n})", file=sys.stderr)
        sys.exit(1)
    print("OK, записей:", n)


if __name__ == "__main__":
    main()
