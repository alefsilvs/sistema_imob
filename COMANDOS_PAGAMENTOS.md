# Comandos para Gerenciamento de Pagamentos

Este documento lista todos os comandos disponíveis para gerenciar pagamentos e assinaturas no sistema.

## 🚀 Comandos Django Criados

### 1. Verificar Assinaturas Vencidas

```bash
# Executar verificação (modo produção)
python manage.py verificar_assinaturas_vencidas

# Executar em modo teste (sem fazer alterações)
python manage.py verificar_assinaturas_vencidas --dry-run

# Configurar dias de antecedência para notificações
python manage.py verificar_assinaturas_vencidas --dias-antecedencia 7

# Exemplo completo
python manage.py verificar_assinaturas_vencidas --dry-run --dias-antecedencia 5
```

**O que faz:**
- Verifica assinaturas vencidas
- Processa renovações automáticas
- Cancela assinaturas sem renovação
- Envia notificações de vencimento

### 2. Processar Pagamentos Pendentes

```bash
# Executar processamento (modo produção)
python manage.py processar_pagamentos_pendentes

# Executar em modo teste (sem fazer alterações)
python manage.py processar_pagamentos_pendentes --dry-run

# Configurar timeout personalizado (em horas)
python manage.py processar_pagamentos_pendentes --timeout-horas 48

# Processar apenas um tipo de pagamento
python manage.py processar_pagamentos_pendentes --gateway PIX
python manage.py processar_pagamentos_pendentes --gateway CARTAO
python manage.py processar_pagamentos_pendentes --gateway BOLETO

# Exemplo completo
python manage.py processar_pagamentos_pendentes --dry-run --timeout-horas 24 --gateway PIX
```

**O que faz:**
- Verifica status de pagamentos pendentes
- Consulta gateways de pagamento
- Atualiza status (aprovado/rejeitado)
- Cancela pagamentos em timeout

## 🤖 Automação com PowerShell

### Executar Script de Automação

```powershell
# Executar uma vez
powershell.exe -ExecutionPolicy Bypass -File "automatizar_pagamentos.ps1"

# Executar em modo administrador
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File 'automatizar_pagamentos.ps1'" -Verb RunAs
```

### Testar Script

```powershell
# Navegar para o diretório
cd "C:\Users\Cliente\Desktop\sistema imo"

# Executar script
.\automatizar_pagamentos.ps1

# Ver logs em tempo real
Get-Content "logs\pagamentos_automaticos.log" -Wait
```

## 📊 Monitoramento

### Verificar Logs

```bash
# Ver logs do Django
tail -f logs/nfe.log

# Ver logs do PowerShell
Get-Content "logs\pagamentos_automaticos.log" -Tail 50

# Filtrar logs por data
Get-Content "logs\pagamentos_automaticos.log" | Where-Object {$_ -match "2025-09-09"}
```

### Status do Sistema

```bash
# Verificar assinaturas ativas
python manage.py shell -c "from assinaturas.models import AssinaturaUsuario; print(f'Ativas: {AssinaturaUsuario.objects.filter(status=\"ATIVA\").count()}')"

# Verificar pagamentos pendentes
python manage.py shell -c "from pagamentos.models import PagamentoOnline; print(f'Pendentes: {PagamentoOnline.objects.filter(status=\"PENDENTE\").count()}')"

# Verificar trials expirando
python manage.py shell -c "from django.utils import timezone; from datetime import timedelta; from saas.models import Tenant; data_limite = timezone.now().date() + timedelta(days=3); print(f'Trials expirando: {Tenant.objects.filter(data_expiracao_trial__lte=data_limite, status=\"TRIAL\").count()}')"
```

## ⚙️ Configuração de Produção

### Variáveis de Ambiente

```bash
# Configurar no .env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configurações de pagamento
PIX_PROVIDER_URL=https://api.provedor.com
PIX_API_KEY=sua_chave_aqui
CARTAO_PROVIDER_URL=https://api.cartao.com
CARTAO_API_KEY=sua_chave_cartao
```

### Celery (Alternativa ao PowerShell)

```bash
# Instalar Celery
pip install celery redis

# Iniciar worker
celery -A sistema_imobiliario worker --loglevel=info

# Iniciar beat (agendador)
celery -A sistema_imobiliario beat --loglevel=info

# Monitorar tarefas
celery -A sistema_imobiliario flower
```

## 🔧 Solução de Problemas

### Problemas Comuns

1. **Comando não encontrado:**
   ```bash
   # Verificar se o comando existe
   python manage.py help
   
   # Listar comandos disponíveis
   python manage.py help | grep -E "verificar|processar"
   ```

2. **Erro de permissão no PowerShell:**
   ```powershell
   # Alterar política de execução
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   
   # Ou executar com bypass
   powershell.exe -ExecutionPolicy Bypass -File "script.ps1"
   ```

3. **Erro de timezone:**
   ```python
   # No settings.py, verificar:
   USE_TZ = True
   TIME_ZONE = 'America/Sao_Paulo'
   ```

4. **Erro de conexão com gateway:**
   ```bash
   # Verificar conectividade
   curl -I https://api.gateway.com
   
   # Testar credenciais
   python manage.py shell -c "from pagamentos.utils import testar_conexao_gateway; testar_conexao_gateway()"
   ```

### Debug Avançado

```bash
# Executar com debug detalhado
python manage.py verificar_assinaturas_vencidas --verbosity=2

# Executar com profiling
python -m cProfile manage.py processar_pagamentos_pendentes

# Verificar queries SQL
python manage.py shell -c "from django.db import connection; from django.conf import settings; settings.DEBUG = True; # executar comando; print(connection.queries)"
```

## 📈 Métricas e Relatórios

### Relatório Diário

```bash
# Criar script de relatório diário
cat > relatorio_diario.py << 'EOF'
from django.utils import timezone
from datetime import timedelta
from assinaturas.models import AssinaturaUsuario
from pagamentos.models import PagamentoOnline

hoje = timezone.now().date()
ontem = hoje - timedelta(days=1)

print(f"=== RELATÓRIO DIÁRIO - {hoje} ===")
print(f"Assinaturas ativas: {AssinaturaUsuario.objects.filter(status='ATIVA').count()}")
print(f"Pagamentos aprovados hoje: {PagamentoOnline.objects.filter(status='APROVADO', data_pagamento__date=hoje).count()}")
print(f"Pagamentos pendentes: {PagamentoOnline.objects.filter(status='PENDENTE').count()}")
EOF

python manage.py shell < relatorio_diario.py
```

### Dashboard de Status

```bash
# Acessar admin Django
# http://localhost:8000/admin/

# Ou criar view personalizada
python manage.py shell -c "
from django.db.models import Count
from pagamentos.models import PagamentoOnline
status_count = PagamentoOnline.objects.values('status').annotate(count=Count('status'))
for item in status_count:
    print(f'{item[\"status\"]}: {item[\"count\"]}')
"
```

---

**Nota:** Sempre teste os comandos em modo `--dry-run` antes de executar em produção!