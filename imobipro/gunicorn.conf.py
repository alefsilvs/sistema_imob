# -*- coding: utf-8 -*-
"""
Configuração do Gunicorn para Sistema Imobiliário - KingHost
Copyright (c) 2024 - Todos os direitos reservados
"""

import multiprocessing
import os

# Configurações do servidor
bind = "unix:/home/sistema_imo/apps/sistema_imo/sistema_imo.sock"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeouts
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/home/sistema_imo/logs/gunicorn_access.log"
errorlog = "/home/sistema_imo/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Processo
user = "sistema_imo"
group = "www-data"
tmp_upload_dir = None
daemon = False
pidfile = "/home/sistema_imo/apps/sistema_imo/gunicorn.pid"

# Segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
worker_tmp_dir = "/dev/shm"  # Usar RAM para arquivos temporários

# Configurações específicas para KingHost
def when_ready(server):
    server.log.info("Servidor pronto - Sistema Imobiliário")

def worker_int(worker):
    worker.log.info("Worker recebeu INT ou QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")