#!/usr/bin/env python3
"""
Клиент для работы с Ollama API на сервере Dell R760
"""

import os
import requests
import json
import base64
import sys
from pathlib import Path

# Конфигурация (по умолчанию локальный туннель/OLLAMA)
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

class OllamaClient:
    def __init__(self, base_url=OLLAMA_URL):
        self.base_url = base_url
        
    def list_models(self):
        """Список доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"\n[*] Доступные модели ({len(models)}):")
                for model in models:
                    name = model.get('name', 'unknown')
                    size = model.get('size', 0) / (1024**3)  # В GB
                    print(f"  - {name} ({size:.1f} GB)")
                return models
            else:
                print(f"[-] Ошибка: {response.status_code}")
                return []
        except Exception as e:
            print(f"[-] Ошибка подключения: {e}")
            return []
    
    def generate(self, model, prompt, stream=False, options=None):
        """Генерация текста"""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        if options:
            data["options"] = options
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                stream=stream
            )
            
            if stream:
                # Потоковый вывод
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            print(chunk['response'], end='', flush=True)
                print()  # Новая строка в конце
            else:
                # Одним блоком
                result = response.json()
                return result.get('response', '')
                
        except Exception as e:
            print(f"[-] Ошибка: {e}")
            return None
    
    def generate_with_image(self, model, prompt, image_path):
        """Генерация с изображением (vision модели)"""
        # Чтение и кодирование изображения
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"[-] Ошибка чтения изображения: {e}")
            return None
        
        data = {
            "model": model,
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data
            )
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            print(f"[-] Ошибка: {e}")
            return None
    
    def chat(self, model, messages):
        """Чат с контекстом"""
        data = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=data
            )
            result = response.json()
            return result.get('message', {}).get('content', '')
        except Exception as e:
            print(f"[-] Ошибка: {e}")
            return None

def main():
    """Примеры использования"""
    client = OllamaClient()
    
    print("="*70)
    print("  OLLAMA CLIENT - Dell R760")
    print("="*70)
    
    # Список моделей
    models = client.list_models()
    
    if not models:
        print("\n[-] Не удалось подключиться к серверу")
        print(f"[*] Проверьте что сервер доступен: {OLLAMA_URL}")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("  ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ")
    print("="*70)
    
    # Пример 1: Простой запрос
    print("\n[1] Простой текстовый запрос:")
    print("-" * 70)
    prompt = "Напиши функцию на Python для вычисления чисел Фибоначчи"
    print(f"Запрос: {prompt}\n")
    
    response = client.generate("qwen2.5:72b", prompt)
    if response:
        print(f"Ответ:\n{response}\n")
    
    # Пример 2: С параметрами
    print("\n[2] Запрос с параметрами:")
    print("-" * 70)
    prompt = "Объясни что такое нейронные сети простыми словами"
    print(f"Запрос: {prompt}\n")
    
    options = {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 500
    }
    
    response = client.generate("qwen2.5:72b", prompt, options=options)
    if response:
        print(f"Ответ:\n{response}\n")
    
    # Пример 3: Чат с контекстом
    print("\n[3] Чат с контекстом:")
    print("-" * 70)
    
    messages = [
        {"role": "user", "content": "Привет! Как тебя зовут?"},
        {"role": "assistant", "content": "Привет! Я AI ассистент на базе Qwen2.5."},
        {"role": "user", "content": "Напиши функцию сортировки пузырьком на Python"}
    ]
    
    print("Диалог:")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")
    print()
    
    response = client.chat("qwen2.5:72b", messages)
    if response:
        print(f"Ответ:\n{response}\n")
    
    print("\n" + "="*70)
    print("  ГОТОВО!")
    print("="*70)
    print(f"\n[*] API доступен: {OLLAMA_URL}")
    print("[*] Документация: https://github.com/ollama/ollama/blob/main/docs/api.md")

if __name__ == "__main__":
    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        client = OllamaClient()
        
        if sys.argv[1] == "list":
            # Список моделей
            client.list_models()
            
        elif sys.argv[1] == "ask" and len(sys.argv) > 3:
            # Быстрый запрос: python ollama-client.py ask "qwen2.5:72b" "Привет!"
            model = sys.argv[2]
            prompt = sys.argv[3]
            print(f"\n[*] Запрос к {model}...")
            response = client.generate(model, prompt)
            if response:
                print(f"\n{response}\n")
                
        elif sys.argv[1] == "vision" and len(sys.argv) > 4:
            # Vision запрос: python ollama-client.py vision "llama3.2-vision:90b" "Опиши изображение" image.jpg
            model = sys.argv[2]
            prompt = sys.argv[3]
            image_path = sys.argv[4]
            print(f"\n[*] Vision запрос к {model}...")
            response = client.generate_with_image(model, prompt, image_path)
            if response:
                print(f"\n{response}\n")
                
        else:
            print("Использование:")
            print("  python ollama-client.py list")
            print('  python ollama-client.py ask "qwen2.5:72b" "Ваш вопрос"')
            print('  python ollama-client.py vision "llama3.2-vision:90b" "Опиши" image.jpg')
    else:
        # Запуск примеров
        main()
