# Guia de Deploy - KingHost

Este guia detalha como hospedar o Sistema Imobiliário na KingHost.

## Pré-requisitos

### Planos Recomendados
- **VPS SSD 1** (mínimo) - Para projetos pequenos/médios
- **VPS SSD 2** (recomendado) - Para melhor performance
- **Cloud Server** - Para alta disponibilidade

### Especificações Mínimas
- 2 GB RAM
- 2 vCPUs
- 40 GB SSD
- Python 3.8+
- PostgreSQL ou MySQL

## Preparação do Ambiente Local

### 1. Configurar Settings de Produção

Crie um arquivo `settings_production.py`:

```python
from .settings import *
import os

# Configurações de produção
DEBUG = False
ALLOWED_HOSTS = ['seu-dominio.com.br', 'www.seu-dominio.com.br', 'IP_DO_SERVIDOR']

# Banco de dados (PostgreSQL recomendado)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sistema_imobiliario'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Segurança
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = '/home/usuario/public_html/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/usuario/public_html/media/'

# Email (configurar com seu provedor)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.kinghost.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Cache (Redis recomendado)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/usuario/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Atualizar Requirements

Adicione dependências de produção:

```txt
# Produção
gunicorn==21.2.0
psycopg2-binary==2.9.7
redis==4.6.0
whitenoise==6.5.0
```

## Configuração no Servidor KingHost

### 1. Acesso SSH

```bash
ssh usuario@seu-servidor.kinghost.net
```

### 2. Preparar Ambiente

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server

# Criar usuário para aplicação
sudo adduser sistema_imo
sudo usermod -aG sudo sistema_imo
```

### 3. Configurar PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE sistema_imobiliario;
CREATE USER sistema_imo WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE sistema_imobiliario TO sistema_imo;
\q
```

### 4. Deploy da Aplicação

```bash
# Mudar para usuário da aplicação
sudo su - sistema_imo

# Criar diretórios
mkdir -p ~/apps/sistema_imo
mkdir -p ~/logs
mkdir -p ~/public_html/{static,media}

# Clonar projeto
cd ~/apps/sistema_imo
git clone https://github.com/seu-usuario/sistema-imobiliario.git .

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cat > .env << EOF
SECRET_KEY=sua_chave_secreta_muito_longa_e_segura
DB_NAME=sistema_imobiliario
DB_USER=sistema_imo
DB_PASSWORD=senha_segura
DB_HOST=localhost
DB_PORT=5432
EMAIL_USER=seu-email@dominio.com.br
EMAIL_PASSWORD=senha_email
EOF

# Executar migrações
python manage.py migrate --settings=sistema_imobiliario.settings_production

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production

# Criar superusuário
python manage.py createsuperuser --settings=sistema_imobiliario.settings_production
```

### 5. Configurar Gunicorn

Criar arquivo de serviço:

```bash
sudo nano /etc/systemd/system/sistema_imo.service
```

Conteúdo:

```ini
[Unit]
Description=Sistema Imobiliário Gunicorn daemon
After=network.target

[Service]
User=sistema_imo
Group=www-data
WorkingDirectory=/home/sistema_imo/apps/sistema_imo
Environment="PATH=/home/sistema_imo/apps/sistema_imo/venv/bin"
ExecStart=/home/sistema_imo/apps/sistema_imo/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/home/sistema_imo/apps/sistema_imo/sistema_imo.sock \
          sistema_imobiliario.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Ativar serviço:

```bash
sudo systemctl start sistema_imo
sudo systemctl enable sistema_imo
sudo systemctl status sistema_imo
```

### 6. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/sistema_imo
```

Conteúdo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br www.seu-dominio.com.br;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/sistema_imo/public_html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /home/sistema_imo/public_html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/sistema_imo/apps/sistema_imo/sistema_imo.sock;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar site:

```bash
sudo ln -s /etc/nginx/sites-available/sistema_imo /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Configurar SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com.br -d www.seu-dominio.com.br
```

## Configurações Específicas da KingHost

### 1. Painel de Controle

- Acesse o painel da KingHost
- Configure o DNS para apontar para seu VPS
- Configure subdomínios se necessário

### 2. Backup Automático

```bash
# Criar script de backup
nano ~/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/sistema_imo/backups"
mkdir -p $BACKUP_DIR

# Backup do banco
pg_dump sistema_imobiliario > $BACKUP_DIR/db_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /home/sistema_imo/public_html/media

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Agendar no crontab:

```bash
crontab -e
# Adicionar linha:
0 2 * * * /home/sistema_imo/backup.sh
```

### 3. Monitoramento

Instalar htop e configurar alertas:

```bash
sudo apt install htop
```

## Otimizações de Performance

### 1. Redis Cache

```bash
# Configurar Redis
sudo nano /etc/redis/redis.conf
# Ajustar maxmemory conforme disponível
```

### 2. Nginx Gzip

Adicionar ao nginx.conf:

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

### 3. Database Tuning

```sql
-- Otimizações PostgreSQL
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

## Manutenção

### Comandos Úteis

```bash
# Verificar status dos serviços
sudo systemctl status sistema_imo nginx postgresql redis

# Ver logs
sudo journalctl -u sistema_imo -f
tail -f ~/logs/django.log

# Atualizar aplicação
cd ~/apps/sistema_imo
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=sistema_imobiliario.settings_production
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production
sudo systemctl restart sistema_imo
```

### Troubleshooting

1. **Erro 502**: Verificar se Gunicorn está rodando
2. **Erro 500**: Verificar logs do Django
3. **Arquivos estáticos não carregam**: Verificar configuração do Nginx
4. **Banco não conecta**: Verificar credenciais e firewall

## Suporte KingHost

- **Telefone**: 0800 033 7777
- **Chat**: Disponível no painel
- **Email**: suporte@kinghost.com.br
- **Documentação**: https://king.host/wiki/

## Checklist Final

- [ ] Domínio configurado
- [ ] SSL ativo
- [ ] Backup funcionando
- [ ] Monitoramento configurado
- [ ] Performance otimizada
- [ ] Logs configurados
- [ ] Email funcionando
- [ ] Todas as funcionalidades testadas

---

**Nota**: Este guia assume um VPS Linux. Para hospedagem compartilhada, algumas configurações podem diferir. Consulte a documentação específica da KingHost para seu tipo de plano.