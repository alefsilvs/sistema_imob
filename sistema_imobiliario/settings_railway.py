import os
import logging
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

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]

# Adicionar domínio personalizado se configurado
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    ALLOWED_HOSTS.append(f'www.{CUSTOM_DOMAIN}')
    ALLOWED_HOSTS.append(f'.{CUSTOM_DOMAIN}')
    CSRF_TRUSTED_ORIGINS.extend([
        f"https://{CUSTOM_DOMAIN}",
        f"https://*.{CUSTOM_DOMAIN}",
    ])

# Banco de dados Railway
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
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
else:
    # Cache em banco de dados como fallback
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
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
        'simple': {
            'format': '{levelname} {message}',
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
        'sistema_imobiliario': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações específicas do Railway
PORT = int(os.environ.get('PORT', 8000))

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de timezone
USE_TZ = True
TIME_ZONE = 'America/Sao_Paulo'

# Configurações do WhatsApp (se aplicável)
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')
WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY')

EVOLUTION_SERVICE_NAME = os.environ.get('EVOLUTION_SERVICE_NAME') or 'evolution-api'
EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL') or WHATSAPP_API_URL or f'http://{EVOLUTION_SERVICE_NAME}.railway.internal:8080'
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY') or WHATSAPP_API_KEY
EVOLUTION_INSTANCE_NAME = os.environ.get('EVOLUTION_INSTANCE_NAME') or os.environ.get('WHATSAPP_INSTANCE_NAME') or 'imobilpro'
EVOLUTION_AUTO_START_DOCKER = False

# Configurações de pagamento (se aplicável)
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')
MERCADOPAGO_PUBLIC_KEY = os.environ.get('MERCADOPAGO_PUBLIC_KEY')

# Configurações de backup (se aplicável)
BACKUP_EMAIL = os.environ.get('BACKUP_EMAIL')

# Configurações de monitoramento
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='production',
    )

# Configurações de performance
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Configurações de internacionalização
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True

# Configurações de arquivos estáticos adicionais
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configurações de compressão do WhiteNoise
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Configurações de CORS (se necessário para API)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    f"https://{CUSTOM_DOMAIN}" if CUSTOM_DOMAIN else "",
]

# Remover origens vazias
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin]

# Configurações de CSP (Content Security Policy)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")

# Configurações específicas para Railway
RAILWAY_ENVIRONMENT = os.environ.get('RAILWAY_ENVIRONMENT', 'production')
RAILWAY_PROJECT_ID = os.environ.get('RAILWAY_PROJECT_ID')
RAILWAY_SERVICE_ID = os.environ.get('RAILWAY_SERVICE_ID')

# Debug para Railway (apenas em desenvolvimento)
if RAILWAY_ENVIRONMENT == 'development':
    DEBUG = True
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

print(f"🚀 Railway Settings Loaded - Environment: {RAILWAY_ENVIRONMENT}")
print(f"📊 Database: {'PostgreSQL' if 'postgresql' in DATABASES['default']['ENGINE'] else 'SQLite'}")
print(f"🔒 Debug Mode: {DEBUG}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
