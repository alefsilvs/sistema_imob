# 🐍 DEPLOY NO PYTHONANYWHERE - Sistema Imobiliário

## 🎯 **PYTHONANYWHERE - Especialista em Python**

### 🌟 **Características:**
- ✅ **Especializado em Python/Django**
- ✅ **Console web integrado**
- ✅ **MySQL incluído**
- ✅ **Fácil configuração**
- ✅ **Suporte brasileiro**
- 💰 **Plano gratuito limitado**

---

## 📋 **PASSO A PASSO:**

### **1. Criar conta:** https://www.pythonanywhere.com

### **2. Upload do código**
```bash
# No console do PythonAnywhere
git clone https://github.com/seu-usuario/sistema-imobiliario.git
cd sistema-imobiliario
```

### **3. Criar ambiente virtual**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **4. Criar `settings_pythonanywhere.py`**
```python
import os
from .settings import *

# Configurações básicas
DEBUG = False
ALLOWED_HOSTS = [
    'seuusuario.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]

# Banco de dados MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'seuusuario$sistema_imo',
        'USER': 'seuusuario',
        'PASSWORD': 'sua_senha_mysql',
        'HOST': 'seuusuario.mysql.pythonanywhere-services.com',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = '/home/seuusuario/sistema-imobiliario/staticfiles'

# Arquivos de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/seuusuario/sistema-imobiliario/media'

# Configurações de segurança
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email (usar Gmail ou outro)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

### **5. Configurar WSGI**
```python
# /var/www/seuusuario_pythonanywhere_com_wsgi.py
import os
import sys

# Adicionar o projeto ao path
path = '/home/seuusuario/sistema-imobiliario'
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_imobiliario.settings_pythonanywhere'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### **6. Executar migrações**
```bash
cd /home/seuusuario/sistema-imobiliario
source venv/bin/activate
python manage.py migrate --settings=sistema_imobiliario.settings_pythonanywhere
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_pythonanywhere
python manage.py createsuperuser --settings=sistema_imobiliario.settings_pythonanywhere
```

### **7. Configurar arquivos estáticos**
- **URL:** `/static/`
- **Directory:** `/home/seuusuario/sistema-imobiliario/staticfiles/`

### **8. Configurar arquivos de mídia**
- **URL:** `/media/`
- **Directory:** `/home/seuusuario/sistema-imobiliario/media/`

---

## 💰 **PLANOS:**

### **🆓 Gratuito:**
- 1 aplicação web
- 512MB de espaço
- Limitações de CPU
- Domínio: `seuusuario.pythonanywhere.com`

### **💵 Hacker ($5/mês):**
- 1 aplicação web
- 1GB de espaço
- Mais CPU
- Domínio personalizado

### **💎 Web Developer ($12/mês):**
- 3 aplicações web
- 10GB de espaço
- SSH completo
- Múltiplos domínios

---

## 🎯 **VANTAGENS:**
- ✅ **Muito fácil para iniciantes**
- ✅ **Console web integrado**
- ✅ **Suporte excelente**
- ✅ **Backup automático**

## ⚠️ **DESVANTAGENS:**
- ❌ **Plano gratuito muito limitado**
- ❌ **Performance limitada**
- ❌ **Sem Docker**

---

## 🚀 **DEPLOY AUTOMÁTICO:**

### **Script de deploy**
```bash
#!/bin/bash
# deploy_pythonanywhere.sh

echo "🚀 Deploy no PythonAnywhere..."

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar código
git pull origin main

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate --settings=sistema_imobiliario.settings_pythonanywhere

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_pythonanywhere

# Recarregar aplicação
touch /var/www/seuusuario_pythonanywhere_com_wsgi.py

echo "✅ Deploy concluído!"
```

---

## 📞 **SUPORTE:**
- **Documentação:** https://help.pythonanywhere.com/
- **Fórum:** https://www.pythonanywhere.com/forums/
- **Email:** support@pythonanywhere.com