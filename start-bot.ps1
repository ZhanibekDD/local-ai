# Запуск Telegram бота
Write-Host "Проверка SSH туннеля..." -ForegroundColor Green

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    Write-Host "✅ SSH туннель работает!" -ForegroundColor Green
} catch {
    Write-Host "❌ SSH туннель не работает!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Сначала запустите start-tunnel.ps1 в отдельном окне!" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit
}

Write-Host ""
Write-Host "Запуск Telegram бота..." -ForegroundColor Green
Write-Host ""

# Запуск бота
python telegram-bot-local.py
