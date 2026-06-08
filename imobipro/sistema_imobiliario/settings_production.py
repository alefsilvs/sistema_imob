# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Configurações de Produção para KingHost

Copyright (c) 2024 - Todos os direitos reservados
"""

from .settings import *
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o arquivo .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# CONFIGURAÇÕES DE SEGURANÇA
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY deve ser definida no arquivo .env")

DEBUG = False

# Hosts permitidos - CONFIGURE COM SEU DOMÍNIO KINGHOST
ALLOWED_HOSTS = [
    os.environ.get('DOMAIN_NAME', 'seu-dominio.com.br'),
    f"www.{os.environ.get('DOMAIN_NAME', 'seu-dominio.com.br')}",
    os.environ.get('SERVER_IP', ''),
    'localhost',  # Para testes locais
    '127.0.0.1',
]

# MIDDLEWARE - Adicionando WhiteNoise para arquivos estáticos
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir arquivos estáticos
    'security.middleware.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'saas.middleware.TenantMiddleware',
    'saas.middleware.TenantDatabaseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'saas.middleware.EmailVerificationMiddleware',
    'security.middleware.MasterUserMiddleware',
    'saas.middleware.TenantSecurityMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'saas.middleware.TenantContextMiddleware',
    'saas.middleware.APITenantMiddleware',
    'core.middleware_perfil.ControlePermissaoPerfilMiddleware',
    'security.middleware.AuditMiddleware',
]

# BANCO DE DADOS - PostgreSQL (Recomendado para KingHost)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sistema_imobiliario'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 60,
        },
    }
}

# CACHE - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'KEY_PREFIX': 'sistema_imo',
        'TIMEOUT': 300,
    }
}

# ARQUIVOS ESTÁTICOS - Configuração para KingHost
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise para servir arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ARQUIVOS DE MÍDIA
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# EMAIL - Configuração para KingHost
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.kinghost.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_USER', 'noreply@seu-dominio.com.br')
SERVER_EMAIL = os.environ.get('EMAIL_USER', 'server@seu-dominio.com.br')

# CONFIGURAÇÕES DE SEGURANÇA HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# SESSÕES
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configurações de sessão
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# Configurações de CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 86400

# Configurações de email para produção
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configurações de logging para produção
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/opt/imobiliario/logs/django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/opt/imobiliario/logs/django_error.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'notificacoes': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações de cache para produção
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/opt/imobiliario/cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Configurações de WhatsApp/Evolution API
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', '')
WHATSAPP_INSTANCE_NAME = os.getenv('WHATSAPP_INSTANCE_NAME', 'sistema_imobiliario')

# Configurações de timezone
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

# Configurações de internacionalização
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True

# Configurações de upload de arquivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Configurações de performance
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Configurações de admin
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

# Configurações de backup
BACKUP_ENABLED = True
BACKUP_DIRECTORY = '/opt/imobiliario/backups/'
BACKUP_RETENTION_DAYS = 30

# Configurações específicas do sistema
SISTEMA_NOME = 'Sistema Imobiliário - ImobilPro'
SISTEMA_VERSAO = '1.0.0'
SISTEMA_EMPRESA = 'Sua Empresa'

# Configurações de notificações
NOTIFICACAO_EMAIL_ATIVO = True
NOTIFICACAO_WHATSAPP_ATIVO = True
NOTIFICACAO_MAX_TENTATIVAS = 3
NOTIFICACAO_INTERVALO_TENTATIVAS = 300  # 5 minutos

# Configurações de proteção (manter as existentes)
PROTECTION_ENABLED = True
PROTECTION_LOG_FILE = '/opt/imobiliario/logs/protection.log'

# Configurações de CORS (se necessário para APIs)
CORS_ALLOWED_ORIGINS = [
    "https://seu-dominio.com",
    "https://www.seu-dominio.com",
]

CORS_ALLOW_CREDENTIALS = True

# Configurações de rate limiting
RATE_LIMIT_ENABLE = True
RATE_LIMIT_PER_MINUTE = 60

# Configurações de monitoramento
MONITORING_ENABLED = True
MONITORING_EMAIL = os.getenv('MONITORING_EMAIL', '')

# Configurações de backup automático
AUTO_BACKUP_ENABLED = True
AUTO_BACKUP_TIME = '02:00'  # 2:00 AM
AUTO_BACKUP_RETENTION = 7  # dias

print(f"[PRODUÇÃO] Configurações carregadas para: {ALLOWED_HOSTS}")
print(f"[PRODUÇÃO] Banco de dados: PostgreSQL em {DATABASES['default']['HOST']}")
print(f"[PRODUÇÃO] Debug: {DEBUG}")
print(f"[PRODUÇÃO] Email: {EMAIL_HOST_USER}")
print(f"[PRODUÇÃO] WhatsApp API: {EVOLUTION_API_URL}")