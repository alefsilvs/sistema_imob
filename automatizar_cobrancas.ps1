# Script PowerShell para automatizar cobranças de aluguel/IPTU em atraso via WhatsApp
# Execute este script periodicamente usando o Agendador de Tarefas do Windows

param(
    [switch]$DryRun
)

# Configurações
$PROJETO_PATH = "C:\Users\Cliente\Desktop\sistema imo"
$PYTHON_PATH = "python"
$LOG_FILE = "$PROJETO_PATH\logs\cobrancas_automaticas.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

if (!(Test-Path "$PROJETO_PATH\logs")) {
    New-Item -ItemType Directory -Path "$PROJETO_PATH\logs" -Force | Out-Null
}

Write-Log "=== Iniciando cobranças automáticas (WhatsApp) ==="

Set-Location $PROJETO_PATH

if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Log "Ativando ambiente virtual..."
    & ".venv\Scripts\Activate.ps1"
}

try {
    Write-Log "Aplicando migrações (se houver)..."
    $migrate = & $PYTHON_PATH manage.py migrate --noinput 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERRO no migrate: $migrate"
    }

    $cmdArgs = @("manage.py", "enviar_cobrancas_atraso")
    if ($DryRun) {
        $cmdArgs += "--dry-run"
        Write-Log "Modo DRY-RUN ativo (não envia WhatsApp)."
    }

    Write-Log "Executando: python $($cmdArgs -join ' ')"
    $result = & $PYTHON_PATH @cmdArgs 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Cobranças executadas com sucesso"
        Write-Log "$result"
    } else {
        Write-Log "ERRO ao executar cobranças: $result"
    }
} catch {
    Write-Log "ERRO GERAL: $($_.Exception.Message)"
} finally {
    Write-Log "=== Cobranças automáticas finalizadas ==="
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
            $true
        }
    }
    $logContent | Set-Content $LOG_FILE
}

