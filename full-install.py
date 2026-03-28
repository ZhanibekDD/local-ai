#!/usr/bin/env python3
"""
Полная установка AI моделей на Dell R760
Внешний IP: YOUR_PUBLIC_HOST:42
"""

import paramiko
import time
import sys

EXTERNAL_IP = "YOUR_PUBLIC_HOST"
SSH_PORT = 42
USERNAME = "dnepr"
PASSWORD = "REDACTED"

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(msg):
    print(f"{Colors.GREEN}[+] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}[*] {msg}{Colors.END}")

def print_warn(msg):
    print(f"{Colors.YELLOW}[!] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}[-] {msg}{Colors.END}")

def main():
    print("="*70)
    print("  УСТАНОВКА AI НА DELL R760")
    print("="*70)
    print(f"\nСервер: {EXTERNAL_IP}:{SSH_PORT}")
    print(f"Пользователь: {USERNAME}\n")
    
    # Подключение
    print_info("Подключение к серверу...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            EXTERNAL_IP,
            port=SSH_PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=30
        )
        print_step("Подключение успешно!\n")
    except Exception as e:
        print_error(f"Ошибка подключения: {e}")
        return False
    
    def run(cmd, desc="", timeout=300, show_output=True):
        """Выполнение команды"""
        if desc:
            print_info(desc)
        
        # Для sudo команд используем echo password
        if cmd.strip().startswith('sudo'):
            cmd = f"echo '{PASSWORD}' | sudo -S {cmd[5:]}"
        
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
        
        output = ""
        for line in stdout:
            output += line
            if show_output:
                print(line, end='')
        
        return output
    
    # Проверка системы
    print("\n" + "="*70)
    print("ПРОВЕРКА СИСТЕМЫ")
    print("="*70 + "\n")
    
    run("hostname && uname -a", "Информация о системе")
    run("free -h | grep Mem", "Память")
    run("df -h / | tail -1", "Диск")
    
    # Проверка GPU
    output = run("nvidia-smi 2>/dev/null || echo 'NOT_INSTALLED'", "GPU", show_output=False)
    
    if "NVIDIA" in output:
        print_step("NVIDIA драйверы установлены")
        print(output)
        gpu_ok = True
    else:
        print_warn("NVIDIA драйверы НЕ установлены")
        gpu_ok = False
    
    # Проверка Ollama
    output = run("ollama --version 2>/dev/null || echo 'NOT_INSTALLED'", "Ollama", show_output=False)
    
    if "ollama version" in output.lower():
        print_step("Ollama установлен")
        print(output)
        run("ollama list", "Список моделей")
        ollama_ok = True
    else:
        print_warn("Ollama НЕ установлен")
        ollama_ok = False
    
    # Установка
    print("\n" + "="*70)
    print("УСТАНОВКА КОМПОНЕНТОВ")
    print("="*70 + "\n")
    
    # Обновление системы
    if not gpu_ok or not ollama_ok:
        print_info("Обновление системы...")
        run("sudo apt update", "Обновление списка пакетов", timeout=120)
    
    # Ollama
    if not ollama_ok:
        print_info("Установка Ollama (это займет 1-2 минуты)...")
        run("curl -fsSL https://ollama.com/install.sh | sh", "Установка Ollama", timeout=300)
        
        print_info("Настройка Ollama...")
        run("sudo mkdir -p /etc/systemd/system/ollama.service.d", "Создание директории")
        run("echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf", "Конфиг 1")
        run("echo 'Environment=\"OLLAMA_HOST=0.0.0.0:11434\"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf", "Конфиг 2")
        run("echo 'Environment=\"OLLAMA_ORIGINS=*\"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf", "Конфиг 3")
        run("sudo systemctl daemon-reload", "Перезагрузка systemd")
        run("sudo systemctl restart ollama", "Перезапуск Ollama")
        run("sudo systemctl enable ollama", "Автозапуск Ollama")
        
        time.sleep(3)
        run("systemctl status ollama --no-pager -l", "Статус Ollama")
        print_step("Ollama установлен и запущен!")
    
    # NVIDIA драйверы
    if not gpu_ok:
        print_info("Установка NVIDIA драйверов (это займет 5-10 минут)...")
        run("sudo apt install -y nvidia-driver-535 nvidia-utils-535", 
            "Установка драйверов", timeout=600)
        
        print_warn("\nТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА!")
        print("Выполните на сервере: sudo reboot")
        print("Затем запустите этот скрипт снова для загрузки моделей")
        client.close()
        return False
    
    # Файрвол
    print_info("Настройка файрвола...")
    run("sudo apt install -y ufw", "Установка UFW", timeout=60)
    run("sudo ufw allow 22/tcp", "SSH")
    run("sudo ufw allow 11434/tcp", "Ollama API")
    run("sudo ufw --force enable", "Включение UFW")
    run("sudo ufw status", "Статус")
    
    # Загрузка моделей
    print("\n" + "="*70)
    print("ЗАГРУЗКА AI МОДЕЛЕЙ")
    print("="*70)
    print_warn("\nВНИМАНИЕ: Загрузка займет 30-60 минут!")
    print_warn("Модели очень большие (115GB общий размер)\n")
    
    response = input("Начать загрузку моделей? (y/n): ")
    
    if response.lower() != 'y':
        print_info("\nЗагрузка пропущена. Для загрузки позже:")
        print("  ssh -p 42 user@YOUR_PUBLIC_HOST")
        print("  ollama pull qwen2.5:72b")
        print("  ollama pull llama3.2-vision:90b")
        client.close()
        return True
    
    # Текущие модели
    run("ollama list", "Текущие модели")
    
    # Qwen2.5 72B
    print("\n" + "-"*70)
    print_info("Загрузка Qwen2.5 72B (41GB)")
    print_info("Лучшая модель для русского языка и кода")
    print_info("Примерное время: 20-40 минут")
    print("-"*70 + "\n")
    
    run("ollama pull qwen2.5:72b", "Загрузка Qwen2.5 72B", timeout=3600)
    print_step("Qwen2.5 72B загружена!")
    
    # Llama Vision
    print("\n" + "-"*70)
    print_info("Загрузка Llama 3.2 Vision 90B (55GB)")
    print_info("Топовая модель для анализа изображений")
    print_info("Примерное время: 30-50 минут")
    print("-"*70 + "\n")
    
    run("ollama pull llama3.2-vision:90b", "Загрузка Vision модели", timeout=3600)
    print_step("Llama Vision 90B загружена!")
    
    # DeepSeek Coder
    print("\n" + "-"*70)
    print_info("Загрузка DeepSeek Coder 33B (19GB)")
    print_info("Специализирована на программировании")
    print_info("Примерное время: 10-20 минут")
    print("-"*70 + "\n")
    
    run("ollama pull deepseek-coder:33b", "Загрузка модели для кода", timeout=2400)
    print_step("DeepSeek Coder 33B загружена!")
    
    # Итоговый список
    print("\n" + "="*70)
    print("УСТАНОВЛЕННЫЕ МОДЕЛИ")
    print("="*70 + "\n")
    run("ollama list", "")
    
    # Тест
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ")
    print("="*70 + "\n")
    
    print_info("Тест Qwen2.5 72B...")
    run('ollama run qwen2.5:72b "Напиши функцию на Python для вычисления факториала числа. Ответь кратко и покажи только код."',
        "", timeout=120)
    
    # Финал
    print("\n" + "="*70)
    print("УСТАНОВКА ЗАВЕРШЕНА!")
    print("="*70)
    
    print(f"\n{Colors.GREEN}✓ SSH доступ:{Colors.END} ssh -p 42 user@{EXTERNAL_IP}")
    print(f"{Colors.GREEN}✓ Ollama API:{Colors.END} http://{EXTERNAL_IP}:11434")
    
    print(f"\n{Colors.BLUE}Установленные модели:{Colors.END}")
    print("  • Qwen2.5 72B - текст, код, русский язык")
    print("  • Llama Vision 90B - анализ изображений")
    print("  • DeepSeek Coder 33B - программирование")
    
    print(f"\n{Colors.BLUE}Примеры использования:{Colors.END}")
    print("  ollama run qwen2.5:72b")
    print("  ollama run llama3.2-vision:90b")
    print("  ollama run deepseek-coder:33b")
    
    print(f"\n{Colors.BLUE}Мониторинг:{Colors.END}")
    print("  nvidia-smi")
    print("  ollama ps")
    print("  systemctl status ollama")
    
    client.close()
    return True

if __name__ == "__main__":
    try:
        import paramiko
    except ImportError:
        print_error("Требуется установить paramiko:")
        print("  pip install paramiko")
        sys.exit(1)
    
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warn("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nОшибка: {e}")
        sys.exit(1)
