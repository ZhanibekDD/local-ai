# Создание SSH туннеля для Ollama API
Write-Host "Создание SSH туннеля к серверу..." -ForegroundColor Green
Write-Host "Порт 11434 (Ollama) будет доступен на localhost:11434" -ForegroundColor Yellow
Write-Host ""
Write-Host "ВАЖНО: Оставьте это окно открытым!" -ForegroundColor Red
Write-Host ""

# Запуск SSH туннеля
ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST
