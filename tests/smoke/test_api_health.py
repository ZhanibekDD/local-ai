"""HTTP-слой: /health без живого Ollama."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
