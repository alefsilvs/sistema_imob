# 🚀 Hospedagem Gratuita no Render.com

## 📋 Índice
- [Por que Render.com?](#por-que-rendercom)
- [Pré-requisitos](#pré-requisitos)
- [Preparação do Projeto](#preparação-do-projeto)
- [Configurações Django](#configurações-django)
- [Deploy no Render](#deploy-no-render)
- [Configurações Finais](#configurações-finais)
- [Monitoramento](#monitoramento)
- [Limites do Plano Gratuito](#limites-do-plano-gratuito)
- [Troubleshooting](#troubleshooting)

## 🎯 Por que Render.com?

### ✅ Vantagens
- **Hospedagem gratuita** com PostgreSQL incluído
- **Deploy automático** via GitHub
- **SSL gratuito** e automático
- **Domínio personalizado** gratuito
- **Interface simples** e intuitiva
- **Logs em tempo real**
- **Backup automático** do banco
- **Suporte a Python/Django** nativo

### 📊 Comparação com outras plataformas
| Recurso | Render | Railway | Heroku |
|---------|--------|---------|--------|
| Horas gratuitas | 750h/mês | 500h/mês | 550h/mês |
| RAM | 512MB | 1GB | 512MB |
| PostgreSQL | ✅ Grátis | ✅ Grátis | ✅ Grátis |
| SSL | ✅ Auto | ✅ Auto | ✅ Auto |
| Domínio custom | ✅ Grátis | ✅ Grátis | ❌ Pago |

## 📋 Pré-requisitos

- Conta no GitHub
- Conta no Render.com (gratuita)
- Projeto Django funcionando localmente
- Git configurado

## 🔧 Preparação do Projeto

### 1. Criar arquivo `render.yaml`

```yaml
# render.yaml
databases:
  - name: sistema-imo-db
    databaseName: sistema_imo
    user: sistema_imo_user

services:
  - type: web
    name: sistema-imo
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn sistema_imobiliario.wsgi:application"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: sistema-imo-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_CONCURRENCY
        value: 4
```

### 2. Criar script de build `build.sh`

```bash
#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input --settings=sistema_imobiliario.settings_render
python manage.py migrate --settings=sistema_imobiliario.settings_render
```

### 3. Tornar o script executável

```bash
chmod +x build.sh
```

## ⚙️ Configurações Django

### Criar `settings_render.py`

```python
# sistema_imobiliario/settings_render.py
import os
import dj_database_url
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Adicionar domínio personalizado se configurado
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')

# Banco de dados Render
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
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

# Configurações de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Configurações de cache Redis (se disponível)
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Cache em banco como fallback
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }

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
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações específicas do Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de timezone
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

print(f"🎨 Render Settings Loaded")
print(f"📊 Database: PostgreSQL")
print(f"🔒 Debug Mode: {DEBUG}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
```

## 🚀 Deploy no Render

### 1. Preparar repositório GitHub

```bash
# Adicionar arquivos ao Git
git add .
git commit -m "Configurações para Render.com"
git push origin main
```

### 2. Conectar ao Render

1. Acesse [render.com](https://render.com)
2. Faça login com GitHub
3. Clique em "New +"
4. Selecione "Web Service"
5. Conecte seu repositório

### 3. Configurar o serviço

**Configurações básicas:**
- **Name:** `sistema-imobiliario`
- **Environment:** `Python 3`
- **Build Command:** `./build.sh`
- **Start Command:** `gunicorn sistema_imobiliario.wsgi:application`

**Configurações avançadas:**
- **Instance Type:** `Free`
- **Auto-Deploy:** `Yes`

### 4. Configurar banco de dados

1. No dashboard, clique em "New +"
2. Selecione "PostgreSQL"
3. Configure:
   - **Name:** `sistema-imo-db`
   - **Database:** `sistema_imo`
   - **User:** `sistema_imo_user`
   - **Plan:** `Free`

### 5. Configurar variáveis de ambiente

No painel do serviço web, vá em "Environment" e adicione:

```
SECRET_KEY=sua_chave_secreta_aqui
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_render
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
DEFAULT_FROM_EMAIL=seu_email@gmail.com
CUSTOM_DOMAIN=seudominio.com (opcional)
```

## 🔧 Configurações Finais

### 1. Primeiro deploy

O deploy acontece automaticamente após a configuração.

### 2. Executar migrações

As migrações são executadas automaticamente no `build.sh`.

### 3. Criar superusuário

```bash
# Via Render Shell (no dashboard)
python manage.py createsuperuser --settings=sistema_imobiliario.settings_render
```

### 4. Configurar domínio personalizado

1. No dashboard do serviço
2. Vá em "Settings" > "Custom Domains"
3. Adicione seu domínio
4. Configure CNAME no seu provedor DNS:
   ```
   CNAME: www.seudominio.com -> seu-app.onrender.com
   ```

## 📊 Monitoramento

### Logs em tempo real
```bash
# No dashboard do Render
# Clique em "Logs" para ver logs em tempo real
```

### Métricas disponíveis
- CPU usage
- Memory usage
- Response time
- Error rate
- Deploy history

### Alertas
- Configure alertas por email
- Monitore uptime
- Acompanhe performance

## 💰 Limites do Plano Gratuito

### Web Service
- **750 horas/mês** de execução
- **512MB RAM**
- **Hibernação** após 15min inativo
- **Build time:** 15min máximo
- **Bandwidth:** Ilimitado

### PostgreSQL
- **1GB** de armazenamento
- **Conexões:** 97 simultâneas
- **Backup:** 7 dias
- **Uptime:** 99.9%

### Recursos inclusos
- ✅ SSL automático
- ✅ Deploy automático
- ✅ Domínio personalizado
- ✅ Logs em tempo real
- ✅ Métricas básicas

## 🔧 Troubleshooting

### Problemas comuns

#### 1. Build falha
```bash
# Verificar logs de build
# Comum: dependências em requirements.txt
# Solução: Verificar versões compatíveis
```

#### 2. Aplicação não inicia
```bash
# Verificar start command
# Deve ser: gunicorn sistema_imobiliario.wsgi:application
```

#### 3. Erro de banco de dados
```bash
# Verificar DATABASE_URL
# Deve estar conectada ao PostgreSQL
```

#### 4. Arquivos estáticos não carregam
```bash
# Verificar STATIC_ROOT e collectstatic
# Deve executar no build.sh
```

#### 5. Hibernação frequente
```bash
# Plano gratuito hiberna após 15min
# Considere upgrade para plano pago
```

### Comandos úteis

```bash
# Ver logs
# No dashboard: Logs tab

# Restart serviço
# No dashboard: Manual Deploy

# Conectar ao banco
# No dashboard: PostgreSQL > Connect

# Shell do Django
# Via Render Shell: python manage.py shell
```

## 🎯 Próximos Passos

1. **Criar conta no Render.com**
2. **Preparar repositório GitHub**
3. **Configurar arquivos de deploy**
4. **Fazer primeiro deploy**
5. **Configurar domínio personalizado**
6. **Configurar monitoramento**
7. **Testar funcionalidades**

## 📚 Recursos Adicionais

- [Documentação Render](https://render.com/docs)
- [Deploy Django no Render](https://render.com/docs/deploy-django)
- [PostgreSQL no Render](https://render.com/docs/databases)
- [Domínios personalizados](https://render.com/docs/custom-domains)

---

**💡 Dica:** O Render.com é uma excelente opção para projetos Django, oferecendo uma experiência similar ao Heroku com plano gratuito generoso e PostgreSQL incluído!