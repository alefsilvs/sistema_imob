# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o arquivo .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = 'django-insecure-change-me'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver', '*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'security',  # Sistema de segurança master
    'core',
    'imoveis',
    'contratos',
    'financeiro',
    'manutencao',
    'documentos',
    'notificacoes',
    'pagamentos',  # Sistema de pagamentos online
    'assinaturas',  # Sistema de controle de acesso e assinaturas
    'saas.apps.SaasConfig',  # Sistema SaaS multi-tenant
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'security.middleware.SecurityMiddleware',  # Middleware principal de segurança
    # 'security.middleware.LoginSecurityMiddleware',  # Segurança de login - DESABILITADO: erro NOT NULL constraint
    'core.middleware_host.CanonicalDevHostMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'security.middleware.CSRFSecurityMiddleware',  # Proteção CSRF adicional - TEMPORARIAMENTE DESABILITADO
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # MOVIDO PARA ANTES DO TENANT
    'saas.middleware.TenantMiddleware',  # Identificação de tenant por subdomínio
    'saas.middleware.TenantDatabaseMiddleware',  # Configuração de database por tenant
    'saas.database_isolation.TenantSchemaMiddleware',  # Middleware de isolamento de schema
    'django.contrib.messages.middleware.MessageMiddleware',
    'saas.middleware.EmailVerificationMiddleware',  # Verificação de email obrigatória - HABILITADO
    'security.middleware.MasterUserMiddleware',  # Validação do usuário master
    # 'saas.middleware_pkg.trial_middleware.TrialMiddleware',  # Controle de trial gratuito - DESABILITADO: interfere no save
    # 'assinaturas.middleware.ControleAssinaturaMiddleware',  # Controle de acesso por assinatura - DESABILITADO: interfere no save
    # 'assinaturas.middleware.LimiteRecursosMiddleware',  # Limite de recursos por plano - DESABILITADO TEMPORARIAMENTE
    'saas.middleware.TenantSecurityMiddleware',  # Segurança e limites por tenant
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'saas.middleware.TenantContextMiddleware',  # Contexto do tenant nos templates
    'saas.middleware.APITenantMiddleware',  # Middleware para APIs
    'core.middleware_perfil.ControlePermissaoPerfilMiddleware',  # Controle de permissões por perfil
    'security.middleware.AuditMiddleware',  # Auditoria de ações
]

ROOT_URLCONF = 'sistema_imobiliario.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_imobiliario.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site framework
SITE_ID = 1

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Configurações de Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Configure conforme seu provedor
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@sistema.com')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))

EVOLUTION_AUTO_PROVISION = os.getenv('EVOLUTION_AUTO_PROVISION', '0') == '1'
EVOLUTION_HTTP_TIMEOUT = int(os.getenv('EVOLUTION_HTTP_TIMEOUT', '5'))

# URL do site para links de recuperação de senha
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')
SITE_ID = 1

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'  # Redireciona para home que tem lógica personalizada
LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTHENTICATION_BACKENDS = [
    'security.utils.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ========================================
# CONFIGURAÇÕES DE NFe
# ========================================

# Focus NFe API Configuration
FOCUS_NFE_CONFIG = {
    'TOKEN': os.getenv('FOCUS_NFE_TOKEN', ''),  # Token da API Focus NFe
    'AMBIENTE': os.getenv('FOCUS_NFE_AMBIENTE', 'homologacao'),  # 'producao' ou 'homologacao'
    'BASE_URL': {
        'homologacao': 'https://homologacao.focusnfe.com.br',
        'producao': 'https://api.focusnfe.com.br'
    },
    'TIMEOUT': 30,  # Timeout em segundos
    'RETRY_ATTEMPTS': 3,  # Tentativas de retry
}

# WebMania NFe API Configuration (alternativa)
WEBMANIA_NFE_CONFIG = {
    'CONSUMER_KEY': os.getenv('WEBMANIA_CONSUMER_KEY', ''),
    'CONSUMER_SECRET': os.getenv('WEBMANIA_CONSUMER_SECRET', ''),
    'ACCESS_TOKEN': os.getenv('WEBMANIA_ACCESS_TOKEN', ''),
    'ACCESS_TOKEN_SECRET': os.getenv('WEBMANIA_ACCESS_TOKEN_SECRET', ''),
    'AMBIENTE': os.getenv('WEBMANIA_AMBIENTE', 'homologacao'),
    'BASE_URL': {
        'homologacao': 'https://webmaniabr.com/api/1/nfe/homologacao',
        'producao': 'https://webmaniabr.com/api/1/nfe'
    },
}

# Configurações Fiscais da Empresa
EMPRESA_FISCAL = {
    'CNPJ': os.getenv('EMPRESA_CNPJ', ''),
    'INSCRICAO_ESTADUAL': os.getenv('EMPRESA_IE', ''),
    'INSCRICAO_MUNICIPAL': os.getenv('EMPRESA_IM', ''),
    'RAZAO_SOCIAL': os.getenv('EMPRESA_RAZAO_SOCIAL', 'Sua Empresa LTDA'),
    'NOME_FANTASIA': os.getenv('EMPRESA_NOME_FANTASIA', 'Sua Empresa'),
    'ENDERECO': {
        'LOGRADOURO': os.getenv('EMPRESA_LOGRADOURO', ''),
        'NUMERO': os.getenv('EMPRESA_NUMERO', ''),
        'COMPLEMENTO': os.getenv('EMPRESA_COMPLEMENTO', ''),
        'BAIRRO': os.getenv('EMPRESA_BAIRRO', ''),
        'CEP': os.getenv('EMPRESA_CEP', ''),
        'CIDADE': os.getenv('EMPRESA_CIDADE', ''),
        'UF': os.getenv('EMPRESA_UF', ''),
        'CODIGO_MUNICIPIO': os.getenv('EMPRESA_COD_MUNICIPIO', ''),
    },
    'CONTATO': {
        'TELEFONE': os.getenv('EMPRESA_TELEFONE', ''),
        'EMAIL': os.getenv('EMPRESA_EMAIL', ''),
    },
    'REGIME_TRIBUTARIO': os.getenv('EMPRESA_REGIME_TRIBUTARIO', '1'),  # 1=Simples Nacional, 2=Simples Nacional - excesso, 3=Normal
}

# Configurações de NFe
NFE_CONFIG = {
    'SERIE_NFE': int(os.getenv('NFE_SERIE', '1')),
    'NATUREZA_OPERACAO': os.getenv('NFE_NATUREZA_OPERACAO', 'Prestação de serviços'),
    'CODIGO_SERVICO': os.getenv('NFE_CODIGO_SERVICO', '25.01'),  # Código do serviço na lista de serviços
    'ALIQUOTA_ISS': float(os.getenv('NFE_ALIQUOTA_ISS', '5.0')),  # Alíquota do ISS em %
    'ITEM_LISTA_SERVICO': os.getenv('NFE_ITEM_LISTA_SERVICO', '25.01'),
    'CODIGO_TRIBUTACAO_MUNICIPIO': os.getenv('NFE_COD_TRIB_MUNICIPIO', ''),
    'DISCRIMINACAO_SERVICO': os.getenv('NFE_DISCRIMINACAO', 'Serviços de administração imobiliária'),
    'ENVIAR_EMAIL': os.getenv('NFE_ENVIAR_EMAIL', 'True').lower() == 'true',
    'GERAR_PDF': os.getenv('NFE_GERAR_PDF', 'True').lower() == 'true',
}

# Configurações de Certificado Digital (se necessário)
CERTIFICADO_DIGITAL = {
    'ARQUIVO_PFX': os.getenv('CERTIFICADO_PFX_PATH', ''),
    'SENHA': os.getenv('CERTIFICADO_SENHA', ''),
    'VALIDADE': os.getenv('CERTIFICADO_VALIDADE', ''),
}

# Provider de NFe ativo ('focus' ou 'webmania')
NFE_PROVIDER = os.getenv('NFE_PROVIDER', 'focus')

# Configurações da Empresa para Templates
EMPRESA_NOME = os.getenv('EMPRESA_NOME', 'Sistema Imobiliário')
EMPRESA_TELEFONE = os.getenv('EMPRESA_TELEFONE', '')
EMPRESA_EMAIL = os.getenv('EMPRESA_EMAIL', '')

# Diretórios para armazenar arquivos NFe
NFE_STORAGE = {
    'XML_DIR': MEDIA_ROOT / 'nfe' / 'xml',
    'PDF_DIR': MEDIA_ROOT / 'nfe' / 'pdf',
    'BACKUP_DIR': MEDIA_ROOT / 'nfe' / 'backup',
}

# Criar diretórios se não existirem
for directory in NFE_STORAGE.values():
    directory.mkdir(parents=True, exist_ok=True)

# Logging específico para NFe e Segurança
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
        'security': {
            'format': '[SECURITY] {levelname} {asctime} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_nfe': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'nfe.log',
            'formatter': 'verbose',
        },
        'file_security': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
        'file_security_critical': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security_critical.log',
            'formatter': 'security',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'nfe': {
            'handlers': ['file_nfe', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['file_security', 'file_security_critical', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Criar diretório de logs
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Suprimir warning do servidor de desenvolvimento
import warnings
warnings.filterwarnings('ignore', message='.*development server.*')



# ================================================================================
# CONFIGURAÇÕES DA EVOLUTION API (WHATSAPP)
# ================================================================================
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY', 'sistema_imo_2024_secure_key_789')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'imobilpro')
EVOLUTION_AUTO_START_DOCKER = os.getenv('EVOLUTION_AUTO_START_DOCKER', 'true').lower() == 'true'

# ================================================================================
# SISTEMA DE PROTEÇÃO - IMOBILPRO
# ================================================================================

# Inicialização do sistema de proteção
try:
    from .protection import init_protection
    # Inicializa proteção ao carregar settings
    _protection = init_protection()
except ImportError:
    print("⚠️  Sistema de proteção não encontrado!")
except Exception as e:
    print(f"⚠️  Erro ao inicializar proteção: {e}")

# Configurações de Sessão - Segurança contra vazamento de dados
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # True em produção
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True  # Renovar sessão a cada request
SESSION_COOKIE_NAME = 'imobilpro_sessionid'  # Nome único para evitar conflitos

# Configurações de CSRF
CSRF_COOKIE_HTTPONLY = False  # Permitir acesso via JavaScript se necessário
CSRF_COOKIE_SECURE = False  # Desabilitar HTTPS obrigatório para desenvolvimento
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
CSRF_FAILURE_VIEW = 'core.csrf_failure.csrf_failure'
CSRF_USE_SESSIONS = False  # Usar cookies ao invés de sessões para CSRF
CSRF_COOKIE_NAME = 'csrftoken'  # Nome padrão do cookie CSRF

# ================================================================================
# CONFIGURAÇÕES DE SEGURANÇA DE PAGAMENTOS
# ================================================================================

# Rate limiting para tentativas de pagamento
PAYMENT_MAX_ATTEMPTS = 5  # Máximo de tentativas por período
PAYMENT_WINDOW_MINUTES = 15  # Janela de tempo em minutos
PAYMENT_BLOCK_DURATION = 60  # Duração do bloqueio em minutos

# Validações de pagamento
PAYMENT_MIN_AMOUNT = 0.01  # Valor mínimo
PAYMENT_MAX_AMOUNT = 10000.00  # Valor máximo (R$ 10.000)

# Configurações de auditoria de admin
ADMIN_ACCESS_LOG_ENABLED = True
ADMIN_BYPASS_LOG_LEVEL = 'CRITICAL'  # Nível de log para bypass de admin
CSRF_COOKIE_AGE = 3600

# Configurações de segurança adicional
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Informações de propriedade
SOFTWARE_INFO = {
    'name': 'Sistema Imobiliário - ImobilPro',
    'version': '1.0.0',
    'copyright': '© 2024 - Todos os direitos reservados',
    'license': 'Proprietária',
    'author': 'Proprietário Exclusivo',
    'contact': 'Consulte documentação para contato',
    'legal_notice': 'Uso não autorizado é crime previsto em lei'
}

