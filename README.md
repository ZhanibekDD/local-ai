# Dell R760 AI Server - Установка и настройка

## Содержание

1. [Характеристики сервера](#характеристики-сервера)
2. [Файлы в этой папке](#файлы-в-этой-папке)
3. [Быстрый старт](#быстрый-старт)
4. [Решение проблем](#решение-проблем)

---

## Характеристики сервера

**Dell PowerEdge R760**

- **Процессоры:** 2x Intel Xeon Silver 4516Y+ (24 ядра каждый, 48 ядер всего)
- **Частота:** 2GHz base, 185W TDP
- **Память:** 8x 64GB DDR5 4800MHz RDIMM = **512GB RAM**
- **GPU:** NVIDIA A40 48GB VRAM (профессиональная карта для AI/ML)
- **Хранилище:**
  - 3x SSD 960GB NVMe U.2 (быстрые для моделей)
  - 5x HDD 1.8TB 2.5" SAS 10K (для данных)
- **RAID:** H965i + BOSS-N1+2xM.2
- **Сеть:** 2x 10GbE SFP+ (высокоскоростная сеть)
- **Питание:** 2x 1400W (резервирование)
- **Управление:** iDRAC9 Enterprise (удаленное управление)

**Возможности для AI:**
- Запуск моделей до 70-90B параметров
- Одновременная работа нескольких моделей
- Высокая скорость инференса благодаря A40
- Профессиональное решение для продакшена

---

## Файлы в этой папке

### Основные инструкции:

1. **`БЫСТРЫЙ-СТАРТ.md`** ⭐ 
   - Самая краткая инструкция
   - Готовые команды для копирования
   - Начните с этого файла!

2. **`manual-setup-commands.md`**
   - Подробная пошаговая инструкция
   - Объяснения каждого шага
   - Решение проблем

3. **`server-setup.md`**
   - Полная документация
   - Все варианты установки
   - Оптимизация и настройка

4. **`ДИАГНОСТИКА-ПОДКЛЮЧЕНИЯ.md`**
   - Если сервер не отвечает
   - Проверка сети и SSH
   - Работа с iDRAC

### Скрипты:

5. **`install-commands.sh`**
   - Bash скрипт для запуска на сервере
   - Автоматическая установка всего
   - Копируйте на сервер и запускайте

6. **`auto-install.py`**
   - Python скрипт для удаленной установки
   - Запускается с Windows
   - Требует доступ к серверу по SSH

7. **`ollama-client.py`**
   - Python клиент для работы с моделями
   - Примеры использования API
   - Запускайте после установки

### Дополнительные:

8. **`install-ai-models.ps1`** - PowerShell скрипт (альтернатива)
9. **`download-models.ps1`** - Инструкции для загрузки моделей
10. **`quick-install.md`** - Краткая версия инструкции
11. **`requirements.txt`** - Python зависимости

---

## Быстрый старт

### Вариант 1: Автоматическая установка (рекомендуется)

**Шаг 1:** Скопируйте скрипт на сервер
```bash
scp install-commands.sh user@YOUR_LAN_HOST:~/
```

**Шаг 2:** Подключитесь к серверу
```bash
ssh user@YOUR_LAN_HOST
```
Пароль: `REDACTED`

**Шаг 3:** Запустите установку
```bash
chmod +x install-commands.sh
./install-commands.sh
```

Скрипт автоматически:
- Обновит систему
- Установит NVIDIA драйверы
- Установит Docker и NVIDIA Container Toolkit
- Установит Ollama
- Настроит файрвол
- Предложит загрузить модели

### Вариант 2: Ручная установка

Откройте файл **`БЫСТРЫЙ-СТАРТ.md`** и копируйте команды блоками.

---

## Что будет установлено

### Программное обеспечение:
- **NVIDIA Driver 535** - драйверы для GPU
- **CUDA Toolkit** - для работы с GPU
- **Docker** - контейнеризация
- **NVIDIA Container Toolkit** - GPU в Docker
- **Ollama** - платформа для запуска AI моделей

### AI Модели:

**Текстовые:**
- **Qwen2.5 72B** (41GB) - лучшая для русского языка и кода
- **DeepSeek Coder 33B** (19GB) - специализирована на программировании

**Vision:**
- **Llama 3.2 Vision 90B** (55GB) - топовая мультимодальная модель

**Общий размер:** ~115GB (убедитесь что есть свободное место)

---

## После установки

### Проверка работы:

```bash
# Подключение к серверу
ssh user@YOUR_LAN_HOST

# Проверка GPU
nvidia-smi

# Проверка Ollama
systemctl status ollama
ollama list

# Тест модели
ollama run qwen2.5:72b "Привет! Напиши Hello World на Python."
```

### Использование из Windows:

**PowerShell:**
```powershell
$body = @{
    model = "qwen2.5:72b"
    prompt = "Напиши функцию сортировки на Python"
    stream = $false
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://YOUR_LAN_HOST:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
Write-Host $response.response
```

**Python:**
```bash
python ollama-client.py list
python ollama-client.py ask "qwen2.5:72b" "Привет! Как дела?"
python ollama-client.py vision "llama3.2-vision:90b" "Опиши изображение" image.jpg
```

---

## Решение проблем

### Сервер не отвечает:

1. **Проверьте подключение:**
   ```bash
   ping YOUR_LAN_HOST
   ```

2. **Используйте iDRAC9:**
   - Откройте https://YOUR_LAN_HOST (или IP iDRAC)
   - Войдите (root/YOUR_IDRAC_PASSWORD или с наклейки)
   - Проверьте статус сервера
   - Откройте Virtual Console

3. **Физический доступ:**
   - Подключите монитор и клавиатуру
   - Войдите в систему
   - Проверьте сеть: `ip addr show`

### GPU не обнаруживается:

```bash
# Переустановка драйверов
sudo apt purge -y nvidia-*
sudo apt autoremove -y
sudo apt install -y nvidia-driver-535
sudo reboot
```

### Ollama не работает:

```bash
# Проверка логов
sudo journalctl -u ollama -n 50

# Перезапуск
sudo systemctl restart ollama

# Проверка портов
sudo netstat -tulpn | grep 11434
```

### Модель не загружается:

```bash
# Проверьте место на диске
df -h

# Используйте квантизованные версии (меньше памяти)
ollama pull qwen2.5:72b-q4_0
```

---

## Дополнительные возможности

### Web интерфейс (Open WebUI)

Установите для удобного веб-интерфейса:

```bash
mkdir -p ~/ai-stack
cd ~/ai-stack

# Создайте docker-compose.yml (см. БЫСТРЫЙ-СТАРТ.md)
docker compose up -d
```

Откройте: `http://YOUR_LAN_HOST:3000`

### Мониторинг GPU

```bash
# Установка gpustat
pip3 install gpustat

# Мониторинг в реальном времени
watch -n 1 gpustat

# Или стандартный
watch -n 1 nvidia-smi
```

### Оптимизация хранилища

Создайте RAID 0 из NVMe для максимальной скорости:

```bash
# Проверка дисков
lsblk

# Создание RAID 0 из 3x NVMe (2.8TB, очень быстро)
sudo mdadm --create /dev/md0 --level=0 --raid-devices=3 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1
sudo mkfs.ext4 /dev/md0
sudo mkdir -p /mnt/models
sudo mount /dev/md0 /mnt/models

# Автомонтирование
echo '/dev/md0 /mnt/models ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

---

## Рекомендации по моделям

### Для вашего сервера (A40 48GB):

**Одна большая модель:**
- Qwen2.5 72B или Llama 3.1 70B (займет ~40GB)
- Llama 3.2 Vision 90B (займет ~50GB с квантизацией)

**Несколько средних моделей одновременно:**
- DeepSeek Coder 33B + LLaVA 13B
- Mixtral 8x7B + LLaVA 34B

**Максимальная скорость:**
- Llama 3.1 8B (очень быстрая)
- Qwen2.5 7B (быстрая, хорошее качество)

---

## Полезные ссылки

- **Ollama:** https://ollama.com
- **Модели:** https://ollama.com/library
- **API документация:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Open WebUI:** https://github.com/open-webui/open-webui
- **vLLM:** https://docs.vllm.ai/

---

## Контакты

- **Email:** admin@example.com
- **Сервер:** Dell PowerEdge R760
- **IP:** YOUR_LAN_HOST
- **SSH:** user@YOUR_LAN_HOST (порт 22)
- **Пароль:** REDACTED

---

## Следующие шаги

1. ✅ Прочитайте `БЫСТРЫЙ-СТАРТ.md`
2. ✅ Подключитесь к серверу по SSH
3. ✅ Скопируйте и запустите `install-commands.sh`
4. ✅ Дождитесь загрузки моделей (30-60 минут)
5. ✅ Протестируйте модели
6. ✅ Используйте через API или интерактивно

**Удачи с настройкой AI сервера! 🚀**
