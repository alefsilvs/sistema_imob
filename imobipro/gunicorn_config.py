# Configuração do Gunicorn para Sistema Imobiliário - Produção
# Arquivo: /home/imobiliario/sistema-imobiliario/gunicorn_config.py

import multiprocessing
import os
from pathlib import Path

# Configurações básicas
bind = "127.0.0.1:8000"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Timeouts
timeout = 30
keepalive = 2
graceful_timeout = 30

# Usuário e grupo
user = "imobiliario"
group = "imobiliario"

# Diretórios
chdir = "/home/imobiliario/sistema-imobiliario"
pidfile = "/home/imobiliario/sistema-imobiliario/gunicorn.pid"

# Logs
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Captura de saída
capture_output = True
enable_stdio_inheritance = True

# Daemon
daemon = False

# Configurações de processo
proc_name = "gunicorn_imobiliario"

# SSL (se necessário para comunicação direta)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Configurações de desenvolvimento (desabilitar em produção)
reload = False
reload_engine = "auto"

# Configurações de memória
max_requests_jitter = 50
worker_tmp_dir = "/dev/shm"

# Hooks para logging e monitoramento
def when_ready(server):
    """Executado quando o servidor está pronto para aceitar conexões"""
    server.log.info("Servidor Gunicorn pronto para aceitar conexões")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Bind: {bind}")
    server.log.info(f"PID: {os.getpid()}")

def worker_int(worker):
    """Executado quando um worker recebe SIGINT ou SIGQUIT"""
    worker.log.info(f"Worker {worker.pid} interrompido")

def pre_fork(server, worker):
    """Executado antes de fazer fork de um worker"""
    server.log.info(f"Iniciando worker {worker.age}")

def post_fork(server, worker):
    """Executado após fazer fork de um worker"""
    server.log.info(f"Worker {worker.pid} iniciado")

def pre_exec(server):
    """Executado antes de executar um novo processo"""
    server.log.info("Executando novo processo Gunicorn")

def on_exit(server):
    """Executado quando o servidor está saindo"""
    server.log.info("Servidor Gunicorn finalizando")

def on_reload(server):
    """Executado quando o servidor é recarregado"""
    server.log.info("Servidor Gunicorn recarregado")

def worker_abort(worker):
    """Executado quando um worker é abortado"""
    worker.log.info(f"Worker {worker.pid} abortado")

# Configurações específicas para Django
raw_env = [
    'DJANGO_SETTINGS_MODULE=core.settings_production',
    'PYTHONPATH=/home/imobiliario/sistema-imobiliario',
]

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de performance
worker_tmp_dir = "/dev/shm"  # Usar RAM para arquivos temporários

# Configurações de SSL/TLS (se necessário)
# ssl_version = 2  # SSLv23
# ciphers = 'TLSv1'
# ca_certs = '/path/to/ca_certs'
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# check_hostname = False

# Configurações de proxy
forwarded_allow_ips = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
proxy_protocol = False
proxy_allow_ips = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# Configurações de thread (para worker_class = "gthread")
# threads = 2
# thread_timeout = 30

# Configurações de async (para worker_class = "gevent" ou "eventlet")
# worker_connections = 1000

# Configurações de estatísticas
statsd_host = None
statsd_prefix = ""

# Configurações de logging estruturado
logconfig_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(message)s',
            'datefmt': '[%Y-%m-%d %H:%M:%S %z]',
            'class': 'logging.Formatter',
        },
        'access': {
            'format': '%(message)s',
            'class': 'logging.Formatter',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
        },
        'error_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'generic',
            'filename': '/var/log/gunicorn/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'access_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'access',
            'filename': '/var/log/gunicorn/access.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'gunicorn.error': {
            'level': 'INFO',
            'handlers': ['console', 'error_file'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'INFO',
            'handlers': ['access_file'],
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    }
}

# Configurações específicas por ambiente
if os.getenv('ENVIRONMENT') == 'development':
    reload = True
    loglevel = 'debug'
    workers = 1
    timeout = 120
elif os.getenv('ENVIRONMENT') == 'staging':
    workers = 2
    loglevel = 'info'
elif os.getenv('ENVIRONMENT') == 'production':
    workers = multiprocessing.cpu_count() * 2 + 1
    loglevel = 'warning'
    preload_app = True

# Configurações de monitoramento
def post_worker_init(worker):
    """Executado após inicialização do worker"""
    from django.core.management import execute_from_command_line
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_production')
    django.setup()
    
    worker.log.info(f"Worker {worker.pid} inicializado com Django")

# Configurações de health check
def worker_exit(server, worker):
    """Executado quando um worker sai"""
    server.log.info(f"Worker {worker.pid} finalizando")

# Configurações de graceful shutdown
def on_starting(server):
    """Executado quando o servidor está iniciando"""
    server.log.info("Iniciando servidor Gunicorn")
    
    # Criar diretórios de log se não existirem
    log_dir = Path("/var/log/gunicorn")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Definir permissões
    os.chmod(log_dir, 0o755)

# Configurações de reload
def nworkers_changed(server, new_value, old_value):
    """Executado quando o número de workers muda"""
    server.log.info(f"Número de workers alterado de {old_value} para {new_value}")

# Configurações de erro
def worker_connections_changed(server, new_value, old_value):
    """Executado quando worker_connections muda"""
    server.log.info(f"Worker connections alterado de {old_value} para {new_value}")

# Configurações de performance para diferentes cargas
if os.getenv('HIGH_TRAFFIC') == 'true':
    workers = multiprocessing.cpu_count() * 4
    worker_connections = 2000
    max_requests = 2000
    timeout = 60
    keepalive = 5

# Configurações de debug (apenas desenvolvimento)
if os.getenv('DEBUG') == 'true':
    reload = True
    loglevel = 'debug'
    timeout = 300
    workers = 1

# Configurações de teste de carga
if os.getenv('LOAD_TEST') == 'true':
    workers = multiprocessing.cpu_count() * 8
    worker_connections = 5000
    max_requests = 5000
    timeout = 120

# Configurações de backup/failover
if os.getenv('BACKUP_MODE') == 'true':
    workers = 1
    timeout = 300
    max_requests = 100

# Configurações de manutenção
if os.getenv('MAINTENANCE_MODE') == 'true':
    workers = 1
    timeout = 60
    max_requests = 50

print(f"Configuração Gunicorn carregada:")
print(f"  Workers: {workers}")
print(f"  Bind: {bind}")
print(f"  Timeout: {timeout}")
print(f"  Log Level: {loglevel}")
print(f"  Preload App: {preload_app}")
print(f"  Max Requests: {max_requests}")