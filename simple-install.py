#!/usr/bin/env python3
"""
Простая установка AI на Dell R760
IP: YOUR_PUBLIC_HOST:42
"""

import os
import paramiko
import time
import sys

IP = os.environ.get("DEPLOY_HOST", "YOUR_PUBLIC_HOST")
PORT = int(os.environ.get("SSH_PORT", "42"))
USER = os.environ.get("SSH_USER", "user")
PASS = os.environ.get("SSH_PASSWORD")
if not PASS:
    sys.exit("Задайте SSH_PASSWORD в окружении")

def main():
    print("="*70)
    print("  УСТАНОВКА AI НА DELL R760")
    print("="*70)
    print(f"\nСервер: {IP}:{PORT}\n")
    
    # Подключение
    print("[*] Подключение...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(IP, port=PORT, username=USER, password=PASS, timeout=30)
        print("[+] Подключено!\n")
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    def run(cmd, desc=""):
        """Выполнение команды"""
        if desc:
            print(f"\n>>> {desc}")
        
        if cmd.strip().startswith('sudo'):
            cmd = f"echo '{PASS}' | sudo -S {cmd[5:]}"
        
        try:
            stdin, stdout, stderr = client.exec_command(cmd, timeout=300, get_pty=True)
            output = stdout.read().decode('utf-8', errors='ignore')
            print(output)
            return output
        except Exception as e:
            print(f"Ошибка: {e}")
            return ""
    
    # Проверка
    print("="*70)
    print("ПРОВЕРКА СИСТЕМЫ")
    print("="*70)
    
    run("hostname", "Имя сервера")
    run("free -h | grep Mem", "Память")
    run("df -h / | tail -1", "Диск")
    
    output = run("nvidia-smi 2>/dev/null || echo 'GPU_NOT_FOUND'", "GPU")
    gpu_ok = "NVIDIA" in output
    
    output = run("ollama --version 2>/dev/null || echo 'OLLAMA_NOT_FOUND'", "Ollama")
    ollama_ok = "ollama version" in output.lower()
    
    # Установка
    print("\n" + "="*70)
    print("УСТАНОВКА")
    print("="*70)
    
    if not gpu_ok or not ollama_ok:
        run("sudo apt update -y", "Обновление")
    
    if not ollama_ok:
        print("\n[*] Установка Ollama (1-2 минуты)...")
        run("curl -fsSL https://ollama.com/install.sh | sh", "Ollama")
        
        run("sudo mkdir -p /etc/systemd/system/ollama.service.d", "")
        run("echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf", "")
        run("echo 'Environment=\"OLLAMA_HOST=0.0.0.0:11434\"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf", "")
        run("sudo systemctl daemon-reload && sudo systemctl restart ollama && sudo systemctl enable ollama", "Запуск Ollama")
        time.sleep(3)
    
    if not gpu_ok:
        print("\n[*] Установка NVIDIA (5-10 минут)...")
        run("sudo apt install -y nvidia-driver-535", "NVIDIA драйверы")
        print("\n[!] ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА: sudo reboot")
        print("После перезагрузки запустите скрипт снова")
        client.close()
        return False
    
    run("sudo apt install -y ufw", "UFW")
    run("sudo ufw allow 22/tcp && sudo ufw allow 11434/tcp && sudo ufw --force enable", "Файрвол")
    
    # Модели
    print("\n" + "="*70)
    print("ЗАГРУЗКА МОДЕЛЕЙ")
    print("="*70)
    print("\n[!] Это займет 30-60 минут!\n")
    
    response = input("Начать загрузку? (y/n): ")
    if response.lower() != 'y':
        print("\nДля загрузки позже: ollama pull qwen2.5:72b")
        client.close()
        return True
    
    print("\n[*] Загрузка Qwen2.5 72B (20-40 мин)...")
    run("ollama pull qwen2.5:72b", "")
    
    print("\n[*] Загрузка Llama Vision 90B (30-50 мин)...")
    run("ollama pull llama3.2-vision:90b", "")
    
    print("\n[*] Загрузка DeepSeek Coder 33B (10-20 мин)...")
    run("ollama pull deepseek-coder:33b", "")
    
    run("ollama list", "Установленные модели")
    
    print("\n[*] Тест модели...")
    run('ollama run qwen2.5:72b "Hello World на Python"', "")
    
    print("\n" + "="*70)
    print("ГОТОВО!")
    print("="*70)
    print(f"\nSSH: ssh -p {PORT} {USER}@{IP}")
    print(f"API: http://{IP}:11434")
    
    client.close()
    return True

if __name__ == "__main__":
    try:
        import paramiko
    except ImportError:
        print("pip install paramiko")
        sys.exit(1)
    
    main()
