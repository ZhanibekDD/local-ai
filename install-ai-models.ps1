# Установка моделей Ollama на удалённом хосте через SSH
# Обязательно: $env:SSH_PASSWORD; рекомендуется: $env:DEPLOY_HOST, $env:SSH_USER, $env:SSH_PORT

$ErrorActionPreference = "Stop"
$serverIP = if ($env:DEPLOY_HOST) { $env:DEPLOY_HOST } else { throw "Установите DEPLOY_HOST" }
$username = if ($env:SSH_USER) { $env:SSH_USER } else { "user" }
if (-not $env:SSH_PASSWORD) {
    Write-Error "Установите SSH_PASSWORD"
    exit 1
}
$password = $env:SSH_PASSWORD

Write-Host "=== Установка AI моделей ===" -ForegroundColor Green
Write-Host "Сервер: ${username}@${serverIP}" -ForegroundColor Cyan
Write-Host ""

function Invoke-SSHCommand {
    param([string]$Command, [string]$Description)
    Write-Host ">>> $Description" -ForegroundColor Yellow
    $securePassword = ConvertTo-SecureString $password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
    $sshCommand = "echo $password | ssh -o StrictHostKeyChecking=no -tt ${username}@${serverIP} `"$Command`""
    Invoke-Expression $sshCommand
}

# Пример: раскомментируйте нужные ollama pull на сервере
# Invoke-SSHCommand "ollama pull qwen2.5:72b" "Загрузка модели"

Write-Host "Отредактируйте скрипт под свои команды ollama pull." -ForegroundColor Yellow
