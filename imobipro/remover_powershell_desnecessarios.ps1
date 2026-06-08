# Script para remover arquivos PowerShell desnecessarios
Write-Host "Removendo scripts PowerShell desnecessarios..." -ForegroundColor Green

# Lista de scripts para remover
$scriptsParaRemover = @(
    "diagnosticar_evolution_corrigido.ps1",
    "gerenciar_instancias_v2.ps1", 
    "teste_manual.ps1",
    "teste_mensagem.ps1",
    "diagnostico_simples.ps1",
    "remover_wavoip_token.ps1",
    "resetar_evolution_api.ps1"
)

$removidos = 0
foreach ($script in $scriptsParaRemover) {
    if (Test-Path $script) {
        Write-Host "  [X] Removendo: $script" -ForegroundColor Red
        Remove-Item $script -Force
        $removidos++
    } else {
        Write-Host "  [!] Nao encontrado: $script" -ForegroundColor Yellow
    }
}

Write-Host "`nLimpeza concluida! $removidos arquivos removidos." -ForegroundColor Green
Write-Host "`nScripts mantidos (uteis):" -ForegroundColor Cyan
Write-Host "  - diagnosticar_evolution.ps1" -ForegroundColor White
Write-Host "  - gerenciar_instancias.ps1" -ForegroundColor White  
Write-Host "  - criar_instancia_simples.ps1" -ForegroundColor White
Write-Host "  - iniciar_evolution.ps1" -ForegroundColor White
Write-Host "  - limpar_projeto.ps1" -ForegroundColor White