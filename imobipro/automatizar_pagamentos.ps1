# Script PowerShell para automatizar verificação de assinaturas e pagamentos
# Execute este script periodicamente usando o Agendador de Tarefas do Windows

# Configurações
$PROJETO_PATH = "C:\Users\Cliente\Desktop\sistema imo"
$PYTHON_PATH = "python"  # ou caminho completo se necessário
$LOG_FILE = "$PROJETO_PATH\logs\pagamentos_automaticos.log"

# Função para log
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

# Criar diretório de logs se não existir
if (!(Test-Path "$PROJETO_PATH\logs")) {
    New-Item -ItemType Directory -Path "$PROJETO_PATH\logs" -Force
}

Write-Log "=== Iniciando verificação automática de pagamentos ==="

# Mudar para o diretório do projeto
Set-Location $PROJETO_PATH

# Ativar ambiente virtual se existir
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Log "Ativando ambiente virtual..."
    & ".venv\Scripts\Activate.ps1"
}

try {
    # 1. Verificar assinaturas vencidas
    Write-Log "Verificando assinaturas vencidas..."
    $result1 = & $PYTHON_PATH manage.py verificar_assinaturas_vencidas 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Verificação de assinaturas concluída com sucesso"
        Write-Log "Resultado: $result1"
    } else {
        Write-Log "ERRO na verificação de assinaturas: $result1"
    }

    # 2. Processar pagamentos pendentes
    Write-Log "Processando pagamentos pendentes..."
    $result2 = & $PYTHON_PATH manage.py processar_pagamentos_pendentes 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Processamento de pagamentos concluído com sucesso"
        Write-Log "Resultado: $result2"
    } else {
        Write-Log "ERRO no processamento de pagamentos: $result2"
    }

    # 3. Log de finalização
    Write-Log "Comandos principais executados com sucesso"

} catch {
    Write-Log "ERRO GERAL: $($_.Exception.Message)"
} finally {
    Write-Log "=== Verificação automática finalizada ==="
    Write-Log ""
}

# Manter apenas os últimos 30 dias de logs
$cutoffDate = (Get-Date).AddDays(-30)
if (Test-Path $LOG_FILE) {
    $logContent = Get-Content $LOG_FILE | Where-Object {
        if ($_ -match "\[(\d{4}-\d{2}-\d{2})") {
            $logDate = [DateTime]::ParseExact($matches[1], "yyyy-MM-dd", $null)
            $logDate -gt $cutoffDate
        } else {
            $true  # Manter linhas sem data
        }
    }
    $logContent | Set-Content $LOG_FILE
}