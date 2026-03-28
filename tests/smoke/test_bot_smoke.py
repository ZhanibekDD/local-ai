"""Точка входа бота: ранний выход без токена, без polling."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_main_exits_when_no_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from app.bot import telegram_app as ta

    def fake_settings() -> SimpleNamespace:
        return SimpleNamespace(
            telegram_bot_token="",
            ollama_base_url="http://127.0.0.1:11434",
            sqlite_path=tmp_path / "bot.db",
        )

    monkeypatch.setattr(ta, "get_settings", fake_settings)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    ta.main()


def test_telegram_app_importable() -> None:
    from app.bot import telegram_app

    assert callable(telegram_app.main)
