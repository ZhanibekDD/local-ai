# Check Dell R760 Server

$serverIP = "YOUR_LAN_HOST"

Write-Host "=== Check Server $serverIP ===" -ForegroundColor Green
Write-Host ""

Write-Host "[1] Ping test..." -ForegroundColor Yellow
$ping = Test-Connection -ComputerName $serverIP -Count 3 -Quiet
if ($ping) {
    Write-Host "[+] Server responds to ping" -ForegroundColor Green
} else {
    Write-Host "[-] Server does NOT respond" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2] SSH port (22) test..." -ForegroundColor Yellow
$tcp = New-Object System.Net.Sockets.TcpClient
try {
    $tcp.Connect($serverIP, 22)
    Write-Host "[+] SSH port 22 is OPEN" -ForegroundColor Green
    $tcp.Close()
} catch {
    Write-Host "[-] SSH port 22 is CLOSED" -ForegroundColor Red
}

Write-Host ""
Write-Host "[3] Ollama port (11434) test..." -ForegroundColor Yellow
$tcp2 = New-Object System.Net.Sockets.TcpClient
try {
    $tcp2.Connect($serverIP, 11434)
    Write-Host "[+] Ollama port 11434 is OPEN" -ForegroundColor Green
    $tcp2.Close()
} catch {
    Write-Host "[-] Ollama port 11434 is CLOSED" -ForegroundColor Red
}

Write-Host ""
if ($ping) {
    Write-Host "Next step: ssh user@$serverIP" -ForegroundColor Cyan
} else {
    Write-Host "Server is not accessible. Check:" -ForegroundColor Yellow
    Write-Host "  1. Server is powered on" -ForegroundColor White
    Write-Host "  2. Network cable connected" -ForegroundColor White
    Write-Host "  3. Use iDRAC: https://$serverIP" -ForegroundColor White
}
