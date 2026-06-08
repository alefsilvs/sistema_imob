# 🌊 DEPLOY NO DIGITALOCEAN - Sistema Imobiliário

## 🚀 **DIGITALOCEAN APP PLATFORM - Profissional**

### 🌟 **Características:**
- ✅ **Muito confiável**
- ✅ **Escalável**
- ✅ **PostgreSQL incluído**
- ✅ **Redis incluído**
- ✅ **Monitoramento avançado**
- 💰 **$5/mês (muito barato para o que oferece)**

---

## 📋 **PASSO A PASSO:**

### **1. Criar conta:** https://cloud.digitalocean.com

### **2. Criar arquivo `.do/app.yaml`**
```yaml
name: sistema-imobiliario
services:
- name: web
  source_dir: /
  github:
    repo: seu-usuario/sistema-imobiliario
    branch: main
  run_command: gunicorn sistema_imobiliario.wsgi:application --bind 0.0.0.0:$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
  routes:
  - path: /
  health_check:
    http_path: /
  envs:
  - key: DJANGO_SETTINGS_MODULE
    value: sistema_imobiliario.settings_digitalocean
  - key: DEBUG
    value: "False"
  - key: PYTHONPATH
    value: .

databases:
- name: sistema-imo-db
  engine: PG
  version: "14"
  size: db-s-dev-database

workers:
- name: celery-worker
  source_dir: /
  github:
    repo: seu-usuario/sistema-imobiliario
    branch: main
  run_command: celery -A sistema_imobiliario worker --loglevel=info
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DJANGO_SETTINGS_MODULE
    value: sistema_imobiliario.settings_digitalocean
```

### **3. Criar `settings_digitalocean.py`**
```python
import os
import dj_database_url
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    '.ondigitalocean.app',
    'localhost',
    '127.0.0.1',
]

# Adicionar domínio personalizado
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')

# Banco de dados PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Cache Redis
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                }
            }
        }
    }

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware para arquivos estáticos
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configurações de segurança
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configurações de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Configurações de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Configurações de performance
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

print(f"🌊 DigitalOcean Settings Loaded")
print(f"📊 Database: PostgreSQL")
print(f"🔒 Debug Mode: {DEBUG}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
print(f"💾 Cache: Redis" if REDIS_URL else "Database")
```

### **4. Criar script de build**
```bash
#!/usr/bin/env bash
# build_digitalocean.sh

set -o errexit

echo "🌊 Build para DigitalOcean App Platform..."

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input --settings=sistema_imobiliario.settings_digitalocean

# Executar migrações
python manage.py migrate --settings=sistema_imobiliario.settings_digitalocean

echo "✅ Build concluído!"
```

---

## 💰 **PREÇOS (2024):**

### **🚀 Basic ($5/mês):**
- 512MB RAM
- 1 vCPU
- PostgreSQL incluído
- SSL automático
- Domínio personalizado

### **💎 Professional ($12/mês):**
- 1GB RAM
- 1 vCPU
- Recursos adicionais
- Backup automático

### **🏢 Advanced ($24/mês):**
- 2GB RAM
- 2 vCPU
- Alta disponibilidade
- Monitoramento avançado

---

## 🎯 **VANTAGENS:**
- ✅ **Muito confiável (99.99% uptime)**
- ✅ **PostgreSQL e Redis incluídos**
- ✅ **Escalabilidade automática**
- ✅ **Monitoramento integrado**
- ✅ **Backup automático**
- ✅ **SSL automático**
- ✅ **Deploy via GitHub**

## ⚠️ **DESVANTAGENS:**
- ❌ **Não tem plano gratuito**
- ❌ **Mais caro que Render**

---

## 🚀 **DEPLOY:**

### **1. Via Interface Web:**
1. Acesse DigitalOcean App Platform
2. Conecte seu GitHub
3. Selecione o repositório
4. Configure as variáveis de ambiente
5. Deploy automático

### **2. Via CLI:**
```bash
# Instalar doctl
snap install doctl

# Autenticar
doctl auth init

# Deploy
doctl apps create .do/app.yaml
```

---

## 📊 **MONITORAMENTO:**
- **Métricas em tempo real**
- **Logs centralizados**
- **Alertas automáticos**
- **Health checks**

---

## 🔧 **VARIÁVEIS DE AMBIENTE:**
```
SECRET_KEY=sua_secret_key_aqui
DEBUG=False
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_digitalocean
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_app
CUSTOM_DOMAIN=seudominio.com
```

---

## 🎯 **RECOMENDAÇÃO:**
**DigitalOcean é PERFEITO para:**
- ✅ **Aplicações profissionais**
- ✅ **Projetos que precisam de confiabilidade**
- ✅ **Empresas que podem pagar $5/mês**
- ✅ **Aplicações com tráfego médio/alto**