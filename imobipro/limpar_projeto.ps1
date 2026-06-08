# Script de Limpeza do Projeto
Write-Host "🧹 Iniciando limpeza do projeto..." -ForegroundColor Green

# 1. Remover arquivos de cache Python
Write-Host "Removendo arquivos __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Recurse -Directory -Name "__pycache__" | ForEach-Object {
    $path = Join-Path -Path "." -ChildPath $_
    Write-Host "  Removendo: $path" -ForegroundColor Gray
    Remove-Item -Path $path -Recurse -Force
}

# 2. Remover scripts PowerShell duplicados (manter apenas as versões principais)
Write-Host "Removendo scripts duplicados..." -ForegroundColor Yellow
$scriptsToRemove = @(
    "diagnosticar_evolution_corrigido.ps1",
    "gerenciar_instancias_corrigido.ps1",
    "gerenciar_instancias_debug.ps1",
    "gerenciar_instancias_definitivo.ps1",
    "gerenciar_instancias_final.ps1",
    "gerenciar_instancias_fixed.ps1",
    "gerenciar_instancias_minimo.ps1"
)

foreach ($script in $scriptsToRemove) {
    if (Test-Path $script) {
        Write-Host "  Removendo: $script" -ForegroundColor Gray
        Remove-Item $script -Force
    }
}

# 3. Remover arquivos de configuração duplicados na raiz
Write-Host "Removendo arquivos de configuração duplicados..." -ForegroundColor Yellow
$configsToRemove = @("package.json", "package-lock.json", "yarn.lock")
foreach ($config in $configsToRemove) {
    if (Test-Path $config) {
        Write-Host "  Removendo: $config" -ForegroundColor Gray
        Remove-Item $config -Force
    }
}

# 4. Limpar logs antigos (opcional)
Write-Host "Limpando logs antigos..." -ForegroundColor Yellow
if (Test-Path "logs\nfe.log") {
    $logSize = (Get-Item "logs\nfe.log").Length
    if ($logSize -gt 10MB) {
        Write-Host "  Log muito grande ($([math]::Round($logSize/1MB, 2)) MB), truncando..." -ForegroundColor Gray
        Clear-Content "logs\nfe.log"
    }
}

Write-Host "✅ Limpeza concluída!" -ForegroundColor Green
Write-Host "📊 Espaço liberado: Verifique o tamanho da pasta antes e depois" -ForegroundColor Cyan