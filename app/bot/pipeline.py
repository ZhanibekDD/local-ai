"""Оркестрация: router → LLM / OCR / vision."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient, pick_model
from app.llm.profiles import QwenProfile, profile_config, wrap_prompt
from app.router.classifier import classify_incoming
from app.router.types import TaskType
from app.schemas.flexible import FlexibleExtraction
from app.structured.output import generate_structured

logger = logging.getLogger(__name__)


def _qwen_pref(models: list[str]) -> str:
    s = get_settings()
    return pick_model(models, s.model_qwen_chat, s.model_qwen_fallback, "qwen2.5:72b")


def _code_pref(models: list[str]) -> str:
    s = get_settings()
    return pick_model(models, s.model_code, "deepseek-coder")


def process_text_chat(
    user_message: str,
    conversation_context: str,
    *,
    show_reasoning: bool,
) -> dict[str, Any]:
    client = OllamaClient()
    models = client.list_models()
    decision = classify_incoming(
        text=user_message,
        has_photo=False,
        has_document=False,
        mime=None,
    )
    s = get_settings()
    out: dict[str, Any] = {
        "route": decision.task.value,
        "explain": decision.explain(),
        "debug": decision.debug,
        "model": "",
        "response": "",
        "fallback": False,
    }

    # Неясный тип → чат
    if decision.task == TaskType.UNKNOWN:
        decision.task = TaskType.CHAT
        out["fallback"] = True

    if decision.task == TaskType.CODE:
        model = _code_pref(models)
        out["model"] = model
        prompt = f"{conversation_context}\n\nПользователь: {user_message}\n\nОтвет (код/технически точно):"
        cfg = profile_config(QwenProfile.CHAT)
        ok, text = client.generate(
            model,
            prompt,
            options={"temperature": s.temperature_code, "num_predict": 4096},
        )
        out["response"] = text if ok else f"Ошибка: {text}"
        return out

    if decision.task == TaskType.DOCUMENT_OCR:
        model = _qwen_pref(models)
        out["model"] = model
        out["response"] = (
            "Для извлечения реквизитов из чека/накладной пришлите фото или PDF файлом. "
            "Один документ — одно сообщение."
        )
        out["fallback"] = True
        return out

    if decision.task == TaskType.JSON_EXTRACTION:
        model = _qwen_pref(models)
        out["model"] = model
        hint = f"{conversation_context}\n\nЗапрос пользователя:\n{user_message}"
        obj, st, tries = generate_structured(client, model, hint, FlexibleExtraction)
        out["debug"]["structured_tries"] = tries
        if obj is not None:
            out["response"] = json.dumps(obj.model_dump(), ensure_ascii=False, indent=2)
        else:
            out["response"] = f"Не удалось получить валидный JSON: {st}. Пробую обычный ответ."
            out["fallback"] = True
            model2 = _qwen_pref(models)
            p2 = wrap_prompt(QwenProfile.CHAT, f"{conversation_context}\n\nПользователь: {user_message}")
            cfg = profile_config(QwenProfile.CHAT)
            ok, text = client.generate(
                model2,
                p2,
                options={"temperature": s.temperature_chat, "num_predict": s.num_predict_chat},
            )
            out["response"] = text if ok else out["response"]
        return out

    # CHAT (по умолчанию)
    model = _qwen_pref(models)
    out["model"] = model
    if show_reasoning:
        from app.bot.reasoning import REASONING_INSTRUCTION

        full_prompt = f"{conversation_context}\n\nПользователь: {user_message}{REASONING_INSTRUCTION}"
        ok, text = client.generate(
            model,
            full_prompt,
            options={
                "temperature": 0.45,
                "num_predict": s.num_predict_reasoning,
            },
        )
    else:
        p = wrap_prompt(
            QwenProfile.CHAT,
            f"{conversation_context}\n\nПользователь: {user_message}\n\nОтвет:",
        )
        ok, text = client.generate(
            model,
            p,
            options={"temperature": s.temperature_chat, "num_predict": s.num_predict_chat},
        )
    out["response"] = text if ok else f"Ошибка: {text}"
    return out
