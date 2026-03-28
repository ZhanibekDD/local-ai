"""Точка входа Telegram: handlers + Application."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.bot.pipeline import process_text_chat
from app.bot.reasoning import split_reasoning_response
from app.config.settings import get_settings
from app.llm.ollama_client import OllamaClient
from app.memory.context import format_chat_context
from app.memory.store import ChatManager, init_db
from app.ocr.pipeline import run_document_extraction
from app.router.classifier import classify_incoming
from app.router.types import TaskType
from app.schemas.receipt import ReceiptExtraction
from app.vision.service import VisionMode, vision_analyze

logger = logging.getLogger(__name__)


def _kb_main(user_id: int, cm: ChatManager) -> InlineKeyboardMarkup:
    rs = cm.get_show_reasoning(user_id)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💬 Задать вопрос", callback_data="help_ask"),
                InlineKeyboardButton("💻 Генерация кода", callback_data="help_code"),
            ],
            [
                InlineKeyboardButton("🖼️ Анализ изображения", callback_data="help_vision"),
                InlineKeyboardButton("📚 Список моделей", callback_data="models"),
            ],
            [
                InlineKeyboardButton("💾 Мои чаты", callback_data="my_chats"),
                InlineKeyboardButton("📊 Статус", callback_data="status"),
            ],
            [
                InlineKeyboardButton("➕ Новый чат", callback_data="new_chat"),
                InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
            ],
            [
                InlineKeyboardButton(
                    "🧠 Рассуждение: ВКЛ" if not rs else "🧠 Рассуждение: ВЫКЛ",
                    callback_data="toggle_reasoning",
                )
            ],
        ]
    )


async def send_text_chunks(update: Update, text: str, reply_markup=None) -> None:
    if not text:
        return
    limit = 4000
    msg = update.message or update.callback_query.message
    for i in range(0, len(text), limit):
        chunk = text[i : i + limit]
        rm = reply_markup if i + limit >= len(text) else None
        if update.message:
            await update.message.reply_text(chunk, reply_markup=rm)
        else:
            await msg.reply_text(chunk, reply_markup=rm)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    s = get_settings()
    cm = ChatManager(s.sqlite_path)
    cm.get_or_create_active_chat(update.effective_user.id)
    rs = cm.get_show_reasoning(update.effective_user.id)
    text = """🤖 AI Bot (локальный Ollama)

Добро пожаловать! Память диалогов, роутер моделей, OCR документов, vision.

• Текст → Qwen / DeepSeek (код)
• «Верни JSON» → structured output
• Фото/PDF чека → OCR + JSON
• Фото сцены → Llama Vision

Режим рассуждений: """ + (
        "ВКЛ" if rs else "ВЫКЛ"
    )
    await update.message.reply_text(text, reply_markup=_kb_main(update.effective_user.id, cm))


async def reason_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = ChatManager(get_settings().sqlite_path)
    uid = update.effective_user.id
    cm.set_show_reasoning(uid, not cm.get_show_reasoning(uid))
    nv = cm.get_show_reasoning(uid)
    await update.message.reply_text(
        "Режим рассуждений: "
        + ("ВКЛ — РАССУЖДЕНИЕ / ОТВЕТ" if nv else "ВЫКЛ — обычный ответ")
    )


async def my_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cm = ChatManager(get_settings().sqlite_path)
    uid = update.effective_user.id
    chats = cm.get_user_chats(uid)
    if not chats:
        await update.message.reply_text(
            "У вас пока нет чатов",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]),
        )
        return
    kb = [[InlineKeyboardButton(f"💬 {t}", callback_data=f"chat_{cid}")] for cid, t, _ in chats]
    kb.append([InlineKeyboardButton("➕ Новый чат", callback_data="new_chat")])
    kb.append([InlineKeyboardButton("🏠 Меню", callback_data="start")])
    await update.message.reply_text("💾 Ваши чаты:", reply_markup=InlineKeyboardMarkup(kb))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text or ""
    uid = update.effective_user.id
    s = get_settings()
    cm = ChatManager(s.sqlite_path)
    show_rs = cm.get_show_reasoning(uid)
    status_msg = await update.message.reply_text(
        "🧠 Рассуждение + ответ…" if show_rs else "🤔 Обрабатываю…"
    )
    chat_id = cm.get_or_create_active_chat(uid)
    messages = cm.get_chat_messages(chat_id)
    conv = format_chat_context(messages)

    result = await asyncio.to_thread(
        process_text_chat,
        user_message,
        conv,
        show_reasoning=show_rs,
    )
    response = result.get("response", "")
    model = result.get("model", "")
    explain = result.get("explain", "")

    cm.add_message(chat_id, "user", user_message)
    cm.add_message(chat_id, "assistant", response)

    if len(messages) == 0:
        title = user_message[:50] + "…" if len(user_message) > 50 else user_message
        cm.update_chat_title(chat_id, title)

    await status_msg.delete()

    meta = f"\n\n—\nмодель: {model}; маршрут: {explain}"
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💾 Мои чаты", callback_data="my_chats")],
            [InlineKeyboardButton("🏠 Меню", callback_data="start")],
        ]
    )

    if show_rs and result.get("route") == "chat":
        if "РАССУЖДЕНИЕ" in response or "ОТВЕТ" in response:
            reasoning_part, answer_part = split_reasoning_response(response)
            if reasoning_part and answer_part:
                await send_text_chunks(update, "🧠 Рассуждение:\n\n" + reasoning_part + meta)
                await send_text_chunks(update, "✅ Ответ:\n\n" + answer_part, reply_markup)
                return
            if reasoning_part and not answer_part:
                await send_text_chunks(update, "🧠 Рассуждение:\n\n" + reasoning_part + meta, reply_markup)
                return
        await send_text_chunks(
            update,
            "⚠️ Маркеры РАССУЖДЕНИЕ/ОТВЕТ не найдены.\n\n" + response + meta,
            reply_markup,
        )
        return

    await send_text_chunks(update, response + meta, reply_markup)


async def _download_tg_file(context: ContextTypes.DEFAULT_TYPE, file_id: str) -> bytes:
    tg_file = await context.bot.get_file(file_id)
    return bytes(await tg_file.download_as_bytearray())


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    s = get_settings()
    cm = ChatManager(s.sqlite_path)
    caption = update.message.caption or ""
    status = await update.message.reply_text("🖼 Анализ изображения…")
    photo = update.message.photo[-1]
    data = await _download_tg_file(context, photo.file_id)
    decision = classify_incoming(
        text=caption,
        has_photo=True,
        has_document=False,
        mime="image/jpeg",
    )
    client = OllamaClient()
    try:
        if decision.task == TaskType.DOCUMENT_OCR:
            res = await asyncio.to_thread(
                run_document_extraction,
                client,
                data,
                "image.jpg",
                ReceiptExtraction,
                caption,
            )
            text_out = (
                f"OCR trace: {res.engine_trace}\n\n"
                + (res.raw_text[:2000] if res.structured is None else res.structured.model_dump_json(indent=2))
            )
        else:
            text_out = await asyncio.to_thread(
                vision_analyze,
                client,
                data,
                VisionMode.BASE,
            )
    finally:
        await status.delete()

    chat_id = cm.get_or_create_active_chat(uid)
    cm.add_message(chat_id, "user", f"[фото] {caption}")
    cm.add_message(chat_id, "assistant", text_out)
    await update.message.reply_text(text_out[:4000])


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    s = get_settings()
    cm = ChatManager(s.sqlite_path)
    doc = update.message.document
    if not doc:
        return
    status = await update.message.reply_text("📄 Документ: извлечение…")
    fname = doc.file_name or "file.bin"
    data = await _download_tg_file(context, doc.file_id)
    client = OllamaClient()
    res = await asyncio.to_thread(
        run_document_extraction,
        client,
        data,
        fname,
        ReceiptExtraction,
        "",
    )
    await status.delete()
    out = (
        res.structured.model_dump_json(indent=2)
        if res.structured
        else f"Не удалось структурировать.\nRaw:\n{res.raw_text[:3500]}\n\n{res.status}"
    )
    chat_id = cm.get_or_create_active_chat(uid)
    cm.add_message(chat_id, "user", f"[документ {fname}]")
    cm.add_message(chat_id, "assistant", out)
    await update.message.reply_text(out[:4000])


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    s = get_settings()
    cm = ChatManager(s.sqlite_path)

    if query.data == "new_chat":
        cm.create_new_chat(uid, "Новый чат")
        await query.edit_message_text(
            "➕ Новый чат создан.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]),
        )
    elif query.data == "my_chats":
        chats = cm.get_user_chats(uid)
        if not chats:
            await query.edit_message_text("Нет чатов", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]))
            return
        kb = [[InlineKeyboardButton(f"💬 {t}", callback_data=f"chat_{cid}")] for cid, t, _ in chats]
        kb.append([InlineKeyboardButton("🏠 Меню", callback_data="start")])
        await query.edit_message_text("Ваши чаты:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data.startswith("chat_"):
        cid = int(query.data.split("_")[1])
        cm.switch_chat(uid, cid)
        msgs = cm.get_chat_messages(cid, limit=5)
        prev = "\n".join(f"{'U' if r=='user' else 'A'}: {c[:80]}" for r, c in msgs[-3:])
        await query.edit_message_text(f"✅ Чат активен.\n\n{prev}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]))
    elif query.data == "start":
        rs = cm.get_show_reasoning(uid)
        await query.edit_message_text(
            "🤖 Меню. Рассуждения: " + ("ВКЛ" if rs else "ВЫКЛ"),
            reply_markup=_kb_main(uid, cm),
        )
    elif query.data == "toggle_reasoning":
        cm.set_show_reasoning(uid, not cm.get_show_reasoning(uid))
        await query.edit_message_text(
            "Режим: " + ("ВКЛ" if cm.get_show_reasoning(uid) else "ВЫКЛ"),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]),
        )
    elif query.data == "models":
        client = OllamaClient()
        models = await asyncio.to_thread(client.list_models)
        await query.edit_message_text("Модели:\n" + "\n".join(f"• {m}" for m in models)[:4000])
    elif query.data == "status":
        client = OllamaClient()
        ok = await asyncio.to_thread(lambda: bool(client.list_models()))
        await query.edit_message_text("Ollama: " + ("OK" if ok else "недоступен"))
    else:
        await query.edit_message_text("Раздел в разработке.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="start")]]))


def main() -> None:
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
    s = get_settings()
    token = s.telegram_bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token.strip():
        print("Задайте TELEGRAM_BOT_TOKEN в .env или переменной окружения.")
        return

    init_db(s.sqlite_path)
    print("Ollama:", s.ollama_base_url)
    client = OllamaClient()
    if not client.list_models():
        print("Ollama недоступен или нет моделей. Проверьте туннель SSH.")
        return

    app = Application.builder().token(token.strip()).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chats", my_chats_command))
    app.add_handler(CommandHandler("reason", reason_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Бот запущен. SQLite:", s.sqlite_path)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
