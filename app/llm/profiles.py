"""Профили Qwen: chat, json, rag, judge — system + опции генерации."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class QwenProfile(str, Enum):
    CHAT = "qwen-chat"
    JSON = "qwen-json"
    RAG = "qwen-rag"
    JUDGE = "qwen-judge"


@dataclass
class ProfileConfig:
    system_prefix: str
    temperature: float
    num_predict: int
    format_json: bool


def profile_config(profile: QwenProfile) -> ProfileConfig:
    if profile == QwenProfile.CHAT:
        return ProfileConfig(
            system_prefix=(
                "Ты краткий русскоязычный ассистент. Отвечай по делу, без воды. "
                "Если фактов не хватает — так и скажи, не выдумывай.\n\n"
            ),
            temperature=0.55,
            num_predict=2048,
            format_json=False,
        )
    if profile == QwenProfile.JSON:
        return ProfileConfig(
            system_prefix=(
                "Ты извлекаешь структурированные данные. Ответ ТОЛЬКО валидный JSON по схеме. "
                "Без markdown, без ```, без пояснений до или после JSON. "
                "Неизвестные поля — null.\n\n"
            ),
            temperature=0.15,
            num_predict=4096,
            format_json=True,
        )
    if profile == QwenProfile.RAG:
        return ProfileConfig(
            system_prefix=(
                "Отвечай ТОЛЬКО на основе переданного контекста ниже. "
                "Если в контексте нет ответа — верни одну фразу: данных недостаточно. "
                "Не придумывай факты вне контекста.\n\n"
            ),
            temperature=0.3,
            num_predict=2048,
            format_json=False,
        )
    if profile == QwenProfile.JUDGE:
        return ProfileConfig(
            system_prefix=(
                "Ты внутренний проверяющий (не для пользователя). Оцени: полноту, формат, "
                "соответствие схеме, признаки галлюцинаций. Ответ — краткий JSON: "
                '{"ok":bool,"issues":[],"score":0-10}.\n\n'
            ),
            temperature=0.1,
            num_predict=1024,
            format_json=True,
        )
    raise ValueError(profile)


def wrap_prompt(profile: QwenProfile, user_prompt: str, rag_context: Optional[str] = None) -> str:
    cfg = profile_config(profile)
    parts = [cfg.system_prefix]
    if rag_context and profile == QwenProfile.RAG:
        parts.append("Контекст:\n" + rag_context.strip() + "\n\n")
    parts.append(user_prompt.strip())
    return "\n".join(parts)


def generation_options(cfg: ProfileConfig) -> dict[str, Any]:
    return {
        "temperature": cfg.temperature,
        "num_predict": cfg.num_predict,
    }
