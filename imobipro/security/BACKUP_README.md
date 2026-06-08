# Sistema de Backup Automático

Este documento descreve o sistema de backup automático implementado para proteger os dados do sistema imobiliário.

## Visão Geral

O sistema de backup oferece:
- Backups automáticos agendados
- Múltiplos tipos de backup (banco de dados, mídia, logs, completo)
- Limpeza automática de backups antigos
- Notificações por email
- Restauração de backups
- Integração com Celery ou cron jobs

## Componentes

### 1. BackupManager (`security/backup.py`)
Classe principal que gerencia todas as operações de backup:
- Criação de backups
- Limpeza de arquivos antigos
- Restauração
- Status e monitoramento

### 2. Comandos de Gerenciamento

#### `backup_system`
```bash
# Backup completo
python manage.py backup_system --type full

# Backup apenas do banco de dados
python manage.py backup_system --type database

# Backup com notificação por email
python manage.py backup_system --type full --notify

# Limpeza de backups antigos
python manage.py backup_system --cleanup

# Status dos backups
python manage.py backup_system --status
```

#### `restore_backup`
```bash
# Listar backups disponíveis
python manage.py restore_backup --list

# Restaurar backup específico
python manage.py restore_backup --file backup_20240101_020000.tar.gz

# Restaurar apenas banco de dados
python manage.py restore_backup --file backup_20240101_020000.tar.gz --type database
```

#### `setup_backup_schedule`
```bash
# Habilitar agendamento diário às 2:00
python manage.py setup_backup_schedule --enable --frequency daily --time 02:00

# Configurar tipos de backup
python manage.py setup_backup_schedule --types full database

# Configurar notificações
python manage.py setup_backup_schedule --notification-emails admin@exemplo.com

# Mostrar configuração atual
python manage.py setup_backup_schedule --show-config

# Resetar para configurações padrão
python manage.py setup_backup_schedule --reset
```

### 3. Agendamento Automático

#### Com Celery (Recomendado)
O sistema usa Celery para agendamento automático quando disponível:
- Tarefas periódicas configuráveis
- Execução em background
- Monitoramento de falhas

#### Com Cron Jobs
Para sistemas sem Celery, use o script `security/cron_backup.py`:

```bash
# Gerar exemplos de configuração
python security/cron_backup.py --crontab-examples

# Adicionar ao crontab
crontab -e

# Exemplos de configuração:
# Backup completo diário às 2:00
0 2 * * * /usr/bin/python3 /path/to/projeto/security/cron_backup.py --type full

# Backup de banco a cada 6 horas
0 */6 * * * /usr/bin/python3 /path/to/projeto/security/cron_backup.py --type database

# Limpeza semanal
0 3 * * 0 /usr/bin/python3 /path/to/projeto/security/cron_backup.py --cleanup
```

## Tipos de Backup

### 1. Database (banco de dados)
- Exporta dados do PostgreSQL/MySQL/SQLite
- Arquivo SQL comprimido
- Rápido e eficiente

### 2. Media (arquivos de mídia)
- Backup de arquivos uploadados
- Imagens, documentos, etc.
- Preserva estrutura de diretórios

### 3. Logs (arquivos de log)
- Backup de logs do sistema
- Logs de auditoria
- Logs de aplicação

### 4. Full (completo)
- Inclui banco de dados + mídia + logs
- Backup completo do sistema
- Recomendado para backups diários

## Configuração

### Configurações no Banco de Dados
As configurações são armazenadas na tabela `SystemSetting`:

```python
# Agendamento
backup_schedule = {
    "enabled": True,
    "frequency": "daily",  # daily, weekly, monthly
    "time": "02:00",
    "types": ["full"]
}

# Configurações gerais
max_backups = 30  # Número máximo de backups
backup_directory = "/path/to/backups"  # Diretório de backup

# Notificações
backup_notifications = {
    "enabled": True,
    "emails": ["admin@exemplo.com"]
}
```

### Configurações no settings.py
```python
# Configurações de backup
BACKUP_SETTINGS = {
    'BACKUP_DIR': 'backups/',
    'MAX_BACKUPS': 30,
    'COMPRESS_BACKUPS': True,
    'ENCRYPTION_ENABLED': False,  # Para implementação futura
}

# Configurações de email para notificações
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha'
DEFAULT_FROM_EMAIL = 'sistema@exemplo.com'
```

## Estrutura de Arquivos de Backup

```
backups/
├── backup_20240101_020000.tar.gz
├── backup_20240102_020000.tar.gz
├── manifests/
│   ├── backup_20240101_020000.json
│   └── backup_20240102_020000.json
└── temp/
    └── (arquivos temporários)
```

### Manifesto de Backup
Cada backup inclui um arquivo manifesto com metadados:

```json
{
    "timestamp": "2024-01-01T02:00:00Z",
    "type": "full",
    "files": {
        "database": "database_backup.sql",
        "media": "media_backup.tar",
        "logs": "logs_backup.tar"
    },
    "sizes": {
        "database": 1048576,
        "media": 5242880,
        "logs": 524288
    },
    "checksums": {
        "database": "sha256:abc123...",
        "media": "sha256:def456...",
        "logs": "sha256:ghi789..."
    }
}
```

## Monitoramento e Logs

### Logs de Backup
Todos os backups são registrados em:
- Logs do Django (configurável)
- Arquivo específico: `backup.log`
- Logs do sistema (syslog)

### Notificações
O sistema envia notificações por email para:
- Backup concluído com sucesso
- Falhas no backup
- Limpeza de arquivos antigos
- Erros críticos

### Monitoramento de Status
```bash
# Via comando Django
python manage.py backup_system --status

# Via script cron
python security/cron_backup.py --status
```

## Restauração

### Restauração Completa
```bash
# Listar backups disponíveis
python manage.py restore_backup --list

# Restaurar backup específico
python manage.py restore_backup --file backup_20240101_020000.tar.gz --confirm
```

### Restauração Parcial
```bash
# Apenas banco de dados
python manage.py restore_backup --file backup.tar.gz --type database

# Apenas arquivos de mídia
python manage.py restore_backup --file backup.tar.gz --type media
```

## Segurança

### Proteção de Arquivos
- Backups são comprimidos com tar.gz
- Checksums SHA-256 para verificação de integridade
- Permissões restritas nos arquivos de backup

### Dados Sensíveis
- Campos criptografados são mantidos criptografados no backup
- Senhas e tokens não são incluídos em logs
- Configurações sensíveis são protegidas

## Troubleshooting

### Problemas Comuns

1. **Erro de permissão no diretório de backup**
   ```bash
   # Criar diretório com permissões corretas
   mkdir -p /path/to/backups
   chmod 750 /path/to/backups
   chown user:group /path/to/backups
   ```

2. **Falha na conexão com banco de dados**
   - Verificar configurações de DATABASE_URL
   - Testar conectividade com o banco
   - Verificar permissões do usuário do banco

3. **Espaço em disco insuficiente**
   - Verificar espaço disponível: `df -h`
   - Executar limpeza: `python manage.py backup_system --cleanup`
   - Ajustar configuração de max_backups

4. **Falha no envio de emails**
   - Verificar configurações SMTP
   - Testar conectividade com servidor de email
   - Verificar logs de email do Django

### Logs de Debug
```python
# Habilitar logs detalhados no settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'backup_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'backup_debug.log',
        },
    },
    'loggers': {
        'security.backup': {
            'handlers': ['backup_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Manutenção

### Verificação Regular
- Testar restauração mensalmente
- Verificar integridade dos backups
- Monitorar espaço em disco
- Revisar logs de backup

### Atualizações
- Manter dependências atualizadas
- Revisar configurações periodicamente
- Testar novos recursos em ambiente de desenvolvimento

## Exemplo de Configuração Completa

```bash
# 1. Configurar agendamento
python manage.py setup_backup_schedule \
    --enable \
    --frequency daily \
    --time 02:00 \
    --types full \
    --max-backups 30 \
    --backup-dir /var/backups/sistema_imobiliario \
    --notification-emails admin@exemplo.com suporte@exemplo.com

# 2. Testar backup manual
python manage.py backup_system --type full --notify

# 3. Verificar status
python manage.py backup_system --status

# 4. Configurar cron como backup (opcional)
python security/cron_backup.py --crontab-examples
```

Este sistema garante a proteção completa dos dados do sistema imobiliário com backups automáticos, monitoramento e facilidade de restauração.