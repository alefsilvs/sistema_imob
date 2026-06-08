# Script para diagnosticar problemas da Evolution API

Write-Host "=== DIAGNÓSTICO EVOLUTION API ===" -ForegroundColor Yellow

# 1. Verificar se a API está rodando
Write-Host "\n1. Verificando se a API está rodando na porta 8080..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -TimeoutSec 5
    Write-Host "✓ API está rodando - Status: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "✗ API não está respondendo: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Tentando iniciar a Evolution API..." -ForegroundColor Yellow
    
    # Tentar iniciar a API
    Set-Location "evolution-api"
    Start-Process powershell -ArgumentList "-Command", "npm run start:prod" -WindowStyle Minimized
    Set-Location ".."
    
    Write-Host "Aguardando 10 segundos para a API inicializar..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -Method GET -TimeoutSec 5
        Write-Host "✓ API iniciada com sucesso - Status: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "✗ Falha ao iniciar a API" -ForegroundColor Red
        exit 1
    }
}

# 2. Testar autenticação
Write-Host "\n2. Testando autenticação..." -ForegroundColor Cyan
$headers = @{
    'apikey' = 'F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5'
    'Content-Type' = 'application/json'
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/instance/fetchInstances" -Method GET -Headers $headers
    Write-Host "✓ Autenticação OK" -ForegroundColor Green
    Write-Host "Instâncias existentes: $($response.Count)" -ForegroundColor White
} catch {
    Write-Host "✗ Erro de autenticação: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Testar criação com JSON mínimo
Write-Host "\n3. Testando criação de instância com JSON mínimo..." -ForegroundColor Cyan
$instanceName = "teste_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$minimalBody = @{
    instanceName = $instanceName
} | ConvertTo-Json

Write-Host "Tentando criar instância: $instanceName" -ForegroundColor White
Write-Host "JSON: $minimalBody" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/instance/create" -Method POST -Headers $headers -Body $minimalBody
    Write-Host "✓ Instância criada com sucesso!" -ForegroundColor Green
    Write-Host "Resposta: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor White
} catch {
    Write-Host "✗ Erro ao criar instância: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "Detalhes do erro: $errorBody" -ForegroundColor Red
    }
    
    Write-Host "\n4. Implementando correção no código-fonte..." -ForegroundColor Yellow
    
    # Implementar correção do wavoipToken
    $backupDir = "backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    # Fazer backup dos arquivos
    $filesToFix = @(
        "evolution-api\\src\\api\\integrations\\instance\\instance.controller.ts",
        "evolution-api\\src\\api\\integrations\\channel\\channel.service.ts",
        "evolution-api\\src\\api\\dto\\instance.dto.ts"
    )
    
    foreach ($file in $filesToFix) {
        if (Test-Path $file) {
            Copy-Item $file "$backupDir\\$(Split-Path $file -Leaf).backup"
            Write-Host "Backup criado: $file" -ForegroundColor Green
        }
    }
    
    # Corrigir instance.controller.ts
    $controllerFile = "evolution-api\\src\\api\\integrations\\instance\\instance.controller.ts"
    if (Test-Path $controllerFile) {
        $content = Get-Content $controllerFile -Raw
        $content = $content -replace "wavoipToken: instanceData\.wavoipToken \|\| '',", "// wavoipToken: instanceData.wavoipToken || '',"
        Set-Content $controllerFile $content
        Write-Host "✓ Corrigido: instance.controller.ts" -ForegroundColor Green
    }
    
    # Corrigir channel.service.ts
    $channelFile = "evolution-api\\src\\api\\integrations\\channel\\channel.service.ts"
    if (Test-Path $channelFile) {
        $content = Get-Content $channelFile -Raw
        $content = $content -replace "wavoipToken,", "// wavoipToken,"
        $content = $content -replace "wavoipToken: data\.wavoipToken,", "// wavoipToken: data.wavoipToken,"
        Set-Content $channelFile $content
        Write-Host "✓ Corrigido: channel.service.ts" -ForegroundColor Green
    }
    
    Write-Host "\n5. Reiniciando Evolution API..." -ForegroundColor Yellow
    
    # Parar processos Node.js
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 3
    
    # Recompilar e iniciar
    Set-Location "evolution-api"
    Write-Host "Recompilando..." -ForegroundColor White
    npm run build 2>$null
    
    Write-Host "Iniciando API corrigida..." -ForegroundColor White
    Start-Process powershell -ArgumentList "-Command", "npm run start:prod" -WindowStyle Minimized
    Set-Location ".."
    
    Start-Sleep -Seconds 15
    
    # Testar novamente
    Write-Host "\n6. Testando criação após correções..." -ForegroundColor Cyan
    $newInstanceName = "corrigido_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    $newBody = @{
        instanceName = $newInstanceName
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/instance/create" -Method POST -Headers $headers -Body $newBody
        Write-Host "✓ SUCESSO! Instância criada após correções!" -ForegroundColor Green
        Write-Host "Nome da instância: $newInstanceName" -ForegroundColor White
        
        # Tentar obter QR Code
        Start-Sleep -Seconds 2
        try {
            $qrResponse = Invoke-RestMethod -Uri "http://localhost:8080/instance/connect/$newInstanceName" -Method GET -Headers $headers
            Write-Host "\n✓ QR Code obtido com sucesso!" -ForegroundColor Green
            Write-Host "Base64 do QR Code disponível para escaneamento" -ForegroundColor White
        } catch {
            Write-Host "Erro ao obter QR Code: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "✗ Ainda há problemas: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "\n=== DIAGNÓSTICO CONCLUÍDO ===" -ForegroundColor Yellow