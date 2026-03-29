"""Централизованные настройки: env + defaults."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_CANDIDATE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_CANDIDATE) if _ENV_CANDIDATE.is_file() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")

    sqlite_path: Path = Field(default_factory=lambda: _REPO_ROOT / "bot_chats.db", alias="SQLITE_PATH")

    # Имена моделей (без :tag — подставится первая подходящая из ollama list)
    model_qwen_chat: str = "qwen-pro"
    model_qwen_fallback: str = "qwen2.5:72b"
    model_code: str = "deepseek-coder:33b"
    model_vision: str = "llama3.2-vision:90b"

    temperature_chat: float = 0.55
    temperature_json: float = 0.2
    temperature_code: float = 0.25
    num_ctx_default: int = 8192
    num_predict_chat: int = 2048
    num_predict_json: int = 4096
    num_predict_reasoning: int = 4096

    max_history_messages: int = 20
    max_context_chars: int = 12000

    retry_max: int = 2
    retry_backoff_sec: float = 0.5

    ocr_lang: str = "rus+eng"
    ocr_remote_url: str = Field(
        default="http://localhost:8081/ocr/extract",
        alias="OCR_REMOTE_URL",
        description="По умолчанию локальный туннель; пустая строка в env отключает remote OCR.",
    )
    ocr_engine: str = Field(
        default="auto",
        alias="OCR_ENGINE",
        description="auto: текст PDF → при необходимости OCR; pymupdf: только текст слоя; tesseract: растр+Tesseract; paddle: PaddleOCR если установлен, иначе как auto",
    )

    router_llm_disambiguate: bool = Field(
        default=False,
        alias="ROUTER_LLM_DISAMBIGUATE",
        description="Если True и margin низкий — уточнить маршрут коротким вызовом Qwen-json",
    )
    router_ambiguous_margin: float = Field(default=0.15, alias="ROUTER_AMBIGUOUS_MARGIN")
    router_llm_min_confidence: float = Field(default=0.55, alias="ROUTER_LLM_MIN_CONFIDENCE")

    eval_data_dir: Path = Field(default=Path("eval/data"))
    eval_report_dir: Path = Field(default=Path("eval/reports"))


def get_settings() -> Settings:
    return Settings()
