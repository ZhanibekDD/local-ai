#!/usr/bin/env python3
"""Сравнение двух прогонов eval (JSONL): ok_rate, valid_json, fallback, latency."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

def load_run(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _mean(vals: list[float]) -> float | None:
    return statistics.mean(vals) if vals else None


def _summarize(rows: list[dict]) -> dict:
    n = len(rows)
    ok_rate = sum(1 for r in rows if r.get("ok")) / max(n, 1)
    vj = [r for r in rows if "valid_json" in r]
    valid_json_rate = sum(1 for r in vj if r.get("valid_json")) / max(len(vj), 1) if vj else None
    fb = [r for r in rows if "fallback" in r]
    fallback_rate = sum(1 for r in fb if r.get("fallback")) / max(len(fb), 1) if fb else None
    lat = [float(r["latency_ms"]) for r in rows if r.get("latency_ms") is not None]
    return {
        "n": n,
        "ok_rate": ok_rate,
        "valid_json_rate": valid_json_rate,
        "fallback_rate": fallback_rate,
        "latency_mean_ms": _mean(lat),
        "latency_p50_ms": statistics.median(lat) if lat else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    args = ap.parse_args()
    ra, rb = load_run(args.a), load_run(args.b)
    sa, sb = _summarize(ra), _summarize(rb)
    out = {
        "run_a": sa,
        "run_b": sb,
        "delta": {
            "ok_rate": (sb["ok_rate"] or 0) - (sa["ok_rate"] or 0),
            "latency_mean_ms": (sb["latency_mean_ms"] or 0) - (sa["latency_mean_ms"] or 0)
            if sa.get("latency_mean_ms") is not None
            else None,
        },
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
