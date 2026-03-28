# Пошаговая установка AI моделей на Dell R760

## Подключение к серверу

Попробуйте один из способов подключения:

```bash
# Вариант 1: Прямое подключение (если в одной сети)
ssh user@YOUR_LAN_HOST

# Вариант 2: Через проброшенный порт
ssh -p 42 user@192.168.1.1

# Вариант 3: Если нужен root
ssh root@YOUR_LAN_HOST
```

**Пароль:** ***REDACTED***

---

## Команды для выполнения на сервере

### 1. Проверка системы и GPU

```bash
# Информация о системе
uname -a
lsb_release -a

# Проверка ресурсов
free -h
df -h

# Проверка наличия GPU
lspci | grep -i nvidia

# Проверка текущих драйверов (если есть)
nvidia-smi
```

---

### 2. Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

---

### 3. Установка базовых инструментов

```bash
sudo apt install -y build-essential git wget curl vim htop tmux net-tools
```

---

### 4. Установка NVIDIA драйверов и CUDA

```bash
# Поиск доступных драйверов
ubuntu-drivers devices

# Установка рекомендуемого драйвера
sudo apt install -y nvidia-driver-535 nvidia-utils-535

# Или автоматическая установка
sudo ubuntu-drivers autoinstall

# ПЕРЕЗАГРУЗКА ОБЯЗАТЕЛЬНА!
sudo reboot
```

**После перезагрузки подключитесь снова и проверьте:**

```bash
nvidia-smi
```

Вы должны увидеть информацию о NVIDIA A40.

---

### 5. Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Выход и повторный вход для применения изменений
exit
# Подключитесь снова
ssh user@YOUR_LAN_HOST
```

---

### 6. Установка NVIDIA Container Toolkit

```bash
# Настройка репозитория
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Установка
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Настройка Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Проверка
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi
```

Если видите вывод `nvidia-smi` в Docker - всё работает!

---

### 7. Установка Ollama

```bash
# Установка
curl -fsSL https://ollama.com/install.sh | sh

# Настройка для сетевого доступа
sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

# Перезапуск сервиса
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl enable ollama

# Проверка статуса
systemctl status ollama
```

---

### 8. Загрузка мощных текстовых моделей

```bash
# РЕКОМЕНДУЕТСЯ: Qwen2.5 72B - лучшая для русского языка
ollama pull qwen2.5:72b

# Альтернативы:
ollama pull llama3.1:70b          # Универсальная мощная модель
ollama pull deepseek-coder:33b   # Специализирована на коде
ollama pull mixtral:8x7b         # Быстрая и качественная

# Проверка загруженных моделей
ollama list
```

**Примерное время загрузки:** 20-40 минут на модель (зависит от скорости интернета)

---

### 9. Загрузка Vision моделей

```bash
# РЕКОМЕНДУЕТСЯ: Llama 3.2 Vision 90B - топовая vision модель
ollama pull llama3.2-vision:90b

# Альтернативы:
ollama pull llava:34b            # Хороший баланс
ollama pull llava:13b            # Быстрая, меньше памяти
ollama pull bakllava:13b         # Альтернативная vision модель

# Проверка
ollama list
```

---

### 10. Настройка файрвола

```bash
# Установка UFW
sudo apt install -y ufw

# Разрешение портов
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 11434/tcp    # Ollama API

# Включение файрвола
sudo ufw --force enable

# Проверка
sudo ufw status verbose
```

---

### 11. Тестирование моделей

#### Интерактивный режим:

```bash
# Текстовая модель
ollama run qwen2.5:72b

# Примеры запросов:
# - Привет! Расскажи о себе.
# - Напиши функцию на Python для быстрой сортировки.
# - Объясни что такое нейронные сети.

# Выход: /bye
```

```bash
# Vision модель
ollama run llama3.2-vision:90b

# Для анализа изображения:
# Опиши что на этом изображении /path/to/image.jpg
```

#### Через API:

```bash
# Текстовый запрос
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:72b",
  "prompt": "Привет! Напиши функцию сортировки на Python.",
  "stream": false
}'

# Vision запрос (сначала конвертируем изображение в base64)
IMAGE_BASE64=$(base64 -w 0 /path/to/image.jpg)

curl http://localhost:11434/api/generate -d "{
  \"model\": \"llama3.2-vision:90b\",
  \"prompt\": \"Опиши детально что на изображении\",
  \"images\": [\"$IMAGE_BASE64\"],
  \"stream\": false
}"
```

---

## Доступ к API из Windows

### PowerShell:

```powershell
# Текстовый запрос
$body = @{
    model = "qwen2.5:72b"
    prompt = "Привет! Как дела?"
    stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://YOUR_LAN_HOST:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
```

### Python:

```python
import requests
import base64

# Текстовый запрос
response = requests.post('http://YOUR_LAN_HOST:11434/api/generate', json={
    'model': 'qwen2.5:72b',
    'prompt': 'Привет! Напиши код на Python.',
    'stream': False
})
print(response.json()['response'])

# Vision запрос
with open('image.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post('http://YOUR_LAN_HOST:11434/api/generate', json={
    'model': 'llama3.2-vision:90b',
    'prompt': 'Опиши изображение',
    'images': [image_base64],
    'stream': False
})
print(response.json()['response'])
```

---

## Мониторинг и управление

### Мониторинг GPU:

```bash
# Установка gpustat
pip3 install gpustat

# Мониторинг в реальном времени
watch -n 1 gpustat

# Или стандартный nvidia-smi
watch -n 1 nvidia-smi
```

### Управление Ollama:

```bash
# Статус сервиса
systemctl status ollama

# Перезапуск
sudo systemctl restart ollama

# Логи
sudo journalctl -u ollama -f

# Список запущенных моделей
ollama ps

# Остановка модели
ollama stop model_name

# Удаление модели
ollama rm model_name
```

### Мониторинг системы:

```bash
# CPU и память
htop

# Диски
df -h
sudo iotop

# Сеть
sudo netstat -tulpn | grep LISTEN
```

---

## Оптимизация для максимальной производительности

### Настройка NVMe RAID для моделей:

```bash
# Проверка дисков
lsblk

# Создание RAID 0 из 3x NVMe (2.8TB общий объем, максимальная скорость)
sudo mdadm --create /dev/md0 --level=0 --raid-devices=3 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1

# Форматирование
sudo mkfs.ext4 /dev/md0

# Создание точки монтирования
sudo mkdir -p /mnt/models

# Монтирование
sudo mount /dev/md0 /mnt/models

# Автомонтирование при загрузке
echo '/dev/md0 /mnt/models ext4 defaults 0 0' | sudo tee -a /etc/fstab

# Изменение директории Ollama
sudo systemctl stop ollama
sudo mv /usr/share/ollama /mnt/models/ollama
sudo ln -s /mnt/models/ollama /usr/share/ollama
sudo systemctl start ollama
```

---

## Расширенная настройка: vLLM (для максимальной производительности)

Если нужна максимальная скорость инференса:

```bash
# Установка Python venv
sudo apt install -y python3-venv python3-pip

# Создание окружения
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate

# Установка vLLM
pip install vllm

# Запуск сервера с Qwen2.5 72B
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-72B-Instruct \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --port 8000 \
    --host 0.0.0.0

# В отдельной сессии tmux для фонового запуска:
tmux new -s vllm
# Запустите команду выше
# Отключитесь: Ctrl+B, затем D
```

---

## Альтернатива: Open WebUI (веб-интерфейс)

Для удобного веб-интерфейса к моделям:

```bash
# Создание docker-compose.yml
mkdir -p ~/ai-stack
cd ~/ai-stack

cat > docker-compose.yml <<'EOF'
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - open_webui_data:/app/backend/data
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:
  open_webui_data:
EOF

# Запуск
docker compose up -d

# Проверка логов
docker compose logs -f
```

Затем откройте в браузере: `http://YOUR_LAN_HOST:3000`

---

## Проверка установки

После всех шагов выполните:

```bash
# 1. GPU работает
nvidia-smi

# 2. Docker работает
docker ps

# 3. Ollama работает
systemctl status ollama
ollama list

# 4. Порты открыты
sudo netstat -tulpn | grep -E '(11434|3000|8000)'

# 5. Тест модели
ollama run qwen2.5:72b "Привет! Напиши Hello World на Python."
```

---

## Рекомендуемые модели для вашего сервера

### Для NVIDIA A40 (48GB VRAM):

**Текстовые модели (выберите 1-2):**
- `qwen2.5:72b` (41GB) - **РЕКОМЕНДУЕТСЯ** - отлично для русского языка
- `llama3.1:70b` (40GB) - универсальная мощная модель
- `deepseek-coder:33b` (19GB) - для программирования
- `mixtral:8x7b` (26GB) - быстрая и качественная

**Vision модели:**
- `llama3.2-vision:90b` (55GB с квантизацией) - **РЕКОМЕНДУЕТСЯ**
- `llava:34b` (20GB) - хороший баланс скорости и качества
- `llava:13b` (8GB) - быстрая, можно запускать одновременно с текстовой

### Можно запустить одновременно:
- 1x текстовая 70B модель + 1x vision 13B модель
- Или 2x текстовые 33B модели
- Или 1x vision 90B модель (займет почти всю память)

---

## Команды загрузки моделей

```bash
# Сначала загрузите текстовую модель (это займет 20-40 минут)
ollama pull qwen2.5:72b

# Проверка прогресса
ollama list

# Затем vision модель
ollama pull llama3.2-vision:90b

# Или более легкую версию
ollama pull llava:34b
```

---

## Настройка автозапуска

Ollama уже настроен как systemd сервис и запускается автоматически.

Проверка:
```bash
sudo systemctl status ollama
sudo systemctl enable ollama  # Автозапуск при загрузке
```

---

## Использование моделей

### Интерактивный чат:

```bash
# Текстовая модель
ollama run qwen2.5:72b
>>> Привет! Расскажи о своих возможностях.
>>> /bye  # Выход

# Vision модель с изображением
ollama run llama3.2-vision:90b
>>> Опиши что на этом изображении /home/youruser/image.jpg
```

### Через API (curl):

```bash
# Простой запрос
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:72b",
  "prompt": "Напиши функцию на Python для вычисления факториала",
  "stream": false
}'

# С параметрами
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:72b",
  "prompt": "Объясни квантовую физику простыми словами",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2000
  }
}'
```

### Через Python:

```python
import requests

def ask_ollama(prompt, model="qwen2.5:72b"):
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': model,
        'prompt': prompt,
        'stream': False
    })
    return response.json()['response']

# Использование
result = ask_ollama("Напиши функцию сортировки на Python")
print(result)
```

---

## Мониторинг производительности

### Создание скрипта мониторинга:

```bash
cat > ~/monitor.sh <<'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== GPU Status ==="
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader,nounits
    echo ""
    echo "=== Ollama Models ==="
    ollama ps
    echo ""
    echo "=== System Resources ==="
    free -h | grep Mem
    echo ""
    sleep 2
done
EOF

chmod +x ~/monitor.sh

# Запуск в tmux
tmux new -s monitor
~/monitor.sh
# Отключение: Ctrl+B, затем D
```

---

## Решение проблем

### Ollama не запускается:

```bash
# Проверка логов
sudo journalctl -u ollama -n 50 --no-pager

# Перезапуск
sudo systemctl restart ollama

# Проверка портов
sudo netstat -tulpn | grep 11434
```

### GPU не обнаруживается:

```bash
# Переустановка драйверов
sudo apt purge -y nvidia-*
sudo apt autoremove -y
sudo apt install -y nvidia-driver-535
sudo reboot
```

### Модель не загружается (нехватка памяти):

```bash
# Используйте квантизованные версии
ollama pull qwen2.5:72b-q4_0  # Меньше памяти
ollama pull llama3.1:70b-q4_K_M  # Квантизация 4-bit
```

### Медленная работа:

```bash
# Проверьте что GPU используется
nvidia-smi

# Проверьте загрузку CPU
htop

# Оптимизация параметров модели
ollama run qwen2.5:72b
>>> /set parameter num_gpu 1
>>> /set parameter num_thread 24
```

---

## Дополнительные порты для проброса в роутере

Добавьте в настройках роутера (192.168.1.1):

| Внешний порт | Внутренний IP | Внутренний порт | Описание |
|--------------|---------------|-----------------|----------|
| 42 | YOUR_LAN_HOST | 22 | SSH (уже настроен) |
| 11434 | YOUR_LAN_HOST | 11434 | Ollama API |
| 3000 | YOUR_LAN_HOST | 3000 | Open WebUI (если установлен) |
| 8000 | YOUR_LAN_HOST | 8000 | vLLM API (если используете) |

---

## Полезные ссылки

- **Ollama документация:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Список моделей:** https://ollama.com/library
- **Open WebUI:** https://github.com/open-webui/open-webui
- **vLLM:** https://docs.vllm.ai/

---

## Контакты
Email: admin@example.com
Сервер: Dell R760 (YOUR_LAN_HOST)
