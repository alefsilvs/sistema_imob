# Script para criar instância WhatsApp - Versão Mínima
# Apenas campos essenciais para evitar conflitos

# Configurações da API
$apiUrl = "http://localhost:8080"
$apiKey = "F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5"

# Gerar nome único baseado em timestamp
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$instanceName = "whatsapp-$timestamp"

Write-Host "=== CRIANDO INSTANCIA WHATSAPP (MINIMO) ===" -ForegroundColor Green
Write-Host "Nome da instancia: $instanceName" -ForegroundColor Yellow

# Headers da requisição
$headers = @{
    'apikey' = $apiKey
    'Content-Type' = 'application/json'
}

# Corpo da requisição - APENAS campos essenciais
$body = @{
    instanceName = $instanceName
    integration  = "WHATSAPP-BAILEYS"
    qrcode       = $true
} | ConvertTo-Json -Depth 3

Write-Host "Corpo da requisicao (minimo):" -ForegroundColor Cyan
Write-Host $body -ForegroundColor White

try {
    Write-Host "`nCriando instancia..." -ForegroundColor Yellow
    
    # Criar instância
    $response = Invoke-RestMethod -Uri "$apiUrl/instance/create" -Method POST -Headers $headers -Body $body
    
    Write-Host "Instancia criada com sucesso!" -ForegroundColor Green
    Write-Host "Instance Name: $($response.instance.instanceName)" -ForegroundColor White
    Write-Host "Instance ID: $($response.instance.instanceId)" -ForegroundColor White
    
    # Aguardar um pouco para a instância inicializar
    Write-Host "`nAguardando inicializacao da instancia..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Tentar obter QR Code
    Write-Host "Obtendo QR Code..." -ForegroundColor Yellow
    
    try {
        $qrResponse = Invoke-RestMethod -Uri "$apiUrl/instance/connect/$instanceName" -Method GET -Headers $headers
        
        if ($qrResponse.base64) {
            Write-Host "QR Code obtido com sucesso!" -ForegroundColor Green
            Write-Host "Escaneie o QR Code no WhatsApp Web para conectar" -ForegroundColor Cyan
            Write-Host "QR Code (Base64): $($qrResponse.base64.Substring(0,50))..." -ForegroundColor White
            
            # Salvar QR Code em arquivo
            $qrCodeFile = "qrcode_$instanceName.txt"
            $qrResponse.base64 | Out-File -FilePath $qrCodeFile -Encoding UTF8
            Write-Host "QR Code salvo em: $qrCodeFile" -ForegroundColor Green
            
        } else {
            Write-Host "QR Code nao disponivel ainda. Tente novamente em alguns segundos." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Erro ao obter QR Code: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Tente manualmente: Invoke-RestMethod -Uri '$apiUrl/instance/connect/$instanceName' -Method GET -Headers @{'apikey'='$apiKey'}" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "Erro ao criar instancia:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Message -like "*403*") {
        Write-Host "`nErro 403: Nome da instancia ja existe." -ForegroundColor Yellow
        Write-Host "Tente executar o script novamente." -ForegroundColor Yellow
    } elseif ($_.Exception.Message -like "*400*") {
        Write-Host "`nErro 400: Problema com os campos da requisicao." -ForegroundColor Yellow
        Write-Host "Verifique se a versao da Evolution API esta atualizada." -ForegroundColor Yellow
    }
}

Write-Host "`n=== PROCESSO CONCLUIDO ===" -ForegroundColor Green
Write-Host "Para conectar o WhatsApp, escaneie o QR Code gerado." -ForegroundColor Cyan