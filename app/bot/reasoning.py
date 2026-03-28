"""Режим рассуждения: инструкция и разбор ответа."""

from __future__ import annotations

import re

REASONING_INSTRUCTION = """

ОБЯЗАТЕЛЬНО: первые символы ответа — это строка «РАССУЖДЕНИЕ:» (без приветствий и без преамбулы).

Шаблон (строго так):

РАССУЖДЕНИЕ:
- Шаг 1: что за вопрос и что нужно выяснить
- Шаг 2: какие факты/формулы применимы
- Шаг 3: вывод
(3–7 коротких пунктов на русском)

ОТВЕТ:
(только готовый ответ пользователю, без повторения шагов)

Если нужен только JSON — в ОТВЕТ один JSON; в РАССУЖДЕНИЕ кратко почему так."""


def split_reasoning_response(text: str) -> tuple[str | None, str]:
    t = text.strip()
    if not t:
        return None, text

    m_r = re.search(r"(?is)РАССУЖДЕНИЕ\s*:", t)
    m_a = re.search(r"(?is)ОТВЕТ\s*:", t)
    if m_r and m_a and m_a.start() > m_r.end():
        reasoning = t[m_r.end() : m_a.start()].strip()
        answer = t[m_a.end() :].strip()
        if reasoning and answer:
            return reasoning, answer

    m_r2 = re.search(r"(?is)REASONING\s*:", t)
    m_a2 = re.search(r"(?is)ANSWER\s*:", t)
    if m_r2 and m_a2 and m_a2.start() > m_r2.end():
        reasoning = t[m_r2.end() : m_a2.start()].strip()
        answer = t[m_a2.end() :].strip()
        if reasoning and answer:
            return reasoning, answer

    r_markers = ("РАССУЖДЕНИЕ:", "РАССУЖДЕНИЕ")
    a_markers = ("ОТВЕТ:", "ОТВЕТ", "Ответ:", "ответ:")
    idx_r = -1
    r_len = 0
    tl = t
    for m in r_markers:
        i = tl.find(m)
        if i != -1 and (idx_r == -1 or i < idx_r):
            idx_r = i
            r_len = len(m)
    if idx_r == -1:
        return None, text
    rest = tl[idx_r + r_len :]
    idx_a = -1
    a_len = 0
    for m in a_markers:
        i = rest.find(m)
        if i != -1 and (idx_a == -1 or i < idx_a):
            idx_a = i
            a_len = len(m)
    if idx_a == -1:
        return rest.strip(), ""
    reasoning = rest[:idx_a].strip()
    answer = rest[idx_a + a_len :].strip()
    if not answer and reasoning:
        return None, text
    return reasoning, answer
