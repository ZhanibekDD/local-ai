# Настройка сервера Dell R760 для AI моделей

## Характеристики сервера
- **Процессоры:** 2x Intel Xeon Silver 4516Y+ (48 ядер, 2GHz)
- **Память:** 512GB DDR5 4800MHz
- **Хранилище:** 3x 960GB NVMe SSD + 5x 1.8TB SAS HDD
- **GPU:** NVIDIA A40 (48GB VRAM) - отлично для AI
- **Сеть:** 2x 10GbE SFP+
- **Управление:** iDRAC9 Enterprise

## Текущая конфигурация
- **IP сервера:** YOUR_LAN_HOST
- **Роутер:** 192.168.1.1
- **Port Forwarding:** 42 → YOUR_LAN_HOST:22 (SSH)

---

## Шаг 1: Подключение по SSH

### Из локальной сети:
```bash
ssh root@YOUR_LAN_HOST
# или если создан пользователь:
ssh user@YOUR_LAN_HOST
```

### Из внешней сети (через проброшенный порт):
```bash
ssh -p 42 root@ВАШ_ВНЕШНИЙ_IP
```

---

## Шаг 2: Первоначальная настройка сервера

### 2.1 Обновление системы
```bash
# Для Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Для RHEL/Rocky/AlmaLinux
sudo dnf update -y
```

### 2.2 Установка необходимых пакетов
```bash
# Базовые инструменты
sudo apt install -y build-essential git wget curl vim htop tmux

# Python и pip
sudo apt install -y python3 python3-pip python3-venv

# Docker (для контейнеризации моделей)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2.3 Установка NVIDIA драйверов и CUDA
```bash
# Проверка GPU
lspci | grep -i nvidia

# Установка драйверов NVIDIA
sudo apt install -y nvidia-driver-535 nvidia-utils-535

# Установка CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda_12.3.0_545.23.06_linux.run
sudo sh cuda_12.3.0_545.23.06_linux.run

# Добавить в ~/.bashrc
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Проверка
nvidia-smi
```

---

## Шаг 3: Установка текстовых AI моделей

### Вариант 1: Ollama (рекомендуется для простоты)

```bash
# Установка Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Запуск как сервис
sudo systemctl enable ollama
sudo systemctl start ollama

# Установка мощных моделей
ollama pull llama3.1:70b          # 70B параметров, очень мощная
ollama pull qwen2.5:72b           # 72B параметров, отличная для кода
ollama pull deepseek-coder:33b   # 33B, специализирована на коде
ollama pull mixtral:8x22b         # 141B параметров, топовая модель

# Проверка установленных моделей
ollama list

# Тест модели
ollama run llama3.1:70b "Привет, как дела?"
```

### Вариант 2: vLLM (для максимальной производительности)

```bash
# Создание виртуального окружения
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate

# Установка vLLM
pip install vllm

# Запуск сервера с моделью
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --port 8000
```

### Вариант 3: Text Generation Inference (Hugging Face)

```bash
# Через Docker
docker run --gpus all --shm-size 1g -p 8080:80 \
    -v ~/models:/data \
    ghcr.io/huggingface/text-generation-inference:latest \
    --model-id meta-llama/Llama-3.1-70B-Instruct \
    --num-shard 1
```

---

## Шаг 4: Установка Vision моделей

### Вариант 1: Ollama с мультимодальными моделями

```bash
# Мощные vision модели
ollama pull llama3.2-vision:90b   # 90B, отличное vision
ollama pull llava:34b             # 34B, специализирована на vision
ollama pull bakllava:13b          # Легче, но быстрее

# Тест vision модели
ollama run llama3.2-vision:90b "Опиши это изображение" /path/to/image.jpg
```

### Вариант 2: LLaVA через vLLM

```bash
source ~/vllm-env/bin/activate

# Запуск LLaVA сервера
python -m vllm.entrypoints.openai.api_server \
    --model llava-hf/llava-v1.6-34b-hf \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --port 8001
```

### Вариант 3: ComfyUI + Florence-2 (для детального анализа изображений)

```bash
# Клонирование ComfyUI
cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py --listen 0.0.0.0 --port 8188
```

---

## Шаг 5: Настройка безопасности SSH

### 5.1 Создание пользователя
```bash
# Создать пользователя
sudo adduser dnepr
sudo usermod -aG sudo dnepr

# Переключиться на пользователя
su - dnepr
```

### 5.2 Настройка SSH ключей
```bash
# На вашем локальном компьютере (Windows PowerShell):
ssh-keygen -t ed25519 -C "admin@example.com"

# Копирование ключа на сервер
scp ~/.ssh/id_ed25519.pub user@YOUR_LAN_HOST:~/

# На сервере:
mkdir -p ~/.ssh
cat ~/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
rm ~/id_ed25519.pub
```

### 5.3 Усиление безопасности SSH
```bash
sudo vim /etc/ssh/sshd_config
```

Изменить параметры:
```
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
AllowUsers dnepr
```

Перезапуск SSH:
```bash
sudo systemctl restart sshd
```

---

## Шаг 6: Настройка файрвола

```bash
# UFW (Ubuntu)
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp  # vLLM текст
sudo ufw allow 8001/tcp  # vLLM vision
sudo ufw allow 8080/tcp  # TGI
sudo ufw allow 8188/tcp  # ComfyUI
sudo ufw allow 11434/tcp # Ollama API
sudo ufw enable

# Проверка статуса
sudo ufw status
```

---

## Шаг 7: Настройка автозапуска моделей

### Создание systemd сервиса для Ollama
```bash
sudo vim /etc/systemd/system/ollama.service
```

Содержимое:
```ini
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=dnepr
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
```

---

## Шаг 8: Мониторинг и управление

### Мониторинг GPU
```bash
# Установка gpustat
pip install gpustat

# Мониторинг в реальном времени
watch -n 1 gpustat

# Или nvidia-smi
watch -n 1 nvidia-smi
```

### Мониторинг системы
```bash
# Установка htop, iotop
sudo apt install -y htop iotop

# Запуск
htop
```

---

## Шаг 9: API доступ к моделям

### Ollama API
```bash
# Тестирование API
curl http://YOUR_LAN_HOST:11434/api/generate -d '{
  "model": "llama3.1:70b",
  "prompt": "Привет, как дела?",
  "stream": false
}'

# Vision API
curl http://YOUR_LAN_HOST:11434/api/generate -d '{
  "model": "llama3.2-vision:90b",
  "prompt": "Опиши изображение",
  "images": ["base64_encoded_image"],
  "stream": false
}'
```

### vLLM OpenAI-совместимый API
```bash
# Текстовая модель
curl http://YOUR_LAN_HOST:8000/v1/completions -H "Content-Type: application/json" -d '{
  "model": "meta-llama/Llama-3.1-70B-Instruct",
  "prompt": "Привет!",
  "max_tokens": 100
}'
```

---

## Рекомендуемые модели для вашего сервера

### Текстовые модели (с NVIDIA A40 48GB):
1. **Llama 3.1 70B** - универсальная, очень мощная
2. **Qwen2.5 72B** - отличная для кода и рассуждений
3. **DeepSeek Coder 33B** - специализирована на программировании
4. **Mixtral 8x22B** (141B) - самая мощная, потребует квантизацию

### Vision модели:
1. **Llama 3.2 Vision 90B** - топовая мультимодальная модель
2. **LLaVA 34B** - отличный баланс качества и скорости
3. **CogVLM2** - специализирована на детальном анализе изображений

---

## Шаг 10: Оптимизация производительности

### Настройка RAID для моделей
```bash
# Проверка дисков
lsblk

# Создание RAID 0 из NVMe для максимальной скорости
sudo mdadm --create /dev/md0 --level=0 --raid-devices=3 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1

# Форматирование и монтирование
sudo mkfs.ext4 /dev/md0
sudo mkdir /mnt/models
sudo mount /dev/md0 /mnt/models

# Автомонтирование
echo '/dev/md0 /mnt/models ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

### Настройка swap (опционально)
```bash
# Создание 64GB swap
sudo fallocate -l 64G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Проверка доступа

После настройки проверьте:

1. **SSH:** `ssh -p 42 user@ВАШ_ВНЕШНИЙ_IP`
2. **Ollama API:** `http://YOUR_LAN_HOST:11434`
3. **GPU статус:** `nvidia-smi`
4. **Модели:** `ollama list`

---

## Дополнительные порты для проброса

Рекомендую добавить в роутере:
- **11434** → YOUR_LAN_HOST:11434 (Ollama API)
- **8000** → YOUR_LAN_HOST:8000 (vLLM текст)
- **8001** → YOUR_LAN_HOST:8001 (vLLM vision)
- **8188** → YOUR_LAN_HOST:8188 (ComfyUI)

---

## Контакты и поддержка
Email: admin@example.com
