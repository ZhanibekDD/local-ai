"""Внутренняя оценка ответа (профиль qwen-judge)."""

from __future__ import annotations

import json
from typing import Any, Optional

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.llm.profiles import QwenProfile, profile_config, wrap_prompt


def judge_response(
    client: OllamaClient,
    user_task: str,
    model_answer: str,
    schema_hint: str = "",
) -> Optional[dict[str, Any]]:
    s = get_settings()
    models = client.list_models()
    m = pick_model(models, s.model_qwen_chat, s.model_qwen_fallback)
    cfg = profile_config(QwenProfile.JUDGE)
    prompt = wrap_prompt(
        QwenProfile.JUDGE,
        f"Задача:\n{user_task}\n\nОтвет модели:\n{model_answer}\n\nСхема/ожидание:\n{schema_hint}",
    )
    ok, text = client.generate(
        m,
        prompt,
        format_json=True,
        options={"temperature": cfg.temperature, "num_predict": cfg.num_predict},
    )
    if not ok:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"parse_error": True, "raw": text[:500]}
