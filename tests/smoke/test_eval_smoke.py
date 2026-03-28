"""Eval: run_one для text_support_eval с подставным клиентом."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def run_eval_module():
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    path = root / "eval" / "run_eval.py"
    spec = importlib.util.spec_from_file_location("run_eval_smoke", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_run_one_text_support_mocked(run_eval_module, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = run_eval_module

    def fake_process(
        text: str,
        context: str,
        *,
        show_reasoning: bool = False,
    ) -> dict:
        return {"response": "ok", "route": "chat", "fallback": False}

    monkeypatch.setattr(mod, "process_text_chat", fake_process)
    client = MagicMock()
    client.list_models.return_value = ["dummy:latest"]
    case = {"id": "s1", "suite": "text_support_eval", "input": "ping", "context": ""}
    out = mod.run_one(case, client)
    assert out.get("ok") is True
    assert out.get("route") == "chat"
