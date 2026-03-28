# Проверка доступности сервера Dell R760

$serverIP = "YOUR_LAN_HOST"
$routerIP = "192.168.1.1"

Write-Host "=== Проверка доступности сервера Dell R760 ===" -ForegroundColor Green
Write-Host ""

# 1. Проверка ping
Write-Host "[1] Проверка ping сервера..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $serverIP -Count 3 -Quiet
if ($pingResult) {
    Write-Host "[+] Сервер отвечает на ping" -ForegroundColor Green
} else {
    Write-Host "[-] Сервер НЕ отвечает на ping" -ForegroundColor Red
}

Write-Host ""

# 2. Проверка порта SSH (22)
Write-Host "[2] Проверка порта SSH (22)..." -ForegroundColor Yellow
$tcpClient = New-Object System.Net.Sockets.TcpClient
try {
    $tcpClient.Connect($serverIP, 22)
    Write-Host "[+] Порт 22 (SSH) открыт" -ForegroundColor Green
    $tcpClient.Close()
} catch {
    Write-Host "[-] Порт 22 (SSH) закрыт или недоступен" -ForegroundColor Red
}

Write-Host ""

# 3. Проверка порта Ollama (11434)
Write-Host "[3] Проверка порта Ollama (11434)..." -ForegroundColor Yellow
$tcpClient2 = New-Object System.Net.Sockets.TcpClient
try {
    $tcpClient2.Connect($serverIP, 11434)
    Write-Host "[+] Порт 11434 (Ollama) открыт" -ForegroundColor Green
    $tcpClient2.Close()
} catch {
    Write-Host "[-] Порт 11434 (Ollama) закрыт" -ForegroundColor Red
}

Write-Host ""

# 4. Проверка роутера
Write-Host "[4] Проверка ping роутера..." -ForegroundColor Yellow
$routerPing = Test-Connection -ComputerName $routerIP -Count 2 -Quiet
if ($routerPing) {
    Write-Host "[+] Роутер доступен ($routerIP)" -ForegroundColor Green
} else {
    Write-Host "[-] Роутер недоступен" -ForegroundColor Red
}

Write-Host ""

# 5. Сканирование сети
Write-Host "[5] Сканирование локальной сети..." -ForegroundColor Yellow
Write-Host "Поиск активных устройств в 192.168.1.0/24..." -ForegroundColor Cyan
Write-Host "(Это может занять 1-2 минуты)" -ForegroundColor Gray
Write-Host ""

$activeHosts = @()
1..254 | ForEach-Object {
    $ip = "192.168.1.$_"
    if (Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeoutSeconds 1) {
        $activeHosts += $ip
        Write-Host "[+] Найден: $ip" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Найдено активных устройств: $($activeHosts.Count)" -ForegroundColor Cyan

# Итоги
Write-Host ""
Write-Host "=== ИТОГИ ===" -ForegroundColor Green
Write-Host ""

if ($pingResult) {
    Write-Host "[*] Сервер доступен в сети" -ForegroundColor Green
    Write-Host "[*] Попробуйте подключиться:" -ForegroundColor Cyan
    Write-Host "    ssh youruser@$serverIP" -ForegroundColor White
    Write-Host ""
    Write-Host "[*] Или запустите автоустановку:" -ForegroundColor Cyan
    Write-Host "    python auto-install.py" -ForegroundColor White
} else {
    Write-Host "[!] Сервер недоступен" -ForegroundColor Red
    Write-Host ""
    Write-Host "Возможные причины:" -ForegroundColor Yellow
    Write-Host "  1. Сервер выключен" -ForegroundColor White
    Write-Host "  2. Неправильный IP адрес" -ForegroundColor White
    Write-Host "  3. Файрвол блокирует подключения" -ForegroundColor White
    Write-Host "  4. Сервер в другой подсети" -ForegroundColor White
    Write-Host ""
    Write-Host "Рекомендации:" -ForegroundColor Yellow
    Write-Host "  1. Проверьте что сервер включен (физически)" -ForegroundColor White
    Write-Host "  2. Используйте iDRAC9: https://YOUR_LAN_HOST или https://192.168.0.120" -ForegroundColor White
    Write-Host "  3. Подключите монитор к серверу" -ForegroundColor White
    Write-Host "  4. Смотрите ДИАГНОСТИКА-ПОДКЛЮЧЕНИЯ.md" -ForegroundColor White
}

Write-Host ""
