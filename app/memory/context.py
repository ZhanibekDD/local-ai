"""Сборка контекста диалога с лимитами."""

from __future__ import annotations

from typing import List, Tuple

from app.config.settings import get_settings


def format_chat_context(messages: List[Tuple[str, str]]) -> str:
    s = get_settings()
    if not messages:
        return ""
    # берём последние N сообщений
    tail = messages[-s.max_history_messages :]
    lines = ["Предыдущий контекст диалога:"]
    total = 0
    for role, content in tail:
        role_name = "Пользователь" if role == "user" else "Ассистент"
        piece = f"{role_name}: {content}\n"
        if total + len(piece) > s.max_context_chars:
            lines.append("… (обрезано по лимиту контекста)")
            break
        lines.append(piece.strip())
        total += len(piece)
    return "\n".join(lines) + "\n"
