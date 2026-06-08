# Configuração de Agendamento Automático de Pagamentos - Windows

Este guia explica como configurar o agendamento automático para verificação de assinaturas vencidas e processamento de pagamentos no Windows.

## 📋 Pré-requisitos

- Windows 10/11 ou Windows Server
- Python instalado e funcionando
- Projeto Django configurado
- Permissões de administrador (para criar tarefas agendadas)

## 🚀 Configuração do Agendador de Tarefas

### Método 1: Interface Gráfica

1. **Abrir o Agendador de Tarefas:**
   - Pressione `Win + R`
   - Digite `taskschd.msc` e pressione Enter

2. **Criar Nova Tarefa:**
   - Clique em "Criar Tarefa Básica" no painel direito
   - Nome: `Verificação Automática de Pagamentos`
   - Descrição: `Verifica assinaturas vencidas e processa pagamentos pendentes`

3. **Configurar Gatilho:**
   - Escolha "Diariamente"
   - Horário: `09:00` (ou horário desejado)
   - Repetir a cada: `30 minutos` por `24 horas`

4. **Configurar Ação:**
   - Ação: "Iniciar um programa"
   - Programa: `powershell.exe`
   - Argumentos: `-ExecutionPolicy Bypass -File "C:\Users\Cliente\Desktop\sistema imo\automatizar_pagamentos.ps1"`
   - Iniciar em: `C:\Users\Cliente\Desktop\sistema imo`

### Método 2: Linha de Comando (PowerShell como Administrador)

```powershell
# Criar tarefa para verificação diária às 9h
schtasks /create /tn "Verificacao Assinaturas Diaria" /tr "powershell.exe -ExecutionPolicy Bypass -File 'C:\Users\Cliente\Desktop\sistema imo\automatizar_pagamentos.ps1'" /sc daily /st 09:00 /ru SYSTEM

# Criar tarefa para verificação a cada 30 minutos
schtasks /create /tn "Processamento Pagamentos 30min" /tr "powershell.exe -ExecutionPolicy Bypass -File 'C:\Users\Cliente\Desktop\sistema imo\automatizar_pagamentos.ps1'" /sc minute /mo 30 /ru SYSTEM
```

## ⚙️ Configurações Recomendadas

### Frequências Sugeridas:

1. **Verificação de Assinaturas Vencidas:**
   - Frequência: 1x por dia às 9h
   - Comando: Incluído no script principal

2. **Processamento de Pagamentos:**
   - Frequência: A cada 30 minutos (horário comercial)
   - Comando: Incluído no script principal

3. **Verificação de Trials:**
   - Frequência: 1x por dia às 10h
   - Comando: Incluído no script principal

### Configuração de Horários Específicos:

```powershell
# Apenas horário comercial (8h às 18h)
schtasks /create /tn "Pagamentos Comercial" /tr "powershell.exe -ExecutionPolicy Bypass -File 'C:\Users\Cliente\Desktop\sistema imo\automatizar_pagamentos.ps1'" /sc minute /mo 30 /st 08:00 /et 18:00 /ru SYSTEM
```

## 📊 Monitoramento

### Verificar Logs:
```powershell
# Ver últimas execuções
Get-Content "C:\Users\Cliente\Desktop\sistema imo\logs\pagamentos_automaticos.log" -Tail 50

# Monitorar em tempo real
Get-Content "C:\Users\Cliente\Desktop\sistema imo\logs\pagamentos_automaticos.log" -Wait
```

### Verificar Status das Tarefas:
```powershell
# Listar tarefas relacionadas
schtasks /query /tn "*Pagamentos*" /fo table

# Ver histórico de execução
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=200,201} | Where-Object {$_.Message -like "*Pagamentos*"} | Select-Object TimeCreated, Message
```

## 🔧 Comandos Úteis

### Gerenciar Tarefas:
```powershell
# Executar tarefa manualmente
schtasks /run /tn "Verificacao Assinaturas Diaria"

# Parar tarefa
schtasks /end /tn "Verificacao Assinaturas Diaria"

# Desabilitar tarefa
schtasks /change /tn "Verificacao Assinaturas Diaria" /disable

# Habilitar tarefa
schtasks /change /tn "Verificacao Assinaturas Diaria" /enable

# Deletar tarefa
schtasks /delete /tn "Verificacao Assinaturas Diaria" /f
```

### Teste Manual:
```powershell
# Executar script manualmente
cd "C:\Users\Cliente\Desktop\sistema imo"
powershell.exe -ExecutionPolicy Bypass -File "automatizar_pagamentos.ps1"
```

## 🚨 Solução de Problemas

### Problemas Comuns:

1. **Erro de Política de Execução:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Caminho do Python não encontrado:**
   - Edite o script e defina o caminho completo:
   ```powershell
   $PYTHON_PATH = "C:\Python39\python.exe"  # Exemplo
   ```

3. **Permissões insuficientes:**
   - Execute o PowerShell como Administrador
   - Configure a tarefa para executar como SYSTEM

4. **Ambiente virtual não ativado:**
   - Verifique se o caminho `.venv\Scripts\Activate.ps1` está correto
   - Ou configure o caminho completo do Python no ambiente virtual

### Logs de Debug:
```powershell
# Habilitar logs detalhados no script
$VerbosePreference = "Continue"
```

## 📈 Monitoramento Avançado

### Criar Alerta por Email (Opcional):
```powershell
# Adicionar ao final do script automatizar_pagamentos.ps1
if ($LASTEXITCODE -ne 0) {
    # Enviar email de erro (configure SMTP)
    Send-MailMessage -To "admin@empresa.com" -From "sistema@empresa.com" -Subject "Erro no processamento de pagamentos" -Body "Verifique os logs" -SmtpServer "smtp.empresa.com"
}
```

### Dashboard de Status:
- Acesse: `http://localhost:8000/admin/`
- Verifique seção de pagamentos e assinaturas
- Monitore logs de transações

## ✅ Verificação Final

1. ✅ Script PowerShell criado
2. ✅ Tarefa agendada configurada
3. ✅ Logs sendo gerados
4. ✅ Teste manual executado com sucesso
5. ✅ Monitoramento configurado

---

**Nota:** Ajuste os horários e frequências conforme suas necessidades específicas. Para ambientes de produção, considere usar um serviço de monitoramento mais robusto.