"""Простые проверки полей (после извлечения)."""

from __future__ import annotations

import re
from typing import Optional

_PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{10,}$")


def normalize_phone(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = re.sub(r"\s+", "", s.strip())
    return t if _PHONE_RE.match(s.strip()) else None


def parse_amount(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"(\d+[\.,]?\d*)", s.replace(" ", ""))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None
