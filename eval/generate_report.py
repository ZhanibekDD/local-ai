#!/usr/bin/env python3
"""Агрегация метрик из last_run.jsonl."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _pctl(vals: list[float], p: float) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


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
    valid_json_rate = statistics.mean(1.0 for r in vj if r.get("valid_json")) if vj else None
    ok_rate = statistics.mean(1.0 for r in rows if r.get("ok")) if rows else 0.0
    latencies = [float(r["latency_ms"]) for r in rows if "latency_ms" in r]
    avg_lat = statistics.mean(latencies) if latencies else 0.0
    fbs = [r for r in rows if "fallback" in r]
    fallback_rate = statistics.mean(1.0 for r in fbs if r.get("fallback")) if fbs else None

    by_suite: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_suite[r.get("suite", "default")].append(r)

    suite_stats = {}
    for name, sr in by_suite.items():
        lats = [float(x["latency_ms"]) for x in sr if "latency_ms" in x]
        suite_stats[name] = {
            "n": len(sr),
            "ok_rate": statistics.mean(1.0 for x in sr if x.get("ok")) if sr else 0.0,
            "latency_mean_ms": statistics.mean(lats) if lats else None,
        }

    rep = {
        "n": n,
        "ok_rate": ok_rate,
        "valid_json_rate": valid_json_rate,
        "average_latency_ms": avg_lat,
        "latency_p50_ms": statistics.median(latencies) if latencies else None,
        "latency_p95_ms": _pctl(latencies, 95),
        "fallback_rate": fallback_rate,
        "by_suite": suite_stats,
    }
    out = ROOT / "eval" / "reports" / "summary.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
