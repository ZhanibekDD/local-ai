# Скрипт автоматической установки AI моделей на Dell R760
# Ubuntu Server 22.04 LTS

$serverIP = "YOUR_LAN_HOST"
$username = "dnepr"
$password = "REDACTED"

Write-Host "=== Установка AI моделей на сервер Dell R760 ===" -ForegroundColor Green
Write-Host "Сервер: $serverIP" -ForegroundColor Cyan
Write-Host ""

# Функция для выполнения команд через SSH
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host ">>> $Description" -ForegroundColor Yellow
    
    $securePassword = ConvertTo-SecureString $password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
    
    # Используем plink (PuTTY) если доступен, иначе ssh с expect-подобным поведением
    $sshCommand = "echo $password | ssh -o StrictHostKeyChecking=no -tt $username@$serverIP `"$Command`""
    
    Invoke-Expression $sshCommand
}

# Шаг 1: Проверка системы
Write-Host "`n=== Шаг 1: Проверка системы ===" -ForegroundColor Green
$commands = @"
uname -a
lsb_release -a
free -h
df -h
lspci | grep -i nvidia
"@

# Шаг 2: Обновление системы
Write-Host "`n=== Шаг 2: Обновление системы ===" -ForegroundColor Green
Invoke-SSHCommand "sudo apt update && sudo apt upgrade -y" "Обновление пакетов"

# Шаг 3: Установка базовых инструментов
Write-Host "`n=== Шаг 3: Установка базовых инструментов ===" -ForegroundColor Green
Invoke-SSHCommand "sudo apt install -y build-essential git wget curl vim htop tmux" "Установка инструментов"

# Шаг 4: Установка NVIDIA драйверов
Write-Host "`n=== Шаг 4: Установка NVIDIA драйверов ===" -ForegroundColor Green
Invoke-SSHCommand "sudo apt install -y nvidia-driver-535 nvidia-utils-535" "Установка драйверов"

# Шаг 5: Установка Docker
Write-Host "`n=== Шаг 5: Установка Docker ===" -ForegroundColor Green
$dockerCommands = @"
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && \
sudo sh /tmp/get-docker.sh && \
sudo usermod -aG docker $username
"@
Invoke-SSHCommand $dockerCommands "Установка Docker"

# Шаг 6: Установка NVIDIA Container Toolkit
Write-Host "`n=== Шаг 6: Установка NVIDIA Container Toolkit ===" -ForegroundColor Green
$nvidiaToolkit = @"
distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID) && \
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && \
curl -s -L https://nvidia.github.io/libnvidia-container/\$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && \
sudo apt update && \
sudo apt install -y nvidia-container-toolkit && \
sudo nvidia-ctk runtime configure --runtime=docker && \
sudo systemctl restart docker
"@
Invoke-SSHCommand $nvidiaToolkit "Установка NVIDIA Container Toolkit"

# Шаг 7: Установка Ollama
Write-Host "`n=== Шаг 7: Установка Ollama ===" -ForegroundColor Green
Invoke-SSHCommand "curl -fsSL https://ollama.com/install.sh | sh" "Установка Ollama"

# Шаг 8: Настройка Ollama для сетевого доступа
Write-Host "`n=== Шаг 8: Настройка Ollama ===" -ForegroundColor Green
$ollamaConfig = @"
sudo mkdir -p /etc/systemd/system/ollama.service.d && \
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf && \
echo 'Environment=\"OLLAMA_HOST=0.0.0.0:11434\"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf && \
sudo systemctl daemon-reload && \
sudo systemctl restart ollama && \
sudo systemctl enable ollama
"@
Invoke-SSHCommand $ollamaConfig "Настройка Ollama сервиса"

# Шаг 9: Настройка файрвола
Write-Host "`n=== Шаг 9: Настройка файрвола ===" -ForegroundColor Green
$firewallCommands = @"
sudo apt install -y ufw && \
sudo ufw allow 22/tcp && \
sudo ufw allow 11434/tcp && \
sudo ufw --force enable && \
sudo ufw status
"@
Invoke-SSHCommand $firewallCommands "Настройка UFW"

Write-Host "`n=== Базовая настройка завершена! ===" -ForegroundColor Green
Write-Host "Сервер требует перезагрузки для применения драйверов NVIDIA" -ForegroundColor Yellow
Write-Host ""
Write-Host "Выполните вручную:" -ForegroundColor Cyan
Write-Host "ssh user@YOUR_LAN_HOST" -ForegroundColor White
Write-Host "sudo reboot" -ForegroundColor White
Write-Host ""
Write-Host "После перезагрузки запустите: .\download-models.ps1" -ForegroundColor Cyan
