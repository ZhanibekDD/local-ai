#!/bin/bash
echo "=== Оптимизация моделей для русского языка и производительности ==="

# Создание оптимизированной Qwen
echo "Создание qwen-ru..."
cat > /tmp/Modelfile-qwen-ru << 'EOF'
FROM qwen2.5:72b

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 8192
PARAMETER num_gpu 1
PARAMETER num_thread 32

SYSTEM """Ты умный AI ассистент. Ты ВСЕГДА отвечаешь ТОЛЬКО на русском языке.

Правила:
- Отвечай подробно и понятно на русском
- Если вопрос на английском - отвечай на русском
- Будь полезным и профессиональным
- Не выдумывай информацию

Отвечай на русском языке."""
EOF

ollama create qwen-ru -f /tmp/Modelfile-qwen-ru

# Создание оптимизированного Coder
echo "Создание coder-ru..."
cat > /tmp/Modelfile-coder-ru << 'EOF'
FROM deepseek-coder:33b

PARAMETER temperature 0.3
PARAMETER top_p 0.95
PARAMETER num_ctx 4096
PARAMETER num_gpu 1
PARAMETER num_thread 32

SYSTEM """Ты опытный программист. Все комментарии и объяснения ТОЛЬКО на русском языке.

Правила:
- Пиши чистый, читаемый код
- Комментарии на русском
- Следуй best practices
- Добавляй примеры использования"""
EOF

ollama create coder-ru -f /tmp/Modelfile-coder-ru

# Создание оптимизированного Vision
echo "Создание vision-ru..."
cat > /tmp/Modelfile-vision-ru << 'EOF'
FROM llama3.2-vision:90b

PARAMETER temperature 0.5
PARAMETER num_ctx 4096
PARAMETER num_gpu 1
PARAMETER num_thread 32

SYSTEM """Ты AI для анализа изображений. Отвечай ТОЛЬКО на русском языке.

Правила:
- Подробно описывай изображения на русском
- Отвечай на вопросы об изображении
- Распознавай текст если есть
- Все описания на русском"""
EOF

ollama create vision-ru -f /tmp/Modelfile-vision-ru

# Настройка Ollama для производительности
echo "Настройка Ollama..."
sudo systemctl stop ollama

sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/performance.conf > /dev/null << 'EOF'
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
EOF

sudo systemctl daemon-reload
sudo systemctl start ollama

echo ""
echo "=== Оптимизация завершена! ==="
echo ""
ollama list
echo ""
echo "Новые модели:"
echo "  • qwen-ru - оптимизированная для русского"
echo "  • coder-ru - код с русскими комментариями"
echo "  • vision-ru - анализ изображений на русском"
echo ""
echo "Перезапустите бота для использования новых моделей!"
