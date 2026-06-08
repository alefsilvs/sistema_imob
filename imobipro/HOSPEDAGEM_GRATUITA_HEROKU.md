# 🚀 Hospedagem Gratuita no Heroku

## ⚠️ IMPORTANTE: Mudanças no Heroku
**A partir de 28 de novembro de 2022, o Heroku descontinuou seu plano gratuito.** Este guia é mantido para referência histórica e para usuários que possuem créditos ou planos pagos.

**Alternativas recomendadas:**
- ✅ **Railway** (500h gratuitas/mês)
- ✅ **Render.com** (750h gratuitas/mês)
- ✅ **Fly.io** (Plano gratuito limitado)

## 📋 Índice
- [Status Atual do Heroku](#status-atual-do-heroku)
- [Pré-requisitos](#pré-requisitos)
- [Preparação do Projeto](#preparação-do-projeto)
- [Configurações Django](#configurações-django)
- [Deploy no Heroku](#deploy-no-heroku)
- [Configurações Finais](#configurações-finais)
- [Migração para Alternativas](#migração-para-alternativas)

## 🔴 Status Atual do Heroku

### O que mudou?
- **Plano gratuito descontinuado** (28/11/2022)
- **Dynos gratuitos removidos**
- **PostgreSQL gratuito removido**
- **Redis gratuito removido**

### Opções atuais no Heroku
- **Eco Dynos:** $5/mês (550 horas)
- **Basic Dynos:** $7/mês (ilimitado)
- **PostgreSQL Mini:** $5/mês
- **Redis Mini:** $3/mês

### Por que manter este guia?
- Referência para usuários com créditos
- Base para migração para outras plataformas
- Documentação histórica

## 📋 Pré-requisitos

- Conta no Heroku
- Heroku CLI instalado
- Conta no GitHub
- Projeto Django funcionando

## 🔧 Preparação do Projeto

### 1. Instalar Heroku CLI

```bash
# Windows (via Chocolatey)
choco install heroku-cli

# macOS (via Homebrew)
brew tap heroku/brew && brew install heroku

# Linux (via snap)
sudo snap install --classic heroku
```

### 2. Criar arquivo `Procfile`

```
web: gunicorn sistema_imobiliario.wsgi:application
release: python manage.py migrate --settings=sistema_imobiliario.settings_heroku
```

### 3. Criar `runtime.txt`

```
python-3.11.0
```

### 4. Atualizar `requirements.txt`

Adicionar dependências específicas do Heroku:

```txt
# Heroku específico
dj-database-url>=2.1.0
psycopg2-binary>=2.9.7
gunicorn>=21.2.0
whitenoise>=6.5.0
django-heroku>=0.3.1
```

## ⚙️ Configurações Django

### Criar `settings_heroku.py`

```python
# sistema_imobiliario/settings_heroku.py
import os
import dj_database_url
import django_heroku
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    '.herokuapp.com',
    'localhost',
    '127.0.0.1',
]

# Adicionar domínio personalizado se configurado
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')

# Banco de dados Heroku
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

# Configurações de cache Redis (Heroku Redis)
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

# Configurações específicas do Heroku
HEROKU_APP_NAME = os.environ.get('HEROKU_APP_NAME')
HEROKU_SLUG_COMMIT = os.environ.get('HEROKU_SLUG_COMMIT')

# Configurações de mídia (usar S3 em produção)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ativar configurações automáticas do Heroku
django_heroku.settings(locals())

print(f"🔥 Heroku Settings Loaded")
print(f"📊 Database: PostgreSQL")
print(f"🔒 Debug Mode: {DEBUG}")
print(f"🌐 App Name: {HEROKU_APP_NAME}")
```

## 🚀 Deploy no Heroku

### 1. Login no Heroku

```bash
heroku login
```

### 2. Criar aplicação

```bash
# Criar app com nome específico
heroku create sistema-imobiliario-seu-nome

# Ou deixar o Heroku gerar um nome
heroku create
```

### 3. Configurar variáveis de ambiente

```bash
# Configurações básicas
heroku config:set SECRET_KEY="sua_chave_secreta_aqui"
heroku config:set DJANGO_SETTINGS_MODULE="sistema_imobiliario.settings_heroku"
heroku config:set DEBUG=False

# Email
heroku config:set EMAIL_HOST_USER="seu_email@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="sua_senha_de_app"
heroku config:set DEFAULT_FROM_EMAIL="seu_email@gmail.com"

# Domínio personalizado (opcional)
heroku config:set CUSTOM_DOMAIN="seudominio.com"
```

### 4. Adicionar PostgreSQL

```bash
# Adicionar PostgreSQL (plano pago)
heroku addons:create heroku-postgresql:mini

# Verificar DATABASE_URL
heroku config:get DATABASE_URL
```

### 5. Adicionar Redis (opcional)

```bash
# Adicionar Redis (plano pago)
heroku addons:create heroku-redis:mini

# Verificar REDIS_URL
heroku config:get REDIS_URL
```

### 6. Deploy

```bash
# Adicionar remote do Heroku
git remote add heroku https://git.heroku.com/seu-app-name.git

# Deploy
git add .
git commit -m "Deploy para Heroku"
git push heroku main
```

## 🔧 Configurações Finais

### 1. Executar migrações

```bash
heroku run python manage.py migrate --settings=sistema_imobiliario.settings_heroku
```

### 2. Criar superusuário

```bash
heroku run python manage.py createsuperuser --settings=sistema_imobiliario.settings_heroku
```

### 3. Coletar arquivos estáticos

```bash
heroku run python manage.py collectstatic --settings=sistema_imobiliario.settings_heroku
```

### 4. Configurar domínio personalizado

```bash
# Adicionar domínio (requer plano pago)
heroku domains:add www.seudominio.com

# Configurar SSL (automático no Heroku)
heroku certs:auto:enable
```

## 📊 Monitoramento

### Logs

```bash
# Ver logs em tempo real
heroku logs --tail

# Ver logs específicos
heroku logs --source app
heroku logs --source heroku
```

### Métricas

```bash
# Status da aplicação
heroku ps

# Informações do dyno
heroku ps:scale web=1

# Restart da aplicação
heroku restart
```

## 💰 Custos Atuais (2024)

### Dynos
- **Eco:** $5/mês (550 horas)
- **Basic:** $7/mês (ilimitado)
- **Standard-1X:** $25/mês
- **Standard-2X:** $50/mês

### Add-ons
- **PostgreSQL Mini:** $5/mês (10k rows)
- **PostgreSQL Basic:** $9/mês (10M rows)
- **Redis Mini:** $3/mês (25MB)
- **Redis Premium-0:** $15/mês (100MB)

### Estimativa mensal mínima
- **Eco Dyno:** $5
- **PostgreSQL Mini:** $5
- **Total:** $10/mês

## 🔄 Migração para Alternativas

### 1. Exportar dados do Heroku

```bash
# Backup do banco
heroku pg:backups:capture
heroku pg:backups:download

# Backup de arquivos
heroku run tar -czf backup.tar.gz media/
```

### 2. Migrar para Railway

```bash
# Usar configurações do Railway
cp sistema_imobiliario/settings_heroku.py sistema_imobiliario/settings_railway.py
# Ajustar configurações específicas
```

### 3. Migrar para Render

```bash
# Usar configurações do Render
cp sistema_imobiliario/settings_heroku.py sistema_imobiliario/settings_render.py
# Ajustar configurações específicas
```

## 🛠️ Comandos Úteis

```bash
# Informações da aplicação
heroku info

# Configurações
heroku config

# Escalar dynos
heroku ps:scale web=1

# Conectar ao banco
heroku pg:psql

# Shell Django
heroku run python manage.py shell

# Backup do banco
heroku pg:backups:capture
heroku pg:backups:download

# Logs de erro
heroku logs --tail --source app | grep ERROR
```

## 🔧 Troubleshooting

### Problemas comuns

#### 1. Application Error (H10)
```bash
# Verificar se o dyno está rodando
heroku ps
heroku logs --tail
```

#### 2. Erro de banco de dados
```bash
# Verificar DATABASE_URL
heroku config:get DATABASE_URL
heroku pg:info
```

#### 3. Arquivos estáticos não carregam
```bash
# Executar collectstatic
heroku run python manage.py collectstatic --noinput
```

## 🎯 Recomendações

### Para novos projetos
1. **Use Railway ou Render** (planos gratuitos disponíveis)
2. **Heroku apenas se necessário** (recursos específicos)
3. **Considere custos** ($10+/mês mínimo)

### Para projetos existentes no Heroku
1. **Avalie migração** para plataformas gratuitas
2. **Compare custos** com outras opções
3. **Mantenha backups** regulares

## 📚 Recursos Adicionais

- [Documentação Heroku](https://devcenter.heroku.com/)
- [Django no Heroku](https://devcenter.heroku.com/articles/django-app-configuration)
- [Migração do Heroku](https://devcenter.heroku.com/articles/migrating-from-heroku)
- [Alternativas ao Heroku](https://github.com/Engagespot/heroku-alternatives)

---

**💡 Recomendação:** Considere usar Railway ou Render.com para novos projetos, pois oferecem planos gratuitos robustos e são mais econômicos que o Heroku atual.