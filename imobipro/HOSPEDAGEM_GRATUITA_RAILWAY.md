# 🚀 Hospedagem Gratuita - Railway

## 🎯 Por que Railway?

O **Railway** é uma das melhores opções gratuitas para hospedar aplicações Django em 2024:

✅ **$5 de crédito gratuito por mês** (suficiente para projetos pequenos/médios)  
✅ **PostgreSQL gratuito** incluído  
✅ **Deploy automático** via GitHub  
✅ **HTTPS automático** com domínio próprio  
✅ **Logs em tempo real** e monitoramento  
✅ **Fácil configuração** - sem complexidade  

---

## 📋 Pré-requisitos

1. **Conta no GitHub** (para conectar o repositório)
2. **Conta no Railway** (gratuita em [railway.app](https://railway.app))
3. **Código no GitHub** (vamos configurar isso)

---

## 🔧 Passo 1: Preparar o Projeto para Railway

### 1.1 Criar arquivo `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 1.2 Criar `Procfile`

```
web: gunicorn sistema_imobiliario.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate --settings=sistema_imobiliario.settings_railway
```

### 1.3 Criar `runtime.txt`

```
python-3.11.0
```

### 1.4 Atualizar `requirements.txt`

Adicionar dependências específicas para Railway:

```
# Dependências existentes...
dj-database-url==2.1.0
whitenoise==6.6.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

---

## ⚙️ Passo 2: Configurações Django para Railway

### 2.1 Criar `settings_railway.py`

```python
import os
import dj_database_url
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    '.railway.app',
    '.up.railway.app',
    'localhost',
    '127.0.0.1',
]

# Banco de dados Railway
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

# Configurações de email (usando variáveis de ambiente)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Configurações de cache (Redis se disponível)
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

# Configurações de sessão
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas

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

# Configurações específicas do Railway
PORT = int(os.environ.get('PORT', 8000))

# Configurações de mídia (para Railway)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de timezone
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

# Configurações de segurança adicional
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações do WhatsApp (se aplicável)
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')
WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY')

# Configurações de pagamento (se aplicável)
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
MERCADOPAGO_PUBLIC_KEY = os.environ.get('MERCADOPAGO_PUBLIC_KEY')
```

---

## 🚀 Passo 3: Deploy no Railway

### 3.1 Subir código para GitHub

```bash
# Inicializar repositório Git (se ainda não foi feito)
git init
git add .
git commit -m "Preparar projeto para Railway"

# Criar repositório no GitHub e conectar
git remote add origin https://github.com/SEU_USUARIO/sistema-imobiliario.git
git branch -M main
git push -u origin main
```

### 3.2 Conectar ao Railway

1. **Acesse:** [railway.app](https://railway.app)
2. **Faça login** com GitHub
3. **Clique em "New Project"**
4. **Selecione "Deploy from GitHub repo"**
5. **Escolha seu repositório** `sistema-imobiliario`
6. **Aguarde o deploy automático**

### 3.3 Configurar Banco de Dados

1. **No dashboard do Railway:**
   - Clique em **"+ New"**
   - Selecione **"Database"**
   - Escolha **"PostgreSQL"**

2. **Conectar ao projeto:**
   - O Railway automaticamente criará a variável `DATABASE_URL`
   - Não precisa configurar nada manualmente!

### 3.4 Configurar Variáveis de Ambiente

No dashboard do Railway, vá em **Variables** e adicione:

```bash
# Configurações básicas
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_railway
SECRET_KEY=sua_chave_secreta_aqui_muito_longa_e_segura
DEBUG=False

# Email (Gmail)
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
DEFAULT_FROM_EMAIL=seu_email@gmail.com

# WhatsApp (opcional)
WHATSAPP_API_URL=sua_url_da_api
WHATSAPP_API_KEY=sua_chave_da_api

# Pagamentos (opcional)
MERCADOPAGO_ACCESS_TOKEN=seu_token
MERCADOPAGO_PUBLIC_KEY=sua_chave_publica
```

---

## 🔧 Passo 4: Configurações Finais

### 4.1 Executar Migrações

O Railway executará automaticamente as migrações através do `Procfile`, mas você pode forçar via CLI:

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Fazer login
railway login

# Conectar ao projeto
railway link

# Executar comandos
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic --noinput
```

### 4.2 Configurar Domínio Personalizado

1. **No dashboard do Railway:**
   - Vá em **Settings**
   - Clique em **Domains**
   - Adicione seu domínio personalizado
   - Configure DNS conforme instruções

---

## 📊 Monitoramento e Logs

### Ver Logs em Tempo Real

```bash
# Via CLI
railway logs

# Ou no dashboard web
# Vá em "Deployments" > "View Logs"
```

### Métricas de Uso

- **CPU e Memória:** Visível no dashboard
- **Banco de Dados:** Estatísticas automáticas
- **Tráfego:** Requests por minuto

---

## 💰 Limites do Plano Gratuito

### Railway Starter (Gratuito)
- **$5 de crédito por mês**
- **512MB RAM** por serviço
- **1GB de armazenamento** no banco
- **100GB de tráfego** por mês
- **Domínio .railway.app** gratuito

### Estimativa de Uso
Para um sistema imobiliário pequeno/médio:
- **Aplicação Django:** ~$2-3/mês
- **PostgreSQL:** ~$1-2/mês
- **Total:** ~$3-5/mês (dentro do limite gratuito!)

---

## 🔄 Deploy Automático

### Configurar Auto-Deploy

1. **No dashboard Railway:**
   - Vá em **Settings**
   - Ative **"Auto-Deploy"**
   - Escolha a branch (geralmente `main`)

2. **Agora toda vez que você fizer push:**
   ```bash
   git add .
   git commit -m "Nova funcionalidade"
   git push origin main
   # Deploy automático será iniciado!
   ```

---

## 🛠️ Comandos Úteis

### Gerenciar via CLI

```bash
# Ver status do projeto
railway status

# Executar comandos Django
railway run python manage.py shell
railway run python manage.py dbshell
railway run python manage.py createsuperuser

# Ver variáveis de ambiente
railway variables

# Fazer backup do banco
railway run pg_dump $DATABASE_URL > backup.sql
```

### Debugging

```bash
# Ver logs de erro
railway logs --filter error

# Conectar ao banco diretamente
railway connect postgres

# Executar shell Django
railway run python manage.py shell
```

---

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de Migração:**
   ```bash
   railway run python manage.py migrate --fake-initial
   ```

2. **Arquivos Estáticos não Carregam:**
   ```bash
   railway run python manage.py collectstatic --clear --noinput
   ```

3. **Erro de Memória:**
   - Otimize queries do banco
   - Use cache quando possível
   - Considere upgrade do plano

4. **Timeout de Deploy:**
   - Verifique logs de build
   - Simplifique dependências
   - Use requirements.txt otimizado

---

## 📈 Próximos Passos

### Após Deploy Bem-sucedido

1. **Testar todas as funcionalidades**
2. **Configurar monitoramento**
3. **Fazer backup inicial**
4. **Documentar URLs e credenciais**
5. **Configurar domínio personalizado**

### Otimizações Futuras

1. **Adicionar Redis** para cache
2. **Configurar CDN** para arquivos estáticos
3. **Implementar monitoring** com Sentry
4. **Configurar backup automático**

---

## 🎉 Resultado Final

Após seguir este guia, você terá:

✅ **Sistema rodando** em `https://seu-projeto.up.railway.app`  
✅ **Banco PostgreSQL** configurado e funcionando  
✅ **Deploy automático** a cada push no GitHub  
✅ **HTTPS** configurado automaticamente  
✅ **Logs e monitoramento** disponíveis  
✅ **Custo zero** (dentro do limite de $5/mês)  

---

## 📞 Suporte

- **Documentação Railway:** [docs.railway.app](https://docs.railway.app)
- **Discord Railway:** [discord.gg/railway](https://discord.gg/railway)
- **GitHub Issues:** Para problemas específicos do projeto

---

*Última atualização: Janeiro 2024*