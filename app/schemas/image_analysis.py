"""Краткий анализ изображения (vision)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ImageAnalysisSummary(BaseModel):
    description: str = ""
    scene_type: Optional[str] = None  # ui_screenshot|photo|document_scan|other
    objects: list[str] = Field(default_factory=list)
    text_visible: Optional[str] = None
