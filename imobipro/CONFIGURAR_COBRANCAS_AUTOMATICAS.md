# ⚙️ Cobranças Automáticas (WhatsApp) — Windows

Este guia deixa o robô de cobrança **100% automático** no Windows, usando o Agendador de Tarefas para rodar:

- `python manage.py enviar_cobrancas_atraso`

O script já está pronto:
- `automatizar_cobrancas.ps1`

## ✅ 1) Pré-requisito (uma vez)

Execute as migrações:

```powershell
cd "C:\Users\Cliente\Desktop\sistema imo"
python manage.py migrate
```

## ✅ 2) Teste manual

Simular (não envia WhatsApp):

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Cliente\Desktop\sistema imo\automatizar_cobrancas.ps1" -DryRun
```

Enviar de verdade:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Cliente\Desktop\sistema imo\automatizar_cobrancas.ps1"
```

Logs:
- `logs\cobrancas_automaticas.log`

## ✅ 3) Criar tarefa automática (recomendado)

### Opção A — 1x por dia (09:00)

```powershell
schtasks /create /tn "ImobiPro - Cobranças WhatsApp" /tr "powershell.exe -ExecutionPolicy Bypass -File \"C:\Users\Cliente\Desktop\sistema imo\automatizar_cobrancas.ps1\"" /sc daily /st 09:00
```

### Opção B — 2x por dia (09:00 e 16:00)

Crie duas tarefas:

```powershell
schtasks /create /tn "ImobiPro - Cobranças WhatsApp (09h)" /tr "powershell.exe -ExecutionPolicy Bypass -File \"C:\Users\Cliente\Desktop\sistema imo\automatizar_cobrancas.ps1\"" /sc daily /st 09:00
schtasks /create /tn "ImobiPro - Cobranças WhatsApp (16h)" /tr "powershell.exe -ExecutionPolicy Bypass -File \"C:\Users\Cliente\Desktop\sistema imo\automatizar_cobrancas.ps1\"" /sc daily /st 16:00
```

## 🔧 Operação

Listar tarefas:

```powershell
schtasks /query /tn "ImobiPro - Cobranças WhatsApp" /fo LIST /v
```

Remover tarefa:

```powershell
schtasks /delete /tn "ImobiPro - Cobranças WhatsApp" /f
```

## 🧩 Ajustar regra por empresa (Tenant)

No `Tenant.configuracoes`:

```json
{
  "cobranca_whatsapp": {
    "ativo": true,
    "dias": [1, 5, 10, 20],
    "max_por_execucao": 200,
    "incluir_iptu_parcelado": true,
    "incluir_iptu_no_aluguel": true
  }
}
```

