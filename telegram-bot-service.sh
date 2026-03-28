#!/bin/bash
# Создание systemd сервиса для Telegram бота

echo "=== Создание systemd сервиса для Telegram бота ==="

# Создание systemd unit файла
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram AI Bot
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/telegram-bot
ExecStart=/usr/bin/python3 /home/youruser/telegram-bot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск и автозапуск
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Проверка статуса
echo ""
echo "=== Статус бота ==="
sudo systemctl status telegram-bot

echo ""
echo "=== Управление ботом ==="
echo "Статус:      sudo systemctl status telegram-bot"
echo "Остановка:   sudo systemctl stop telegram-bot"
echo "Запуск:      sudo systemctl start telegram-bot"
echo "Перезапуск:  sudo systemctl restart telegram-bot"
echo "Логи:        sudo journalctl -u telegram-bot -f"
