# Быстрая установка AI моделей на Dell R760

## Предварительные требования
- Сервер с Ubuntu 22.04 LTS или новее
- SSH доступ к серверу
- Интернет подключение

---

## Быстрая установка (копируйте команды блоками)

### 1. Подключение к серверу
```bash
ssh root@YOUR_LAN_HOST
# Введите пароль
```

### 2. Установка NVIDIA драйверов и CUDA
```bash
sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
sudo reboot
```

После перезагрузки подключитесь снова и проверьте:
```bash
nvidia-smi
```

### 3. Установка Docker + NVIDIA Container Toolkit
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Проверка
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi
```

### 4. Установка Ollama (самый простой способ)
```bash
curl -fsSL https://ollama.com/install.sh | sh

# Настройка для доступа по сети
sudo mkdir -p /etc/systemd/system/ollama.service.d
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_HOST=0.0.0.0:11434"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 5. Загрузка мощных моделей

**Текстовые модели:**
```bash
# Топовые модели (выберите 1-2, они большие)
ollama pull llama3.1:70b          # 40GB, универсальная
ollama pull qwen2.5:72b           # 41GB, отличная для кода и русского
ollama pull deepseek-coder:33b   # 19GB, для программирования

# Проверка
ollama list
```

**Vision модели:**
```bash
# Мультимодальные модели
ollama pull llama3.2-vision:90b   # 55GB, топовая vision
ollama pull llava:34b             # 20GB, хороший баланс
ollama pull llava:13b             # 8GB, быстрая

# Тест vision модели
ollama run llama3.2-vision:90b "Опиши что видишь на изображении"
```

### 6. Настройка файрвола
```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 11434/tcp
sudo ufw enable
sudo ufw status
```

---

## Тестирование моделей

### Текстовая модель через API
```bash
curl http://YOUR_LAN_HOST:11434/api/generate -d '{
  "model": "llama3.1:70b",
  "prompt": "Напиши функцию на Python для сортировки массива",
  "stream": false
}'
```

### Vision модель через API
```bash
# Сначала конвертируйте изображение в base64
IMAGE_BASE64=$(base64 -w 0 /path/to/image.jpg)

curl http://YOUR_LAN_HOST:11434/api/generate -d "{
  \"model\": \"llama3.2-vision:90b\",
  \"prompt\": \"Опиши детально что на изображении\",
  \"images\": [\"$IMAGE_BASE64\"],
  \"stream\": false
}"
```

### Интерактивный режим
```bash
# Текстовая модель
ollama run llama3.1:70b

# Vision модель
ollama run llama3.2-vision:90b
```

---

## Альтернатива: Установка через Docker Compose

Создайте файл `docker-compose.yml`:

```yaml
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
```

Запуск:
```bash
docker compose up -d
```

Теперь у вас будет:
- **Ollama API:** http://YOUR_LAN_HOST:11434
- **Web интерфейс:** http://YOUR_LAN_HOST:3000

---

## Рекомендации по моделям для вашего GPU (A40 48GB)

### Оптимальные модели:
- **Llama 3.1 70B** (квантизация Q4) - влезет в 48GB
- **Qwen2.5 72B** (Q4) - отличная для русского языка
- **Llama 3.2 Vision 90B** (Q4) - топовая vision модель

### Если нужна максимальная скорость:
- **Llama 3.1 8B** - очень быстрая, хорошее качество
- **LLaVA 13B** - быстрая vision модель

### Для одновременной работы нескольких моделей:
- Используйте vLLM с tensor parallelism
- Или запускайте несколько экземпляров Ollama в Docker

---

## Полезные команды

```bash
# Просмотр логов Ollama
sudo journalctl -u ollama -f

# Остановка/запуск Ollama
sudo systemctl stop ollama
sudo systemctl start ollama

# Удаление модели
ollama rm model_name

# Информация о модели
ollama show llama3.1:70b

# Список запущенных моделей
ollama ps
```

---

## Следующие шаги

1. Подключитесь к серверу по SSH
2. Выполните команды установки
3. Загрузите нужные модели
4. Протестируйте через API или интерактивный режим
5. Настройте дополнительные порты в роутере для внешнего доступа
