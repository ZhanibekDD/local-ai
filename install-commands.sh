#!/bin/bash
# Скрипт установки AI моделей на Dell R760
# Ubuntu Server 22.04 LTS
# 
# Использование:
# 1. Скопируйте этот файл на сервер: scp install-commands.sh user@YOUR_LAN_HOST:~/
# 2. Подключитесь к серверу: ssh user@YOUR_LAN_HOST
# 3. Запустите: chmod +x install-commands.sh && ./install-commands.sh

set -e  # Остановка при ошибке

echo "======================================================================"
echo "  УСТАНОВКА AI МОДЕЛЕЙ НА DELL R760"
echo "======================================================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода шагов
print_step() {
    echo -e "${GREEN}>>> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[-] $1${NC}"
}

# ШАГ 1: Проверка системы
echo "======================================================================"
echo "ШАГ 1: Проверка системы"
echo "======================================================================"
echo ""

print_step "Информация о системе"
uname -a
lsb_release -a

print_step "Ресурсы"
free -h
df -h /

print_step "Проверка GPU"
lspci | grep -i nvidia || echo "GPU не обнаружен через lspci"

# Проверка nvidia-smi
if command -v nvidia-smi &> /dev/null; then
    print_step "NVIDIA драйверы уже установлены"
    nvidia-smi
    NVIDIA_INSTALLED=1
else
    print_warning "NVIDIA драйверы не установлены"
    NVIDIA_INSTALLED=0
fi

echo ""
read -p "Продолжить установку? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# ШАГ 2: Обновление системы
echo ""
echo "======================================================================"
echo "ШАГ 2: Обновление системы"
echo "======================================================================"
echo ""

print_step "Обновление списка пакетов"
sudo apt update

print_step "Обновление установленных пакетов"
sudo apt upgrade -y

# ШАГ 3: Базовые инструменты
echo ""
echo "======================================================================"
echo "ШАГ 3: Установка базовых инструментов"
echo "======================================================================"
echo ""

print_step "Установка инструментов разработки"
sudo apt install -y build-essential git wget curl vim htop tmux net-tools python3-pip

# ШАГ 4: NVIDIA драйверы
if [ $NVIDIA_INSTALLED -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "ШАГ 4: Установка NVIDIA драйверов"
    echo "======================================================================"
    echo ""
    
    print_step "Поиск доступных драйверов"
    ubuntu-drivers devices
    
    print_step "Установка NVIDIA драйверов"
    sudo apt install -y nvidia-driver-535 nvidia-utils-535
    
    print_warning "ТРЕБУЕТСЯ ПЕРЕЗАГРУЗКА!"
    echo ""
    echo "Выполните: sudo reboot"
    echo "После перезагрузки запустите этот скрипт снова"
    exit 0
else
    echo ""
    echo "======================================================================"
    echo "ШАГ 4: NVIDIA драйверы уже установлены"
    echo "======================================================================"
    echo ""
fi

# ШАГ 5: Docker
echo ""
echo "======================================================================"
echo "ШАГ 5: Установка Docker"
echo "======================================================================"
echo ""

if command -v docker &> /dev/null; then
    print_step "Docker уже установлен"
    docker --version
else
    print_step "Загрузка и установка Docker"
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    
    print_step "Добавление пользователя в группу docker"
    sudo usermod -aG docker $USER
    
    print_warning "Выйдите и войдите снова для применения прав docker"
fi

# ШАГ 6: NVIDIA Container Toolkit
echo ""
echo "======================================================================"
echo "ШАГ 6: Установка NVIDIA Container Toolkit"
echo "======================================================================"
echo ""

print_step "Настройка репозитория"
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

print_step "Установка toolkit"
sudo apt update
sudo apt install -y nvidia-container-toolkit

print_step "Настройка Docker для GPU"
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

print_step "Проверка GPU в Docker"
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi

# ШАГ 7: Ollama
echo ""
echo "======================================================================"
echo "ШАГ 7: Установка Ollama"
echo "======================================================================"
echo ""

if command -v ollama &> /dev/null; then
    print_step "Ollama уже установлен"
    ollama --version
else
    print_step "Установка Ollama"
    curl -fsSL https://ollama.com/install.sh | sh
fi

print_step "Настройка Ollama для сетевого доступа"
sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl enable ollama

sleep 3

print_step "Проверка статуса Ollama"
systemctl status ollama --no-pager

# ШАГ 8: Файрвол
echo ""
echo "======================================================================"
echo "ШАГ 8: Настройка файрвола"
echo "======================================================================"
echo ""

print_step "Установка UFW"
sudo apt install -y ufw

print_step "Настройка правил"
sudo ufw allow 22/tcp
sudo ufw allow 11434/tcp

print_step "Включение файрвола"
sudo ufw --force enable

print_step "Статус файрвола"
sudo ufw status verbose

# ШАГ 9: Загрузка моделей
echo ""
echo "======================================================================"
echo "ШАГ 9: Загрузка AI моделей"
echo "======================================================================"
echo ""

print_warning "Загрузка моделей займет 30-60 минут!"
print_warning "Модели очень большие (40-55GB каждая)"
echo ""

read -p "Загрузить модели сейчас? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Текущие модели"
    ollama list
    
    echo ""
    print_step "Загрузка Qwen2.5 72B (лучшая для русского языка)"
    echo "Это займет 20-40 минут..."
    ollama pull qwen2.5:72b
    
    echo ""
    print_step "Загрузка Llama 3.2 Vision 90B"
    echo "Это займет 30-50 минут..."
    ollama pull llama3.2-vision:90b
    
    echo ""
    print_step "Загрузка дополнительной модели для кода"
    ollama pull deepseek-coder:33b
    
    echo ""
    print_step "Список установленных моделей"
    ollama list
    
    # ШАГ 10: Тестирование
    echo ""
    echo "======================================================================"
    echo "ШАГ 10: Тестирование моделей"
    echo "======================================================================"
    echo ""
    
    print_step "Тест Qwen2.5 72B"
    ollama run qwen2.5:72b "Привет! Напиши функцию на Python для вычисления факториала. Ответь кратко."
    
    echo ""
    print_step "Тест через API"
    curl http://localhost:11434/api/generate -d '{
      "model": "qwen2.5:72b",
      "prompt": "Напиши Hello World на Python",
      "stream": false
    }'
else
    echo ""
    print_step "Пропуск загрузки моделей"
    echo "Для загрузки позже выполните:"
    echo "  ollama pull qwen2.5:72b"
    echo "  ollama pull llama3.2-vision:90b"
    echo "  ollama pull deepseek-coder:33b"
fi

# Финал
echo ""
echo "======================================================================"
echo "УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================================================================"
echo ""
echo "Ollama API доступен: http://YOUR_LAN_HOST:11434"
echo ""
echo "Примеры использования:"
echo ""
echo "1. Интерактивный режим:"
echo "   ollama run qwen2.5:72b"
echo ""
echo "2. Через API:"
echo "   curl http://localhost:11434/api/generate -d '{\"model\":\"qwen2.5:72b\",\"prompt\":\"Привет!\",\"stream\":false}'"
echo ""
echo "3. Мониторинг GPU:"
echo "   watch -n 1 nvidia-smi"
echo ""
echo "4. Список моделей:"
echo "   ollama list"
echo ""
echo "5. Статус сервиса:"
echo "   systemctl status ollama"
echo ""
