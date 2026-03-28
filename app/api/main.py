"""Локальный HTTP-слой: health и список моделей Ollama (без облака)."""

from __future__ import annotations

from fastapi import FastAPI

from app.llm.ollama_client import OllamaClient

app = FastAPI(title="local-ai", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    c = OllamaClient()
    names = c.list_models()
    return {"models": [{"name": n} for n in names], "ollama_reachable": bool(names)}
