#!/usr/bin/env python3
"""Запуск eval по JSONL кейсам (локальный Ollama)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.structured.output import generate_structured
from app.schemas.flexible import FlexibleExtraction
from app.bot.pipeline import process_text_chat


def load_cases(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(json.loads(line))
    return rows


def run_one(case: dict[str, Any], client: OllamaClient) -> dict[str, Any]:
    suite = case.get("suite", "")
    t0 = time.perf_counter()
    out: dict[str, Any] = {"case_id": case.get("id"), "suite": suite, "ok": False}

    if suite == "text_json_eval":
        models = client.list_models()
        m = pick_model(models, get_settings().model_qwen_chat, get_settings().model_qwen_fallback)
        obj, st, tries = generate_structured(client, m, case["input"], FlexibleExtraction)
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
        out["valid_json"] = obj is not None
        out["status"] = st
        out["tries"] = tries
        out["ok"] = obj is not None
        return out

    if suite == "text_support_eval":
        r = process_text_chat(case["input"], case.get("context", ""), show_reasoning=False)
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
        out["ok"] = not str(r.get("response", "")).startswith("Error")
        out["route"] = r.get("route")
        out["fallback"] = bool(r.get("fallback"))
        return out

    if suite == "code_eval":
        r = process_text_chat(case["input"], "", show_reasoning=False)
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
        out["ok"] = r.get("route") == "code" or "```" in str(r.get("response", ""))
        out["route"] = r.get("route")
        out["fallback"] = bool(r.get("fallback"))
        return out

    if suite == "vision_docs_eval":
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
        out["skipped"] = True
        out["note"] = "нужны бинарные фикстуры изображений; прогон вручную через бота"
        out["ok"] = True
        return out

    out["error"] = "unknown_suite"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, default=ROOT / "eval" / "data" / "cases.jsonl")
    ap.add_argument("--out", type=Path, default=ROOT / "eval" / "reports" / "last_run.jsonl")
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    client = OllamaClient()
    if not client.list_models():
        print("Ollama недоступен")
        sys.exit(1)
    results = []
    for case in load_cases(args.cases):
        results.append(run_one(case, client))
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results), encoding="utf-8")
    print("Записано:", args.out, "кейсов:", len(results))


if __name__ == "__main__":
    main()
