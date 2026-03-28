#!/usr/bin/env python3
"""
Telegram бот для AI моделей Dell R760
Работает локально, подключается к Ollama через SSH туннель
"""

import logging
import os
import requests
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
OLLAMA_API = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").strip()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OllamaAPI:
    def __init__(self, base_url=OLLAMA_API):
        self.base_url = base_url
    
    def generate(self, model, prompt):
        try:
            # Используем модель напрямую без дополнительных промптов
            # если это qwen-pro (уже содержит system prompt)
            if "qwen-pro" in model or "coder-ru" in model or "vision-ru" in model:
                full_prompt = prompt
            else:
                full_prompt = f"Ты AI ассистент. Отвечай ТОЛЬКО на русском языке.\n\n{prompt}\n\nОтвет:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048
                    }
                },
                timeout=300
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_with_image(self, model, prompt, image_data):
        try:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            full_prompt = f"Ты AI ассистент для анализа изображений. Отвечай ТОЛЬКО на русском языке. Опиши изображение подробно на русском.\n\n{prompt}\n\nОтвет на русском:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "images": [image_base64],
                    "stream": False,
                    "options": {
                        "temperature": 0.7
                    }
                },
                timeout=300
            )
            if response.status_code == 200:
                return response.json().get('response', '')
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_models(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return [m['name'] for m in response.json().get('models', [])]
            return []
        except:
            return []

ollama = OllamaAPI()

# Хранилище истории диалогов для каждого пользователя
user_conversations = {}

def get_conversation_history(user_id, max_messages=10):
    """Получить историю диалога пользователя"""
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id][-max_messages:]

def add_to_conversation(user_id, role, content):
    """Добавить сообщение в историю"""
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": role, "content": content})
    # Ограничиваем историю 20 сообщениями
    if len(user_conversations[user_id]) > 20:
        user_conversations[user_id] = user_conversations[user_id][-20:]

def clear_conversation(user_id):
    """Очистить историю диалога"""
    if user_id in user_conversations:
        user_conversations[user_id] = []

def format_conversation_context(user_id):
    """Форматировать историю для промпта"""
    history = get_conversation_history(user_id)
    if not history:
        return ""
    
    context = "\n\nПредыдущий контекст диалога:\n"
    for msg in history:
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        context += f"{role}: {msg['content']}\n"
    return context

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для очистки истории диалога"""
    user_id = update.effective_user.id
    clear_conversation(user_id)
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🗑️ История диалога очищена!\n\nТеперь начнем новый разговор с чистого листа.",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        models = ollama.list_models()
        text = f"""📊 Статус сервера Dell R760

🖥️ Сервер: Dell R760
🎮 GPU: NVIDIA A40 48GB
💾 Хранилище: RAID 0 NVMe (1.8TB)
🌐 Подключение: SSH туннель

📚 Загружено моделей: {len(models)}
✓ Ollama API: Работает
✓ SSH туннель: Активен

Модели:"""
        for model in models:
            text += f"\n  • {model}"
    except Exception as e:
        text = f"❌ Ошибка подключения к серверу\n\n{str(e)}"
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "start":
        keyboard = [
            [
                InlineKeyboardButton("💬 Задать вопрос", callback_data="help_ask"),
                InlineKeyboardButton("💻 Генерация кода", callback_data="help_code")
            ],
            [
                InlineKeyboardButton("🖼️ Анализ изображения", callback_data="help_vision"),
                InlineKeyboardButton("📚 Список моделей", callback_data="models")
            ],
            [
                InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton("📊 Статус сервера", callback_data="status")
            ],
            [
                InlineKeyboardButton("🗑️ Новый чат", callback_data="clear")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """🤖 AI Bot Dell R760 + NVIDIA A40

Добро пожаловать! Я AI ассистент на базе мощного сервера Dell R760 с NVIDIA A40 48GB.

Что я умею:
• Отвечать на вопросы (Qwen2.5 72B)
• Генерировать код (DeepSeek Coder 33B)
• Анализировать изображения (Llama Vision 90B)
• Помнить контекст диалога

Просто напишите сообщение или выберите действие:"""
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "help":
        keyboard = [
            [
                InlineKeyboardButton("💬 Задать вопрос", callback_data="help_ask"),
                InlineKeyboardButton("💻 Код", callback_data="help_code")
            ],
            [
                InlineKeyboardButton("🖼️ Изображение", callback_data="help_vision"),
                InlineKeyboardButton("📚 Модели", callback_data="models")
            ],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """📖 Помощь по использованию бота

🗣️ Текстовые запросы:
• Просто напишите сообщение
• /ask <вопрос> - задать вопрос
• Модель: Qwen2.5 72B (русский язык)

💻 Генерация кода:
• /code <задача> - генерация кода
• Модель: DeepSeek Coder 33B

🖼️ Анализ изображений:
• Отправьте фото с подписью
• Модель: Llama Vision 90B

📊 Другие команды:
• /models - список моделей
• /status - статус сервера

🖥️ Сервер: Dell R760 + NVIDIA A40 48GB"""
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "help_ask":
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """💬 Как задать вопрос:

Способ 1: Просто напишите сообщение
  Привет! Расскажи о квантовых компьютерах

Способ 2: Используйте команду /ask
  /ask Что такое машинное обучение?

Модель: Qwen2.5 72B
Язык: Русский, English
Контекст: До 128K токенов"""
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "help_code":
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """💻 Генерация кода:

Использование:
  /code <описание задачи>

Примеры:
  /code Напиши функцию факториала на Python
  /code Создай REST API на FastAPI
  /code Сортировка массива на C++

Модель: DeepSeek Coder 33B
Языки: Python, JavaScript, C++, Java, Go и др."""
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "help_vision":
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """🖼️ Анализ изображений:

Как использовать:
1. Отправьте фото
2. Добавьте подпись с вопросом (опционально)

Примеры подписей:
• Что на этом изображении?
• Опиши детали
• Прочитай текст с фото
• Что это за объект?

Модель: Llama Vision 90B
Поддержка: JPG, PNG, WebP"""
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "models":
        models = ollama.list_models()
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if models:
            text = "📚 Доступные модели на сервере:\n\n"
            for model in models:
                text += f"✓ {model}\n"
            text += f"\nВсего моделей: {len(models)}"
        else:
            text = "❌ Модели не найдены"
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "status":
        try:
            models = ollama.list_models()
            text = f"""📊 Статус сервера Dell R760

🖥️ Сервер: Dell R760
🎮 GPU: NVIDIA A40 48GB
💾 Хранилище: RAID 0 NVMe (1.8TB)
🌐 Подключение: SSH туннель

📚 Загружено моделей: {len(models)}
✓ Ollama API: Работает
✓ SSH туннель: Активен

Модели:"""
            for model in models:
                text += f"\n  • {model}"
        except Exception as e:
            text = f"❌ Ошибка подключения к серверу\n\n{str(e)}"
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "clear":
        user_id = query.from_user.id
        clear_conversation(user_id)
        
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ История диалога очищена!\n\nТеперь начнем новый разговор с чистого листа.",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💬 Задать вопрос", callback_data="help_ask"),
            InlineKeyboardButton("💻 Генерация кода", callback_data="help_code")
        ],
        [
            InlineKeyboardButton("🖼️ Анализ изображения", callback_data="help_vision"),
            InlineKeyboardButton("📚 Список моделей", callback_data="models")
        ],
        [
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton("📊 Статус сервера", callback_data="status")
        ],
        [
            InlineKeyboardButton("🗑️ Новый чат", callback_data="clear")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """🤖 AI Bot Dell R760 + NVIDIA A40

Добро пожаловать! Я AI ассистент на базе мощного сервера Dell R760 с NVIDIA A40 48GB.

Что я умею:
• Отвечать на вопросы (Qwen2.5 72B)
• Генерировать код (DeepSeek Coder 33B)
• Анализировать изображения (Llama Vision 90B)
• Помнить контекст диалога

Просто напишите сообщение или выберите действие:"""
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("💬 Задать вопрос", callback_data="help_ask"),
            InlineKeyboardButton("💻 Код", callback_data="help_code")
        ],
        [
            InlineKeyboardButton("🖼️ Изображение", callback_data="help_vision"),
            InlineKeyboardButton("📚 Модели", callback_data="models")
        ],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """📖 Помощь по использованию бота

🗣️ Текстовые запросы:
• Просто напишите сообщение
• /ask <вопрос> - задать вопрос
• Модель: Qwen2.5 72B (русский язык)

💻 Генерация кода:
• /code <задача> - генерация кода
• Модель: DeepSeek Coder 33B

🖼️ Анализ изображений:
• Отправьте фото с подписью
• Модель: Llama Vision 90B

📊 Другие команды:
• /models - список моделей
• /status - статус сервера

🖥️ Сервер: Dell R760 + NVIDIA A40 48GB"""
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    models = ollama.list_models()
    if models:
        text = "📚 Доступные модели на сервере:\n\n"
        for model in models:
            text += f"✓ {model}\n"
        text += f"\nВсего моделей: {len(models)}"
    else:
        text = "❌ Модели не найдены"
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💬 Использование: /ask <ваш вопрос>\n\nПример:\n/ask Что такое квантовая физика?",
            reply_markup=reply_markup
        )
        return
    
    question = ' '.join(context.args)
    user_id = update.effective_user.id
    
    status_msg = await update.message.reply_text("🤔 Думаю над вопросом...")
    
    # Приоритет: qwen-pro > qwen-ru > qwen2.5:72b
    models = ollama.list_models()
    if "qwen-pro" in models:
        model = "qwen-pro"
    elif "qwen-ru" in models:
        model = "qwen-ru"
    else:
        model = "qwen2.5:72b"
    
    # Добавляем контекст
    conversation_context = format_conversation_context(user_id)
    full_prompt = f"{conversation_context}\n\nПользователь: {question}\n\nОтвет:"
    
    response = ollama.generate(model, full_prompt)
    
    # Сохраняем в историю
    add_to_conversation(user_id, "user", question)
    add_to_conversation(user_id, "assistant", response)
    
    await status_msg.delete()
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            if i == 0:
                await update.message.reply_text(response[i:i+4000], reply_markup=reply_markup)
            else:
                await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response, reply_markup=reply_markup)

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💻 Использование: /code <задача>\n\nПример:\n/code Напиши функцию сортировки пузырьком на Python",
            reply_markup=reply_markup
        )
        return
    
    task = ' '.join(context.args)
    models = ollama.list_models()
    
    # Используем оптимизированную модель если доступна
    if "coder-ru" in models:
        model = "coder-ru"
        model_name = "DeepSeek Coder (RU)"
    elif "deepseek-coder:33b" in models:
        model = "deepseek-coder:33b"
        model_name = "DeepSeek Coder 33B"
    else:
        model = "qwen-ru" if "qwen-ru" in models else "qwen2.5:72b"
        model_name = "Qwen2.5 72B"
    
    status_msg = await update.message.reply_text(f"💻 Генерирую код ({model_name})...")
    
    prompt = f"Ты опытный программист. Напиши код для задачи. Все комментарии и объяснения ТОЛЬКО на русском языке.\n\nЗадача: {task}\n\nКод с комментариями на русском:"
    response = ollama.generate(model, prompt)
    
    await status_msg.delete()
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            if i == 0:
                await update.message.reply_text(response[i:i+4000], reply_markup=reply_markup)
            else:
                await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    status_msg = await update.message.reply_text("🤔 Обрабатываю запрос...")
    
    # Приоритет: qwen-pro > qwen-ru > qwen2.5:72b
    models = ollama.list_models()
    if "qwen-pro" in models:
        model = "qwen-pro"
    elif "qwen-ru" in models:
        model = "qwen-ru"
    else:
        model = "qwen2.5:72b"
    
    # Добавляем контекст предыдущих сообщений
    conversation_context = format_conversation_context(user_id)
    full_prompt = f"{conversation_context}\n\nПользователь: {user_message}\n\nОтвет:"
    
    response = ollama.generate(model, full_prompt)
    
    # Сохраняем в историю
    add_to_conversation(user_id, "user", user_message)
    add_to_conversation(user_id, "assistant", response)
    
    await status_msg.delete()
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            if i == 0:
                await update.message.reply_text(response[i:i+4000], reply_markup=reply_markup)
            else:
                await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models = ollama.list_models()
    
    # Используем оптимизированную модель если доступна
    if "vision-ru" in models:
        model = "vision-ru"
        model_name = "Llama Vision (RU)"
    elif "llama3.2-vision:90b" in models:
        model = "llama3.2-vision:90b"
        model_name = "Llama Vision 90B"
    elif "llava:34b" in models:
        model = "llava:34b"
        model_name = "LLaVA 34B"
    else:
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ Vision модель не установлена\n\nДоступные модели: /models",
            reply_markup=reply_markup
        )
        return
    
    status_msg = await update.message.reply_text(f"🖼️ Анализирую изображение ({model_name})...")
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_data = await file.download_as_bytearray()
    caption = update.message.caption or "Опиши детально что на этом изображении"
    
    response = ollama.generate_with_image(model, caption, bytes(image_data))
    
    await status_msg.delete()
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            if i == 0:
                await update.message.reply_text(response[i:i+4000], reply_markup=reply_markup)
            else:
                await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response, reply_markup=reply_markup)

def main():
    print("=" * 70)
    print("  TELEGRAM BOT - Dell R760 AI Server")
    print("=" * 70)
    print(f"\nOllama API: {OLLAMA_API}")
    print("Проверка подключения к Ollama...")
    
    try:
        response = requests.get(f"{OLLAMA_API}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"[OK] Ollama доступен! Найдено моделей: {len(models)}")
            for model in models:
                print(f"  • {model['name']}")
        else:
            print("[ERROR] Ollama не отвечает")
            print("\nУбедитесь что SSH туннель запущен:")
            print("  ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST")
            return
    except Exception as e:
        print(f"[ERROR] Ошибка подключения к Ollama: {e}")
        print("\nЗапустите SSH туннель:")
        print("  ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST")
        return
    
    print("\n[START] Запуск Telegram бота...")
    if not TELEGRAM_TOKEN:
        print("[ERROR] Задайте переменную окружения TELEGRAM_BOT_TOKEN")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("models", models_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("code", code_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("[OK] Бот запущен и готов к работе!")
    print("\nОткройте Telegram и найдите вашего бота")
    print("Отправьте /start для начала работы\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[STOP] Бот остановлен")
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
