# Script para testar diferentes tokens da instância sistema_imo
$tokens = @(
    "sistema_imo_token_2024",
    "sistema_imo",
    "sistema_imo_2024",
    "sistema_imo_token",
    "imo_token_2024",
    "sistema_imo_secure_token",
    "sistema_imo_2024_secure_key_789"
)

$baseUrl = "http://localhost:8080"

Write-Host "Testando tokens para a instância sistema_imo..." -ForegroundColor Green

foreach ($token in $tokens) {
    Write-Host "`nTestando token: $token" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/instance/connect/sistema_imo" -Method GET -Headers @{"apikey"=$token} -ErrorAction Stop
        Write-Host "✅ SUCESSO! Token válido: $token" -ForegroundColor Green
        Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
        break
    }
    catch {
        $errorResponse = $_.Exception.Response
        if ($errorResponse.StatusCode -eq 401) {
            Write-Host "❌ Token inválido: $token" -ForegroundColor Red
        } else {
            Write-Host "⚠️ Outro erro com token $token : $($_.Exception.Message)" -ForegroundColor Orange
        }
    }
}

Write-Host "`nTeste concluído." -ForegroundColor Green