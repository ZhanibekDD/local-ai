#!/usr/bin/env python3
"""
Подключение к серверу и установка AI моделей
Внешний IP: YOUR_PUBLIC_HOST
"""

import paramiko
import time
import sys

# Конфигурация
EXTERNAL_IP = "YOUR_PUBLIC_HOST"
SSH_PORT = 42
USERNAME = "dnepr"
PASSWORD = "REDACTED"

def connect_and_setup():
    """Подключение и установка"""
    print("="*70)
    print("  ПОДКЛЮЧЕНИЕ К DELL R760 AI SERVER")
    print("="*70)
    print(f"\nСервер: {EXTERNAL_IP}:{SSH_PORT}")
    print(f"Пользователь: {USERNAME}\n")
    
    # Подключение
    print("[*] Подключение к серверу...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            EXTERNAL_IP,
            port=SSH_PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=30,
            banner_timeout=30
        )
        print("[+] Подключение успешно!\n")
    except Exception as e:
        print(f"[-] Ошибка подключения: {e}")
        print("\nВозможные причины:")
        print("1. Порт 42 не проброшен в роутере")
        print("2. SSH не запущен на сервере")
        print("3. Файрвол блокирует подключение")
        print("\nОтправьте файл 'ДЛЯ-ВЫПОЛНЕНИЯ-НА-СЕРВЕРЕ.txt' человеку у сервера")
        return False
    
    def execute(command, description="", timeout=300):
        """Выполнение команды"""
        if description:
            print(f"\n>>> {description}")
        
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            if output:
                print(output)
            if error and "sudo" not in error.lower():
                print(f"[!] {error}")
            
            return output, exit_code
        except Exception as e:
            print(f"[-] Ошибка: {e}")
            return None, 1
    
    # Проверка системы
    print("="*70)
    print("ПРОВЕРКА СИСТЕМЫ")
    print("="*70)
    
    execute("hostname", "Имя сервера")
    execute("uname -a", "Версия ядра")
    execute("lsb_release -a", "Версия Ubuntu")
    execute("free -h", "Память")
    execute("df -h /", "Диск")
    
    # Проверка GPU
    output, code = execute("nvidia-smi", "Проверка GPU")
    
    if code == 0 and output and "NVIDIA" in output:
        print("\n[+] NVIDIA драйверы установлены!")
        gpu_installed = True
    else:
        print("\n[!] NVIDIA драйверы НЕ установлены")
        gpu_installed = False
    
    # Проверка Ollama
    output, code = execute("which ollama", "Проверка Ollama")
    ollama_installed = (code == 0)
    
    if ollama_installed:
        print("[+] Ollama установлен!")
        execute("ollama list", "Список моделей")
    else:
        print("[!] Ollama НЕ установлен")
    
    # Установка
    print("\n" + "="*70)
    print("УСТАНОВКА")
    print("="*70)
    
    if not ollama_installed:
        print("\n[*] Установка Ollama...")
        execute("curl -fsSL https://ollama.com/install.sh | sh", 
                "Загрузка и установка Ollama", timeout=180)
        
        # Настройка Ollama
        print("\n[*] Настройка Ollama для сетевого доступа...")
        commands = """
sudo mkdir -p /etc/systemd/system/ollama.service.d
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_HOST=0.0.0.0:11434"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_ORIGINS=*"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl enable ollama
"""
        execute(commands, "Настройка сервиса")
        time.sleep(3)
        execute("systemctl status ollama --no-pager", "Статус Ollama")
    
    if not gpu_installed:
        print("\n[*] Установка NVIDIA драйверов...")
        execute("sudo apt update", "Обновление пакетов", timeout=120)
        execute("sudo apt install -y nvidia-driver-535 nvidia-utils-535", 
                "Установка драйверов", timeout=600)
        
        print("\n[!] ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА для активации драйверов!")
        print("Выполните: sudo reboot")
        print("Затем запустите этот скрипт снова")
        client.close()
        return False
    
    # Файрвол
    print("\n[*] Настройка файрвола...")
    execute("sudo apt install -y ufw", "Установка UFW", timeout=60)
    execute("sudo ufw allow 22/tcp", "Разрешение SSH")
    execute("sudo ufw allow 11434/tcp", "Разрешение Ollama API")
    execute("sudo ufw --force enable", "Включение файрвола")
    execute("sudo ufw status", "Статус файрвола")
    
    # Загрузка моделей
    print("\n" + "="*70)
    print("ЗАГРУЗКА AI МОДЕЛЕЙ")
    print("="*70)
    print("\n[!] ВНИМАНИЕ: Загрузка займет 30-60 минут!")
    print("[!] Модели очень большие (40-55GB каждая)\n")
    
    response = input("Загрузить модели сейчас? (y/n): ")
    
    if response.lower() == 'y':
        execute("ollama list", "Текущие модели")
        
        print("\n[*] Загрузка Qwen2.5 72B...")
        print("Прогресс будет отображаться ниже (20-40 минут):\n")
        execute("ollama pull qwen2.5:72b", "Загрузка Qwen2.5 72B", timeout=3600)
        
        print("\n[*] Загрузка Llama 3.2 Vision 90B...")
        print("Прогресс будет отображаться ниже (30-50 минут):\n")
        execute("ollama pull llama3.2-vision:90b", "Загрузка Vision модели", timeout=3600)
        
        print("\n[*] Загрузка DeepSeek Coder 33B...")
        execute("ollama pull deepseek-coder:33b", "Загрузка модели для кода", timeout=2400)
        
        print("\n[+] Модели загружены!")
        execute("ollama list", "Список установленных моделей")
        
        # Тест
        print("\n[*] Тестирование модели...")
        execute('ollama run qwen2.5:72b "Привет! Напиши функцию Hello World на Python. Ответь кратко."',
                "Тест Qwen2.5", timeout=120)
    else:
        print("\n[*] Загрузка моделей пропущена")
        print("Для загрузки позже выполните на сервере:")
        print("  ollama pull qwen2.5:72b")
        print("  ollama pull llama3.2-vision:90b")
        print("  ollama pull deepseek-coder:33b")
    
    # Итоги
    print("\n" + "="*70)
    print("УСТАНОВКА ЗАВЕРШЕНА!")
    print("="*70)
    print(f"\n[+] SSH доступ: ssh -p 42 user@{EXTERNAL_IP}")
    print(f"[+] Ollama API: http://{EXTERNAL_IP}:11434")
    print("\n[*] Примеры использования:")
    print("  ollama run qwen2.5:72b")
    print('  curl http://localhost:11434/api/generate -d \'{"model":"qwen2.5:72b","prompt":"Привет!","stream":false}\'')
    print("\n[*] Мониторинг GPU:")
    print("  nvidia-smi")
    print("  watch -n 1 nvidia-smi")
    
    client.close()
    return True

if __name__ == "__main__":
    try:
        import paramiko
    except ImportError:
        print("[-] Требуется установить paramiko:")
        print("    pip install paramiko")
        sys.exit(1)
    
    try:
        connect_and_setup()
    except KeyboardInterrupt:
        print("\n\n[!] Прервано пользователем")
        sys.exit(1)
