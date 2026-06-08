# Script para compilar e iniciar Evolution API
Write-Host "Compilando Evolution API..." -ForegroundColor Yellow
Set-Location "c:\Users\Cliente\Desktop\sistema imo\evolution-api"

# Instalar dependências se necessário
npm install

# Compilar o projeto
npm run build

# Verificar se a compilação foi bem-sucedida
if (Test-Path "dist\main.js") {
    Write-Host "Compilação concluída com sucesso!" -ForegroundColor Green
    Write-Host "Iniciando Evolution API..." -ForegroundColor Yellow
    
    # Iniciar a API
    npm run start:prod
} else {
    Write-Host "Erro na compilação. Verifique os logs acima." -ForegroundColor Red
}