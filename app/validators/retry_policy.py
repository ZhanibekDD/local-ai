"""Логирование ретраев и fallback для наблюдаемости."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def log_fallback(reason: str, *, detail: Optional[str] = None, extra: Optional[dict[str, Any]] = None) -> None:
    msg = "fallback: %s" % reason
    if detail:
        msg += " | %s" % detail
    if extra:
        msg += " | %s" % extra
    logger.warning(msg)


def log_structured_retry(attempt: int, error: str) -> None:
    logger.warning("structured retry attempt=%s err=%s", attempt, error[:200])
