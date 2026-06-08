# Variáveis de Ambiente - Sistema Imobiliário

Este documento lista todas as variáveis de ambiente necessárias para configurar o sistema em produção.

## 📋 Arquivo .env de Produção

Crie o arquivo `/home/imobiliario/sistema-imobiliario/.env` com as seguintes variáveis:

```bash
# ============================================
# CONFIGURAÇÕES GERAIS
# ============================================

# Ambiente de execução
ENVIRONMENT=production
DEBUG=False

# Chave secreta do Django (GERAR UMA NOVA!)
SECRET_KEY=sua_chave_secreta_super_segura_aqui_com_50_caracteres

# Hosts permitidos (separados por vírgula)
ALLOWED_HOSTS=seudominio.com.br,www.seudominio.com.br,127.0.0.1,localhost

# URL base do site
SITE_URL=https://seudominio.com.br

# ============================================
# BANCO DE DADOS POSTGRESQL
# ============================================

DB_ENGINE=django.db.backends.postgresql
DB_NAME=sistema_imobiliario
DB_USER=imobiliario_user
DB_PASSWORD=senha_super_segura_do_banco
DB_HOST=localhost
DB_PORT=5432

# Configurações avançadas do PostgreSQL
DB_CONN_MAX_AGE=600
DB_OPTIONS_sslmode=prefer
DB_OPTIONS_connect_timeout=10
DB_OPTIONS_application_name=sistema_imobiliario

# ============================================
# CONFIGURAÇÕES DE EMAIL
# ============================================

# Backend de email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Servidor SMTP
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Credenciais do email
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app_do_gmail

# Email padrão do sistema
DEFAULT_FROM_EMAIL=Sistema Imobiliário <seu_email@gmail.com>
SERVER_EMAIL=servidor@seudominio.com.br

# Configurações específicas
EMAIL_TIMEOUT=30
EMAIL_SSL_KEYFILE=
EMAIL_SSL_CERTFILE=

# ============================================
# EVOLUTION API (WHATSAPP)
# ============================================

# URL da Evolution API
EVOLUTION_API_URL=http://localhost:8080

# Chave de API da Evolution
EVOLUTION_API_KEY=sua_chave_da_evolution_api

# Nome da instância do WhatsApp
EVOLUTION_INSTANCE_NAME=sistema_imobiliario

# Webhook para receber mensagens
EVOLUTION_WEBHOOK_URL=https://seudominio.com.br/webhook/whatsapp/

# Token de segurança do webhook
EVOLUTION_WEBHOOK_TOKEN=token_seguro_para_webhook

# Configurações de timeout
EVOLUTION_TIMEOUT=30
EVOLUTION_MAX_RETRIES=3

# ============================================
# REDIS (CACHE E SESSÕES)
# ============================================

# URL do Redis
REDIS_URL=redis://localhost:6379/0

# Configurações específicas
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Cache
CACHE_REDIS_DB=1
CACHE_TIMEOUT=3600

# Sessões
SESSION_REDIS_DB=2
SESSION_COOKIE_AGE=86400

# ============================================
# CELERY (TAREFAS ASSÍNCRONAS)
# ============================================

# Broker do Celery (Redis)
CELERY_BROKER_URL=redis://localhost:6379/3

# Backend de resultados
CELERY_RESULT_BACKEND=redis://localhost:6379/4

# Configurações de timeout
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600

# Configurações de retry
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_DEFAULT_RETRY_DELAY=60

# ============================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# ============================================

# Diretório de arquivos estáticos
STATIC_ROOT=/home/imobiliario/sistema-imobiliario/staticfiles
STATIC_URL=/static/

# Diretório de arquivos de mídia
MEDIA_ROOT=/home/imobiliario/sistema-imobiliario/media
MEDIA_URL=/media/

# Tamanho máximo de upload (em bytes)
FILE_UPLOAD_MAX_MEMORY_SIZE=10485760
DATA_UPLOAD_MAX_MEMORY_SIZE=10485760
FILE_UPLOAD_PERMISSIONS=0o644

# ============================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================

# HTTPS
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Cookies seguros
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True

# HSTS
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Referrer Policy
SECURE_REFERRER_POLICY=strict-origin-when-cross-origin

# ============================================
# LOGGING
# ============================================

# Nível de log
LOG_LEVEL=INFO

# Diretório de logs
LOG_DIR=/var/log/sistema-imobiliario

# Tamanho máximo dos arquivos de log (em MB)
LOG_MAX_SIZE=10

# Número de arquivos de backup
LOG_BACKUP_COUNT=5

# ============================================
# MONITORAMENTO
# ============================================

# Sentry (opcional)
SENTRY_DSN=https://sua_chave_do_sentry@sentry.io/projeto
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0

# ============================================
# BACKUP
# ============================================

# Diretório de backup
BACKUP_DIR=/var/backups/sistema-imobiliario

# Retenção de backups (em dias)
BACKUP_RETENTION_DAYS=30

# Compressão de backup
BACKUP_COMPRESSION=gzip

# ============================================
# CONFIGURAÇÕES DE PERFORMANCE
# ============================================

# Timeout de conexão
CONNECTION_TIMEOUT=30

# Pool de conexões
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Cache de templates
TEMPLATE_CACHE=True

# ============================================
# CONFIGURAÇÕES ESPECÍFICAS DO SISTEMA
# ============================================

# Configurações de notificação
NOTIFICACAO_MAX_TENTATIVAS=3
NOTIFICACAO_INTERVALO_RETRY=300

# Configurações de imóveis
IMAGENS_POR_IMOVEL=20
TAMANHO_MAX_IMAGEM=5242880

# Configurações de relatórios
RELATORIO_TIMEOUT=300
RELATORIO_MAX_REGISTROS=10000

# ============================================
# CONFIGURAÇÕES DE TERCEIROS
# ============================================

# Google Maps (se usado)
GOOGLE_MAPS_API_KEY=sua_chave_do_google_maps

# reCAPTCHA (se usado)
RECAPTCHA_PUBLIC_KEY=sua_chave_publica_recaptcha
RECAPTCHA_PRIVATE_KEY=sua_chave_privada_recaptcha

# Analytics (se usado)
GOOGLE_ANALYTICS_ID=UA-XXXXXXXX-X

# ============================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO (REMOVER EM PRODUÇÃO)
# ============================================

# Apenas para desenvolvimento - REMOVER EM PRODUÇÃO
# DEBUG_TOOLBAR=False
# DJANGO_EXTENSIONS=False
```

## 🔐 Gerando Chaves Seguras

### Secret Key do Django
```bash
# Gerar uma nova secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Senhas Seguras
```bash
# Gerar senha aleatória
openssl rand -base64 32

# Ou usando Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📁 Estrutura de Diretórios

Certifique-se de que os seguintes diretórios existam:

```bash
# Criar diretórios necessários
sudo mkdir -p /var/log/sistema-imobiliario
sudo mkdir -p /var/backups/sistema-imobiliario
sudo mkdir -p /home/imobiliario/sistema-imobiliario/staticfiles
sudo mkdir -p /home/imobiliario/sistema-imobiliario/media

# Definir permissões
sudo chown -R imobiliario:imobiliario /var/log/sistema-imobiliario
sudo chown -R imobiliario:imobiliario /var/backups/sistema-imobiliario
sudo chown -R imobiliario:imobiliario /home/imobiliario/sistema-imobiliario

# Definir permissões de acesso
sudo chmod 755 /var/log/sistema-imobiliario
sudo chmod 755 /var/backups/sistema-imobiliario
sudo chmod 755 /home/imobiliario/sistema-imobiliario/staticfiles
sudo chmod 755 /home/imobiliario/sistema-imobiliario/media
```

## 🔧 Configurações Específicas por Ambiente

### Desenvolvimento Local
```bash
ENVIRONMENT=development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### Staging/Teste
```bash
ENVIRONMENT=staging
DEBUG=False
ALLOWED_HOSTS=staging.seudominio.com.br
SECURE_SSL_REDIRECT=True
SENTRY_ENVIRONMENT=staging
```

### Produção
```bash
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=seudominio.com.br,www.seudominio.com.br
SECURE_SSL_REDIRECT=True
SENTRY_ENVIRONMENT=production
```

## 📊 Monitoramento de Variáveis

### Verificar Configurações
```bash
# Verificar se todas as variáveis estão definidas
python manage.py check --deploy

# Testar conexão com banco
python manage.py dbshell

# Testar envio de email
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Teste', 'Mensagem de teste', 'from@example.com', ['to@example.com'])"

# Testar Redis
redis-cli ping

# Testar Evolution API
curl -X GET "$EVOLUTION_API_URL/instance/list" -H "apikey: $EVOLUTION_API_KEY"
```

## 🚨 Segurança

### Permissões do Arquivo .env
```bash
# Definir permissões restritivas
chmod 600 /home/imobiliario/sistema-imobiliario/.env
chown imobiliario:imobiliario /home/imobiliario/sistema-imobiliario/.env
```

### Backup das Configurações
```bash
# Fazer backup do arquivo .env (sem senhas)
cp .env .env.template
# Remover senhas do template
sed -i 's/=.*/=/' .env.template
```

## 📝 Notas Importantes

1. **Nunca commitar o arquivo .env** no controle de versão
2. **Usar senhas diferentes** para cada ambiente
3. **Rotacionar chaves** periodicamente
4. **Monitorar logs** para detectar problemas
5. **Fazer backup** das configurações
6. **Testar todas as integrações** após mudanças
7. **Usar HTTPS** em produção
8. **Configurar firewall** adequadamente
9. **Monitorar recursos** do servidor
10. **Manter sistema atualizado**

## 🔄 Atualizando Configurações

```bash
# Após alterar .env, reiniciar serviços
sudo systemctl restart gunicorn-imobiliario
sudo systemctl restart notificacoes-imobiliario
sudo systemctl restart celery-imobiliario
sudo systemctl restart celerybeat-imobiliario

# Verificar status
sudo systemctl status gunicorn-imobiliario
sudo systemctl status notificacoes-imobiliario

# Ver logs em tempo real
sudo journalctl -u gunicorn-imobiliario -f
```

## 📞 Suporte

Em caso de problemas:
1. Verificar logs do sistema
2. Testar conectividade de rede
3. Validar permissões de arquivos
4. Confirmar configurações de DNS
5. Verificar status dos serviços