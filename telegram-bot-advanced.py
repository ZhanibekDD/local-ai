#!/usr/bin/env python3
"""
Telegram-бот: точка входа. Логика в пакете app/ (router, OCR, vision, structured output).
Переменные: см. .env.example (TELEGRAM_BOT_TOKEN, OLLAMA_BASE_URL).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.bot.telegram_app import main

if __name__ == "__main__":
    main()
