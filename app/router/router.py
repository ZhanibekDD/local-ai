"""Фасад маршрутизатора: explain + решение."""

from __future__ import annotations

from app.router.classifier import classify_incoming
from app.router.types import RouteDecision

route = classify_incoming

__all__ = ["route", "RouteDecision"]
