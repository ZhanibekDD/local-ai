#!/usr/bin/env python3
import paramiko
import time

IP = "YOUR_PUBLIC_HOST"
PORT = 42
USER = "dnepr"
PASS = "REDACTED"

print("Подключение к", IP)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(IP, port=PORT, username=USER, password=PASS, timeout=30)
print("Подключено!\n")

def run(cmd):
    if cmd.startswith('sudo'):
        cmd = f"echo '{PASS}' | sudo -S {cmd[5:]}"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600, get_pty=True)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    return out

print("=== ПРОВЕРКА ===\n")
run("hostname && uname -r")
run("free -h | grep Mem")

output = run("nvidia-smi 2>/dev/null || echo 'NO_GPU'")
gpu_ok = "NVIDIA" in output

output = run("ollama --version 2>/dev/null || echo 'NO_OLLAMA'")
ollama_ok = "version" in output

print(f"\nGPU: {'OK' if gpu_ok else 'NOT INSTALLED'}")
print(f"Ollama: {'OK' if ollama_ok else 'NOT INSTALLED'}\n")

print("=== УСТАНОВКА ===\n")

if not ollama_ok:
    print("Установка Ollama...")
    run("curl -fsSL https://ollama.com/install.sh | sh")
    run("sudo mkdir -p /etc/systemd/system/ollama.service.d")
    run("echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf")
    run("echo 'Environment=\"OLLAMA_HOST=0.0.0.0:11434\"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf")
    run("sudo systemctl daemon-reload && sudo systemctl restart ollama && sudo systemctl enable ollama")
    time.sleep(3)
    print("Ollama установлен!")

if not gpu_ok:
    print("\nУстановка NVIDIA драйверов (5-10 минут)...")
    run("sudo apt update")
    run("sudo apt install -y nvidia-driver-535")
    print("\n[!] ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА!")
    print("Выполните: ssh -p 42 user@YOUR_PUBLIC_HOST")
    print("           sudo reboot")
    print("Затем запустите скрипт снова")
    client.close()
    sys.exit(0)

print("\nНастройка файрвола...")
run("sudo apt install -y ufw")
run("sudo ufw allow 22/tcp && sudo ufw allow 11434/tcp && sudo ufw --force enable")

print("\n=== ЗАГРУЗКА МОДЕЛЕЙ ===\n")
print("Это займет 30-60 минут!\n")

print("1. Qwen2.5 72B (20-40 мин)...")
run("ollama pull qwen2.5:72b")

print("\n2. Llama Vision 90B (30-50 мин)...")
run("ollama pull llama3.2-vision:90b")

print("\n3. DeepSeek Coder 33B (10-20 мин)...")
run("ollama pull deepseek-coder:33b")

print("\n=== СПИСОК МОДЕЛЕЙ ===\n")
run("ollama list")

print("\n=== ТЕСТ ===\n")
run('ollama run qwen2.5:72b "Напиши Hello World на Python"')

print("\n" + "="*70)
print("ГОТОВО!")
print("="*70)
print(f"\nSSH: ssh -p 42 user@{IP}")
print(f"API: http://{IP}:11434\n")

client.close()

if __name__ == "__main__":
    try:
        import paramiko
    except ImportError:
        print("pip install paramiko")
        sys.exit(1)
    main()
