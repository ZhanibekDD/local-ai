# Автоматический запуск SSH туннеля и Telegram бота
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TELEGRAM BOT - Dell R760 AI Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python не найден!" -ForegroundColor Red
    Write-Host "Установите Python: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit
}

# Проверка библиотек
Write-Host "[CHECK] Проверка Python библиотек..." -ForegroundColor Yellow
try {
    python -c "import telegram; import requests" 2>$null
    Write-Host "[OK] Библиотеки установлены" -ForegroundColor Green
} catch {
    Write-Host "[INSTALL] Установка библиотек..." -ForegroundColor Yellow
    pip install python-telegram-bot requests
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ШАГ 1: Создание SSH туннеля" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Запуск SSH туннеля в фоне..." -ForegroundColor Yellow
Write-Host "Сервер: YOUR_PUBLIC_HOST:42" -ForegroundColor Gray
Write-Host "Туннель: localhost:11434 -> server:11434" -ForegroundColor Gray
Write-Host ""

# Запуск SSH туннеля в фоновом задании
$tunnelJob = Start-Job -ScriptBlock {
    ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST
}

Write-Host "Ожидание установки туннеля (10 сек)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка туннеля
Write-Host "[CHECK] Проверка SSH туннеля..." -ForegroundColor Yellow
$tunnelOk = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "[OK] SSH туннель работает!" -ForegroundColor Green
        $tunnelOk = $true
        break
    } catch {
        Write-Host "[WAIT] Попытка $i/5..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $tunnelOk) {
    Write-Host ""
    Write-Host "[ERROR] SSH туннель не установлен!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Запустите туннель вручную в отдельном окне:" -ForegroundColor Yellow
    Write-Host "  ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST" -ForegroundColor White
    Write-Host "  Пароль: REDACTED" -ForegroundColor White
    Write-Host ""
    Write-Host "Затем запустите этот скрипт снова" -ForegroundColor Yellow
    Write-Host ""
    
    Stop-Job $tunnelJob
    Remove-Job $tunnelJob
    pause
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ШАГ 2: Запуск Telegram бота" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Запуск бота (версия с системой чатов)
python telegram-bot-advanced.py

# Очистка при завершении
Write-Host ""
Write-Host "[CLEANUP] Остановка SSH туннеля..." -ForegroundColor Yellow
Stop-Job $tunnelJob
Remove-Job $tunnelJob
Write-Host "[STOP] Бот остановлен" -ForegroundColor Red
