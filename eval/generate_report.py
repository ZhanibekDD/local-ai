#!/usr/bin/env python3
"""Агрегация метрик из last_run.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=ROOT / "eval" / "reports" / "last_run.jsonl")
    args = ap.parse_args()
    if not args.run.exists():
        print("Нет файла прогона:", args.run)
        sys.exit(1)
    rows = [json.loads(l) for l in args.run.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = len(rows)
    vj = [r for r in rows if "valid_json" in r]
    valid_json_rate = mean(1.0 for r in vj if r.get("valid_json")) if vj else None
    ok_rate = mean(1.0 for r in rows if r.get("ok")) if rows else 0.0
    latencies = [r["latency_ms"] for r in rows if "latency_ms" in r]
    avg_lat = mean(latencies) if latencies else 0.0
    fbs = [r for r in rows if "fallback" in r]
    fallback_rate = mean(1.0 for r in fbs if r.get("fallback")) if fbs else None
    rep = {
        "n": n,
        "ok_rate": ok_rate,
        "valid_json_rate": valid_json_rate,
        "average_latency_ms": avg_lat,
        "fallback_rate": fallback_rate,
    }
    out = ROOT / "eval" / "reports" / "summary.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
