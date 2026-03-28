# Скрипт загрузки AI моделей (запускать после перезагрузки сервера)

$serverIP = "YOUR_LAN_HOST"
$username = "dnepr"

Write-Host "=== Загрузка AI моделей ===" -ForegroundColor Green
Write-Host ""

Write-Host "Подключитесь к серверу:" -ForegroundColor Cyan
Write-Host "ssh $username@$serverIP" -ForegroundColor White
Write-Host ""

Write-Host "Затем выполните следующие команды:" -ForegroundColor Cyan
Write-Host ""

Write-Host "# 1. Проверка GPU" -ForegroundColor Yellow
Write-Host "nvidia-smi" -ForegroundColor White
Write-Host ""

Write-Host "# 2. Проверка Ollama" -ForegroundColor Yellow
Write-Host "systemctl status ollama" -ForegroundColor White
Write-Host ""

Write-Host "# 3. Загрузка текстовых моделей (выберите 1-2)" -ForegroundColor Yellow
Write-Host "ollama pull qwen2.5:72b          # 41GB, лучшая для русского языка" -ForegroundColor White
Write-Host "ollama pull llama3.1:70b         # 40GB, универсальная мощная модель" -ForegroundColor White
Write-Host "ollama pull deepseek-coder:33b  # 19GB, для программирования" -ForegroundColor White
Write-Host ""

Write-Host "# 4. Загрузка Vision моделей" -ForegroundColor Yellow
Write-Host "ollama pull llama3.2-vision:90b  # 55GB, топовая vision модель" -ForegroundColor White
Write-Host "ollama pull llava:34b            # 20GB, хороший баланс" -ForegroundColor White
Write-Host ""

Write-Host "# 5. Проверка установленных моделей" -ForegroundColor Yellow
Write-Host "ollama list" -ForegroundColor White
Write-Host ""

Write-Host "# 6. Тест текстовой модели" -ForegroundColor Yellow
Write-Host "ollama run qwen2.5:72b 'Привет! Напиши функцию на Python для сортировки.'" -ForegroundColor White
Write-Host ""

Write-Host "# 7. Тест vision модели" -ForegroundColor Yellow
Write-Host "ollama run llama3.2-vision:90b 'Опиши что видишь' /path/to/image.jpg" -ForegroundColor White
Write-Host ""

Write-Host "=== API доступ ===" -ForegroundColor Green
Write-Host "Ollama API будет доступен по адресу: http://YOUR_LAN_HOST:11434" -ForegroundColor Cyan
Write-Host ""

Write-Host "Тест API из Windows PowerShell:" -ForegroundColor Yellow
$apiTest = @'
$body = @{
    model = "qwen2.5:72b"
    prompt = "Привет! Как дела?"
    stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://YOUR_LAN_HOST:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
'@
Write-Host $apiTest -ForegroundColor White
