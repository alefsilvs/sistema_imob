# 🚀 DEPLOY NO VERCEL - Sistema Imobiliário

## ⚡ **VERCEL - Deploy Ultrarrápido**

### 🎯 **Características:**
- ✅ **Deploy em segundos**
- ✅ **SSL automático**
- ✅ **CDN global**
- ✅ **Integração GitHub**
- ❌ **Limitado para Django (serverless)**

---

## 📋 **PASSO A PASSO:**

### **1. Instalar Vercel CLI**
```bash
npm install -g vercel
```

### **2. Criar arquivo `vercel.json`**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "sistema_imobiliario/wsgi.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb" }
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "sistema_imobiliario/wsgi.py"
    }
  ],
  "env": {
    "DJANGO_SETTINGS_MODULE": "sistema_imobiliario.settings_vercel"
  }
}
```

### **3. Criar `settings_vercel.py`**
```python
import os
import dj_database_url
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    '.vercel.app',
    'localhost',
    '127.0.0.1',
]

# Adicionar domínio personalizado
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)

# Banco de dados (usar PostgreSQL externo)
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
    )
}

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configurações de segurança
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### **4. Deploy**
```bash
vercel --prod
```

---

## ⚠️ **LIMITAÇÕES DO VERCEL:**
- **Serverless**: Cada request é uma função
- **Timeout**: 10 segundos máximo
- **Banco**: Precisa ser externo (Supabase, PlanetScale)
- **Arquivos**: Não persiste uploads

---

## 🎯 **RECOMENDAÇÃO:**
**Use Vercel apenas para:**
- Sites estáticos
- APIs simples
- Projetos pequenos

**Para Django completo, prefira Render ou DigitalOcean!**