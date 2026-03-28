# Создание SSH туннеля с автоматическим вводом пароля
$password = "REDACTED"
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force

Write-Host "Создание SSH туннеля к серверу Dell R760..." -ForegroundColor Green
Write-Host "Порт 11434 (Ollama API) -> localhost:11434" -ForegroundColor Yellow
Write-Host ""
Write-Host "ВАЖНО: Оставьте это окно открытым!" -ForegroundColor Red
Write-Host ""

# Используем plink (PuTTY) если доступен, иначе обычный ssh
if (Get-Command plink -ErrorAction SilentlyContinue) {
    echo $password | plink -ssh -P 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST -pw $password
} else {
    # Обычный SSH (потребует ввод пароля вручную)
    ssh -p 42 -L 11434:localhost:11434 user@YOUR_PUBLIC_HOST
}
