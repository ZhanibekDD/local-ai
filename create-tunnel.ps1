# SSH-туннель Ollama: 11434 на сервере -> localhost:11434
# Задайте: $env:SSH_PASSWORD = "..."  и при необходимости $env:SSH_USER, $env:DEPLOY_HOST, $env:SSH_PORT

$ErrorActionPreference = "Stop"
$user = if ($env:SSH_USER) { $env:SSH_USER } else { "user" }
$host = if ($env:DEPLOY_HOST) { $env:DEPLOY_HOST } else { throw "Установите DEPLOY_HOST (хост SSH)" }
$port = if ($env:SSH_PORT) { [int]$env:SSH_PORT } else { 22 }
if (-not $env:SSH_PASSWORD) {
    Write-Error "Установите переменную окружения SSH_PASSWORD"
    exit 1
}

Write-Host "Туннель: ${user}@${host}:${port} -> localhost:11434 (оставьте окно открытым)" -ForegroundColor Green

if (Get-Command plink -ErrorAction SilentlyContinue) {
    echo $env:SSH_PASSWORD | plink -ssh -P $port -L 11434:localhost:11434 "${user}@${host}" -pw $env:SSH_PASSWORD
} else {
    ssh -p $port -L 11434:localhost:11434 "${user}@${host}"
}
