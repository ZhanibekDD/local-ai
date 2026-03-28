#!/usr/bin/env python3
"""
Telegram бот для работы с AI моделями на Dell R760
Token: <YOUR_BOT_TOKEN>
"""

import logging
import requests
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Конфигурация
TELEGRAM_TOKEN = "<YOUR_BOT_TOKEN>"
OLLAMA_API = "http://localhost:11434"  # Локальный API на сервере

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OllamaAPI:
    """Класс для работы с Ollama API"""
    
    def __init__(self, base_url=OLLAMA_API):
        self.base_url = base_url
    
    def generate(self, model, prompt, stream=False):
        """Генерация текста"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream
                },
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Ошибка API: {response.status_code}"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def generate_with_image(self, model, prompt, image_data):
        """Генерация с изображением"""
        try:
            # Кодируем изображение в base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False
                },
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Ошибка API: {response.status_code}"
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def list_models(self):
        """Список доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except:
            return []

# Инициализация API
ollama = OllamaAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = """
🤖 Привет! Я AI бот на базе Dell R760 с NVIDIA A40!

📚 Доступные команды:

/ask <вопрос> - Задать вопрос (Qwen2.5 72B)
/code <задача> - Генерация кода (DeepSeek Coder)
/vision <описание> - Анализ изображения (отправьте фото)
/models - Список доступных моделей
/help - Помощь

💡 Просто отправьте текст для общения с Qwen2.5 72B
📷 Отправьте фото с подписью для анализа изображения

Powered by Dell R760 + NVIDIA A40 48GB
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🤖 Помощь по использованию бота

📝 Текстовые запросы:
• Просто напишите вопрос
• /ask Объясни квантовую физику
• /code Напиши функцию сортировки на Python

📷 Работа с изображениями:
• Отправьте фото с подписью
• /vision Опиши что на фото

🔧 Технические команды:
• /models - Список моделей
• /start - Начать заново

⚡ Модели на сервере:
• Qwen2.5 72B - универсальная, русский язык
• DeepSeek Coder 33B - программирование
• Llama Vision 90B - анализ изображений

🖥️ Сервер: Dell R760 + NVIDIA A40 48GB
"""
    await update.message.reply_text(help_text)

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /models"""
    await update.message.reply_text("🔍 Проверяю доступные модели...")
    
    models = ollama.list_models()
    
    if models:
        text = "📚 Доступные модели:\n\n"
        for model in models:
            text += f"• {model}\n"
        text += f"\n✅ Всего моделей: {len(models)}"
    else:
        text = "❌ Не удалось получить список моделей"
    
    await update.message.reply_text(text)

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ask"""
    if not context.args:
        await update.message.reply_text("❌ Использование: /ask <ваш вопрос>")
        return
    
    question = ' '.join(context.args)
    await update.message.reply_text(f"🤔 Думаю над вопросом...\n\n❓ {question}")
    
    response = ollama.generate("qwen2.5:72b", question)
    
    # Разбиваем длинные ответы
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /code"""
    if not context.args:
        await update.message.reply_text("❌ Использование: /code <задача программирования>")
        return
    
    task = ' '.join(context.args)
    await update.message.reply_text(f"💻 Генерирую код...\n\n📝 Задача: {task}")
    
    # Используем DeepSeek Coder если доступен, иначе Qwen
    models = ollama.list_models()
    model = "deepseek-coder:33b" if "deepseek-coder:33b" in models else "qwen2.5:72b"
    
    prompt = f"Напиши код для следующей задачи: {task}\n\nОтветь только кодом с комментариями."
    response = ollama.generate(model, prompt)
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text
    
    await update.message.reply_text("🤔 Думаю...")
    
    response = ollama.generate("qwen2.5:72b", user_message)
    
    # Разбиваем длинные ответы
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фотографий"""
    await update.message.reply_text("📷 Анализирую изображение...")
    
    # Получаем фото
    photo = update.message.photo[-1]  # Берем самое большое разрешение
    file = await context.bot.get_file(photo.file_id)
    
    # Скачиваем фото
    image_data = await file.download_as_bytearray()
    
    # Получаем подпись или используем стандартный запрос
    caption = update.message.caption or "Опиши детально что на этом изображении"
    
    # Проверяем доступность vision модели
    models = ollama.list_models()
    
    if "llama3.2-vision:90b" in models:
        model = "llama3.2-vision:90b"
    elif "llava:34b" in models:
        model = "llava:34b"
    elif "llava:13b" in models:
        model = "llava:13b"
    else:
        await update.message.reply_text("❌ Vision модель не установлена. Используйте /models для проверки.")
        return
    
    response = ollama.generate_with_image(model, caption, bytes(image_data))
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        await update.message.reply_text(response)

async def vision_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /vision"""
    await update.message.reply_text(
        "📷 Отправьте изображение с подписью для анализа.\n\n"
        "Пример: Отправьте фото с текстом 'Опиши что на изображении'"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса.\n"
            "Попробуйте еще раз или используйте /help"
        )

def main():
    """Запуск бота"""
    print("="*70)
    print("  TELEGRAM BOT - Dell R760 AI Server")
    print("="*70)
    print(f"\nOllama API: {OLLAMA_API}")
    print("Проверка подключения к Ollama...")
    
    # Проверка подключения
    try:
        response = requests.get(f"{OLLAMA_API}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama доступен! Найдено моделей: {len(models)}")
            for model in models:
                print(f"  • {model['name']}")
        else:
            print("❌ Ollama не отвечает")
            print("Убедитесь что Ollama запущен: systemctl status ollama")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        print("\nПроверьте:")
        print("1. Ollama запущен: systemctl status ollama")
        print("2. API доступен: curl http://localhost:11434/api/tags")
        return
    
    print("\n🚀 Запуск Telegram бота...")
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("models", models_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("code", code_command))
    application.add_handler(CommandHandler("vision", vision_command))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("✅ Бот запущен и готов к работе!")
    print("\nОткройте Telegram и найдите вашего бота")
    print("Отправьте /start для начала работы\n")
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
