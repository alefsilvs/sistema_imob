# Script para gerenciar instâncias Evolution API
$baseUrl = "http://localhost:8080"
$apiKey = "F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5"

# Função para imprimir com menos conflitos
function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

try {
    Write-Status "Listando instâncias..." "Yellow"
    $response = Invoke-WebRequest -Uri "$baseUrl/instance/fetchInstances" -Method GET -Headers @{"apikey"=$apiKey}
    $instances = $response.Content | ConvertFrom-Json
    
    if ($instances.Count -gt 0) {
        Write-Status "Encontradas $($instances.Count) instâncias" "Cyan"
        
        # Deletar instâncias existentes
        foreach ($instance in $instances) {
            try {
                Invoke-WebRequest -Uri "$baseUrl/instance/delete/$($instance.id)" -Method DELETE -Headers @{"apikey"=$apiKey} | Out-Null
                Write-Status "Deletada: $($instance.name)" "Green"
            }
            catch {
                Write-Status "Erro ao deletar $($instance.name): $($_.Exception.Message)" "Red"
            }
        }
    }
    
    # Criar nova instância
    $newInstanceName = "whatsapp-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Status "Criando: $newInstanceName" "Green"
    
    $createResponse = Invoke-WebRequest -Uri "$baseUrl/instance/create" -Method POST -Headers @{"apikey"=$apiKey} -ContentType "application/json" -Body (@{
        instanceName = $newInstanceName
        token = $apiKey
        qrcode = $true
        number = ""
        webhook_url = ""
    } | ConvertTo-Json)
    
    $result = $createResponse.Content | ConvertFrom-Json
    Write-Status "✅ Instância criada com sucesso!" "Green"
    Write-Status "Nome: $($result.instance.instanceName)" "White"
    Write-Status "Status: $($result.instance.status)" "White"
    
} catch {
    Write-Status "❌ Erro: $($_.Exception.Message)" "Red"
}