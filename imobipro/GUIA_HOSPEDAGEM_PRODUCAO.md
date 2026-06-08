# Guia Completo de Hospedagem - Sistema Imobiliário

## 📋 Visão Geral

Este guia fornece instruções detalhadas para hospedar o sistema imobiliário em produção, incluindo todas as tecnologias e APIs utilizadas.

## 🛠️ Tecnologias do Sistema

- **Backend**: Django 4.x + Python 3.12
- **Banco de Dados**: SQLite (desenvolvimento) → PostgreSQL (produção)
- **WhatsApp API**: Evolution API
- **Email**: SMTP configurável
- **Frontend**: HTML/CSS/JavaScript + Bootstrap
- **Arquivos Estáticos**: Django Static Files
- **Segurança**: Sistema de proteção customizado

## 🖥️ Opções de Hospedagem Recomendadas

### 1. VPS/Servidor Dedicado (Recomendado)
- **DigitalOcean**: $5-20/mês
- **Linode**: $5-20/mês
- **Vultr**: $5-20/mês
- **AWS EC2**: $10-30/mês
- **Google Cloud**: $10-30/mês

### 2. Hospedagem Compartilhada (Limitada)
- **Heroku**: $7-25/mês (com limitações)
- **PythonAnywhere**: $5-20/mês

## 🐧 Configuração do Servidor (Ubuntu 22.04 LTS)

### Passo 1: Preparação do Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências essenciais
sudo apt install -y python3.12 python3.12-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx
sudo apt install -y git curl wget
sudo apt install -y certbot python3-certbot-nginx
sudo apt install -y supervisor
```

### Passo 2: Configurar Usuário do Sistema

```bash
# Criar usuário para a aplicação
sudo adduser --system --group --home /opt/imobiliario imobiliario
sudo mkdir -p /opt/imobiliario
sudo chown imobiliario:imobiliario /opt/imobiliario
```

### Passo 3: Clonar e Configurar Aplicação

```bash
# Mudar para usuário da aplicação
sudo su - imobiliario

# Clonar repositório (ou fazer upload dos arquivos)
git clone <seu-repositorio> /opt/imobiliario/app
# OU
# Fazer upload via SCP/SFTP para /opt/imobiliario/app

cd /opt/imobiliario/app

# Criar ambiente virtual
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

## 🗄️ Configuração do PostgreSQL

### Passo 1: Configurar Banco de Dados

```bash
# Acessar PostgreSQL
sudo -u postgres psql

-- Criar banco e usuário
CREATE DATABASE sistema_imobiliario;
CREATE USER imobiliario_user WITH PASSWORD 'senha_super_segura_123';
GRANT ALL PRIVILEGES ON DATABASE sistema_imobiliario TO imobiliario_user;
ALTER USER imobiliario_user CREATEDB;
\q
```

### Passo 2: Configurar settings.py para Produção

```python
# Criar arquivo settings_production.py
from .settings import *
import os

# Segurança
DEBUG = False
ALLOWED_HOSTS = ['seu-dominio.com', 'www.seu-dominio.com', 'IP_DO_SERVIDOR']

# Banco de dados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sistema_imobiliario',
        'USER': 'imobiliario_user',
        'PASSWORD': 'senha_super_segura_123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Arquivos estáticos
STATIC_ROOT = '/opt/imobiliario/static/'
MEDIA_ROOT = '/opt/imobiliario/media/'

# Segurança adicional
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

## 🌐 Configuração do Nginx

### Arquivo: /etc/nginx/sites-available/sistema-imobiliario

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Certificados SSL (serão configurados pelo Certbot)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Arquivos estáticos
    location /static/ {
        alias /opt/imobiliario/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /opt/imobiliario/media/;
        expires 30d;
    }
    
    # Aplicação Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Logs
    access_log /var/log/nginx/imobiliario_access.log;
    error_log /var/log/nginx/imobiliario_error.log;
}
```

### Ativar configuração

```bash
sudo ln -s /etc/nginx/sites-available/sistema-imobiliario /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🚀 Configuração do Gunicorn

### Arquivo: /opt/imobiliario/gunicorn.conf.py

```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5
user = "imobiliario"
group = "imobiliario"
tmp_upload_dir = None
logfile = "/opt/imobiliario/logs/gunicorn.log"
loglevel = "info"
access_logfile = "/opt/imobiliario/logs/gunicorn_access.log"
error_logfile = "/opt/imobiliario/logs/gunicorn_error.log"
```

### Arquivo de serviço: /etc/systemd/system/gunicorn-imobiliario.service

```ini
[Unit]
Description=Gunicorn instance to serve Sistema Imobiliario
After=network.target

[Service]
User=imobiliario
Group=imobiliario
WorkingDirectory=/opt/imobiliario/app
Environment="PATH=/opt/imobiliario/app/venv/bin"
EnvironmentFile=/opt/imobiliario/.env
ExecStart=/opt/imobiliario/app/venv/bin/gunicorn --config /opt/imobiliario/gunicorn.conf.py sistema_imobiliario.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 📱 Configuração da Evolution API (WhatsApp)

### Passo 1: Instalar Node.js

```bash
# Instalar Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Passo 2: Configurar Evolution API

```bash
# Clonar Evolution API
cd /opt/imobiliario
git clone https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api

# Instalar dependências
npm install

# Configurar .env
cp .env.example .env
```

### Arquivo: /opt/imobiliario/evolution-api/.env

```env
# Servidor
SERVER_PORT=8080
SERVER_URL=https://seu-dominio.com

# Banco de dados
DATABASE_ENABLED=true
DATABASE_CONNECTION_URI=postgresql://imobiliario_user:senha_super_segura_123@localhost:5432/evolution_api

# Autenticação
AUTHENTICATION_TYPE=apikey
AUTHENTICATION_API_KEY=sua_chave_api_super_segura

# Webhook
WEBHOOK_GLOBAL_URL=https://seu-dominio.com/api/webhook/whatsapp/
WEBHOOK_GLOBAL_ENABLED=true

# Logs
LOG_LEVEL=info
LOG_COLOR=true
```

### Serviço Evolution API: /etc/systemd/system/evolution-api.service

```ini
[Unit]
Description=Evolution API WhatsApp
After=network.target

[Service]
Type=simple
User=imobiliario
WorkingDirectory=/opt/imobiliario/evolution-api
EnvironmentFile=/opt/imobiliario/evolution-api/.env
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🔒 Configuração SSL/HTTPS

```bash
# Obter certificado SSL gratuito
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Configurar renovação automática
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📧 Configuração de Email

### Arquivo: /opt/imobiliario/.env

```env
# Django
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_production
SECRET_KEY=sua_chave_secreta_super_longa_e_segura

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# WhatsApp
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_chave_api_super_segura
WHATSAPP_INSTANCE_NAME=sistema_imobiliario

# Banco de dados
DB_NAME=sistema_imobiliario
DB_USER=imobiliario_user
DB_PASSWORD=senha_super_segura_123
DB_HOST=localhost
DB_PORT=5432
```

## 🚀 Deploy da Aplicação

```bash
# Como usuário imobiliario
sudo su - imobiliario
cd /opt/imobiliario/app
source venv/bin/activate

# Migrar banco de dados
python manage.py migrate --settings=sistema_imobiliario.settings_production

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production

# Criar superusuário
python manage.py createsuperuser --settings=sistema_imobiliario.settings_production

# Criar diretórios necessários
sudo mkdir -p /opt/imobiliario/logs
sudo chown -R imobiliario:imobiliario /opt/imobiliario/
```

## 🔄 Iniciar Serviços

```bash
# Habilitar e iniciar serviços
sudo systemctl enable gunicorn-imobiliario
sudo systemctl enable evolution-api
sudo systemctl enable nginx
sudo systemctl enable postgresql

sudo systemctl start gunicorn-imobiliario
sudo systemctl start evolution-api
sudo systemctl start nginx
sudo systemctl start postgresql

# Verificar status
sudo systemctl status gunicorn-imobiliario
sudo systemctl status evolution-api
sudo systemctl status nginx
```

## 📊 Monitoramento e Logs

```bash
# Logs da aplicação
sudo tail -f /opt/imobiliario/logs/gunicorn.log
sudo tail -f /opt/imobiliario/logs/gunicorn_error.log

# Logs do Nginx
sudo tail -f /var/log/nginx/imobiliario_access.log
sudo tail -f /var/log/nginx/imobiliario_error.log

# Logs do sistema
sudo journalctl -u gunicorn-imobiliario -f
sudo journalctl -u evolution-api -f
```

## 🔧 Manutenção e Backup

### Script de Backup: /opt/imobiliario/backup.sh

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/imobiliario/backups"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump -U imobiliario_user -h localhost sistema_imobiliario > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos de media
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /opt/imobiliario/media/

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

### Cron para backup automático

```bash
sudo crontab -e
# Adicionar:
0 2 * * * /opt/imobiliario/backup.sh >> /opt/imobiliario/logs/backup.log 2>&1
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro 502 Bad Gateway**
   - Verificar se Gunicorn está rodando
   - Verificar logs do Gunicorn
   - Verificar configuração do Nginx

2. **Erro de conexão com banco**
   - Verificar se PostgreSQL está rodando
   - Verificar credenciais no .env
   - Verificar permissões do usuário

3. **WhatsApp não funciona**
   - Verificar se Evolution API está rodando
   - Verificar configurações de webhook
   - Verificar instância do WhatsApp

4. **Emails não enviados**
   - Verificar configurações SMTP
   - Verificar logs da aplicação
   - Testar conexão SMTP

### Comandos Úteis

```bash
# Reiniciar aplicação
sudo systemctl restart gunicorn-imobiliario

# Atualizar aplicação
cd /opt/imobiliario/app
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=sistema_imobiliario.settings_production
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production
sudo systemctl restart gunicorn-imobiliario

# Verificar uso de recursos
htop
df -h
free -h
```

## 💰 Estimativa de Custos Mensais

- **VPS (2GB RAM, 1 CPU)**: $10-20
- **Domínio**: $10-15/ano
- **SSL**: Gratuito (Let's Encrypt)
- **Email**: Gratuito (Gmail) ou $6/mês (Google Workspace)
- **Total**: ~$15-25/mês

## 📞 Suporte

Para suporte técnico, mantenha logs atualizados e documente qualquer erro encontrado.

---

**⚠️ Importante**: Sempre faça backup antes de qualquer atualização e teste em ambiente de desenvolvimento primeiro.