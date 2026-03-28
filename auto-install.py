#!/usr/bin/env python3
"""
Автоматическая установка AI моделей на Dell R760
Ubuntu Server 22.04 LTS
"""

import os
import paramiko
import time
import sys

SERVER_IP = os.environ.get("DEPLOY_HOST", "YOUR_LAN_HOST")
USERNAME = os.environ.get("SSH_USER", "user")
PASSWORD = os.environ.get("SSH_PASSWORD")
SSH_PORT = int(os.environ.get("SSH_PORT", "22"))
if not PASSWORD:
    sys.exit("Задайте SSH_PASSWORD в окружении")

class ServerSetup:
    def __init__(self):
        self.client = None
        self.connected = False
        
    def connect(self):
        """Подключение к серверу по SSH"""
        print(f"[*] Подключение к {USERNAME}@{SERVER_IP}...")
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                SERVER_IP,
                port=SSH_PORT,
                username=USERNAME,
                password=PASSWORD,
                timeout=10
            )
            self.connected = True
            print("[+] Подключение успешно!\n")
            return True
        except Exception as e:
            print(f"[-] Ошибка подключения: {e}")
            print("\nПопробуйте:")
            print(f"1. Проверьте что сервер включен и доступен")
            print(f"2. Проверьте ping: ping {SERVER_IP}")
            print(f"3. Проверьте SSH: ssh {USERNAME}@{SERVER_IP}")
            return False
    
    def execute(self, command, description="", sudo=False, timeout=300):
        """Выполнение команды на сервере"""
        if not self.connected:
            print("[-] Нет подключения к серверу")
            return None
            
        if description:
            print(f">>> {description}")
        
        try:
            if sudo:
                command = f"echo {PASSWORD} | sudo -S {command}"
            
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Чтение вывода
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            if output:
                print(output)
            if error and exit_code != 0:
                print(f"[!] Ошибка: {error}")
            
            return output, error, exit_code
            
        except Exception as e:
            print(f"[-] Ошибка выполнения: {e}")
            return None, str(e), 1
    
    def check_system(self):
        """Проверка системы"""
        print("\n" + "="*60)
        print("ШАГ 1: Проверка системы")
        print("="*60 + "\n")
        
        self.execute("uname -a", "Информация о системе")
        self.execute("lsb_release -a", "Версия Ubuntu")
        self.execute("free -h", "Память")
        self.execute("df -h /", "Дисковое пространство")
        self.execute("lspci | grep -i nvidia", "Проверка GPU")
        
    def update_system(self):
        """Обновление системы"""
        print("\n" + "="*60)
        print("ШАГ 2: Обновление системы")
        print("="*60 + "\n")
        
        self.execute("apt update", "Обновление списка пакетов", sudo=True, timeout=120)
        self.execute("apt upgrade -y", "Обновление пакетов", sudo=True, timeout=600)
        
    def install_basics(self):
        """Установка базовых инструментов"""
        print("\n" + "="*60)
        print("ШАГ 3: Установка базовых инструментов")
        print("="*60 + "\n")
        
        packages = "build-essential git wget curl vim htop tmux net-tools python3-pip"
        self.execute(f"apt install -y {packages}", "Установка инструментов", sudo=True, timeout=300)
        
    def install_nvidia_drivers(self):
        """Установка NVIDIA драйверов"""
        print("\n" + "="*60)
        print("ШАГ 4: Установка NVIDIA драйверов")
        print("="*60 + "\n")
        
        # Проверка текущих драйверов
        output, _, _ = self.execute("nvidia-smi", "Проверка текущих драйверов")
        
        if output and "NVIDIA" in output:
            print("[+] NVIDIA драйверы уже установлены!")
            return True
        
        print("[*] Установка NVIDIA драйверов...")
        self.execute("apt install -y nvidia-driver-535 nvidia-utils-535", 
                    "Установка драйверов", sudo=True, timeout=600)
        
        print("\n[!] ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА СЕРВЕРА!")
        print("Выполните: sudo reboot")
        print("Затем запустите этот скрипт снова.\n")
        return False
        
    def install_docker(self):
        """Установка Docker"""
        print("\n" + "="*60)
        print("ШАГ 5: Установка Docker")
        print("="*60 + "\n")
        
        # Проверка Docker
        output, _, exit_code = self.execute("docker --version", "Проверка Docker")
        
        if exit_code == 0:
            print("[+] Docker уже установлен!")
        else:
            print("[*] Установка Docker...")
            self.execute("curl -fsSL https://get.docker.com -o /tmp/get-docker.sh", 
                        "Загрузка установщика Docker")
            self.execute("sh /tmp/get-docker.sh", "Установка Docker", sudo=True, timeout=300)
            self.execute(f"usermod -aG docker {USERNAME}", "Добавление в группу docker", sudo=True)
        
    def install_nvidia_toolkit(self):
        """Установка NVIDIA Container Toolkit"""
        print("\n" + "="*60)
        print("ШАГ 6: Установка NVIDIA Container Toolkit")
        print("="*60 + "\n")
        
        commands = """
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) && \
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
"""
        self.execute(commands, "Настройка репозитория", timeout=60)
        self.execute("apt update", "Обновление списка пакетов", sudo=True, timeout=60)
        self.execute("apt install -y nvidia-container-toolkit", "Установка toolkit", sudo=True, timeout=300)
        self.execute("nvidia-ctk runtime configure --runtime=docker", "Настройка Docker", sudo=True)
        self.execute("systemctl restart docker", "Перезапуск Docker", sudo=True)
        
        print("\n[*] Проверка NVIDIA Container Toolkit...")
        self.execute("docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi",
                    "Тест GPU в Docker", timeout=120)
        
    def install_ollama(self):
        """Установка Ollama"""
        print("\n" + "="*60)
        print("ШАГ 7: Установка Ollama")
        print("="*60 + "\n")
        
        # Проверка Ollama
        output, _, exit_code = self.execute("ollama --version", "Проверка Ollama")
        
        if exit_code == 0:
            print("[+] Ollama уже установлен!")
        else:
            print("[*] Установка Ollama...")
            self.execute("curl -fsSL https://ollama.com/install.sh | sh", 
                        "Установка Ollama", timeout=180)
        
        # Настройка для сетевого доступа
        print("\n[*] Настройка Ollama для сетевого доступа...")
        
        config_commands = """
sudo mkdir -p /etc/systemd/system/ollama.service.d && \
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf && \
echo 'Environment="OLLAMA_HOST=0.0.0.0:11434"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf && \
echo 'Environment="OLLAMA_ORIGINS=*"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf && \
sudo systemctl daemon-reload && \
sudo systemctl restart ollama && \
sudo systemctl enable ollama
"""
        self.execute(config_commands, "Настройка сервиса Ollama", timeout=30)
        
        time.sleep(3)
        self.execute("systemctl status ollama --no-pager", "Проверка статуса Ollama")
        
    def setup_firewall(self):
        """Настройка файрвола"""
        print("\n" + "="*60)
        print("ШАГ 8: Настройка файрвола")
        print("="*60 + "\n")
        
        self.execute("apt install -y ufw", "Установка UFW", sudo=True, timeout=120)
        self.execute("ufw allow 22/tcp", "Разрешение SSH", sudo=True)
        self.execute("ufw allow 11434/tcp", "Разрешение Ollama API", sudo=True)
        self.execute("ufw --force enable", "Включение файрвола", sudo=True)
        self.execute("ufw status verbose", "Статус файрвола", sudo=True)
        
    def download_models(self):
        """Загрузка AI моделей"""
        print("\n" + "="*60)
        print("ШАГ 9: Загрузка AI моделей")
        print("="*60 + "\n")
        
        print("[!] ВНИМАНИЕ: Загрузка моделей займет 30-60 минут!")
        print("Модели очень большие (40-55GB каждая)\n")
        
        # Проверка текущих моделей
        self.execute("ollama list", "Текущие модели")
        
        print("\n[*] Загрузка Qwen2.5 72B (лучшая для русского языка)...")
        print("Это займет 20-40 минут в зависимости от скорости интернета.\n")
        
        self.execute("ollama pull qwen2.5:72b", "Загрузка Qwen2.5 72B", timeout=3600)
        
        print("\n[*] Загрузка Llama 3.2 Vision 90B (vision модель)...")
        print("Это займет 30-50 минут.\n")
        
        self.execute("ollama pull llama3.2-vision:90b", "Загрузка Vision модели", timeout=3600)
        
        print("\n[+] Модели загружены!")
        self.execute("ollama list", "Список установленных моделей")
        
    def test_models(self):
        """Тестирование моделей"""
        print("\n" + "="*60)
        print("ШАГ 10: Тестирование моделей")
        print("="*60 + "\n")
        
        print("[*] Тест текстовой модели Qwen2.5 72B...")
        test_command = """ollama run qwen2.5:72b "Привет! Напиши простую функцию на Python для вычисления факториала числа. Ответь кратко." """
        self.execute(test_command, "Тест Qwen2.5", timeout=120)
        
        print("\n[+] Тестирование завершено!")
        
    def run_full_setup(self):
        """Полная установка"""
        print("\n" + "="*70)
        print("  АВТОМАТИЧЕСКАЯ УСТАНОВКА AI МОДЕЛЕЙ НА DELL R760")
        print("="*70 + "\n")
        
        # Подключение
        if not self.connect():
            return False
        
        try:
            # Проверка системы
            self.check_system()
            
            # Обновление
            self.update_system()
            
            # Базовые инструменты
            self.install_basics()
            
            # NVIDIA драйверы
            needs_reboot = not self.install_nvidia_drivers()
            
            if needs_reboot:
                print("\n" + "="*70)
                print("⚠️  ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА СЕРВЕРА")
                print("="*70)
                print("\nВыполните на сервере:")
                print(f"  ssh {USERNAME}@{SERVER_IP}")
                print("  sudo reboot")
                print("\nЗатем запустите этот скрипт снова:")
                print("  python auto-install.py")
                return False
            
            # Docker
            self.install_docker()
            
            # NVIDIA Container Toolkit
            self.install_nvidia_toolkit()
            
            # Ollama
            self.install_ollama()
            
            # Файрвол
            self.setup_firewall()
            
            # Загрузка моделей
            print("\n" + "="*70)
            response = input("Загрузить модели сейчас? (y/n): ")
            if response.lower() == 'y':
                self.download_models()
                self.test_models()
            else:
                print("\n[*] Для загрузки моделей позже выполните на сервере:")
                print("  ollama pull qwen2.5:72b")
                print("  ollama pull llama3.2-vision:90b")
            
            print("\n" + "="*70)
            print("[+] УСТАНОВКА ЗАВЕРШЕНА!")
            print("="*70)
            print(f"\n[*] Ollama API доступен: http://{SERVER_IP}:11434")
            print("\n[*] Примеры использования:")
            print(f"  ssh {USERNAME}@{SERVER_IP}")
            print("  ollama run qwen2.5:72b")
            print("\nИли через API:")
            print(f'  curl http://{SERVER_IP}:11434/api/generate -d \'{{"model":"qwen2.5:72b","prompt":"Привет!","stream":false}}\'')
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n[!] Установка прервана пользователем")
            return False
        except Exception as e:
            print(f"\n[-] Ошибка: {e}")
            return False
        finally:
            if self.client:
                self.client.close()
                print("\n[*] Отключено от сервера")

def main():
    """Главная функция"""
    setup = ServerSetup()
    success = setup.run_full_setup()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    # Проверка зависимостей
    try:
        import paramiko
    except ImportError:
        print("[-] Требуется установить paramiko:")
        print("   pip install paramiko")
        sys.exit(1)
    
    main()
