"""Валидация примера data/sft/custom.example.jsonl."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_custom_example_jsonl_passes_validator() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "training" / "validate_sft_jsonl.py"
    sample = root / "data" / "sft" / "custom.example.jsonl"
    r = subprocess.run(
        [sys.executable, str(script), str(sample)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout

