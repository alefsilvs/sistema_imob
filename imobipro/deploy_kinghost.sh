#!/bin/bash

# Script de Deploy para KingHost - Sistema Imobiliário
# Copyright (c) 2024 - Todos os direitos reservados

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do Sistema Imobiliário na KingHost..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar se está rodando como usuário correto
if [ "$EUID" -eq 0 ]; then
    error "Não execute este script como root. Use o usuário da aplicação."
fi

# Configurações
APP_NAME="sistema_imo"
APP_DIR="/home/$(whoami)/apps/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
STATIC_DIR="/home/$(whoami)/public_html/static"
MEDIA_DIR="/home/$(whoami)/public_html/media"
LOG_DIR="/home/$(whoami)/logs"
BACKUP_DIR="/home/$(whoami)/backups"

# Verificar se o arquivo .env existe
if [ ! -f "$APP_DIR/.env" ]; then
    warning "Arquivo .env não encontrado. Criando template..."
    cat > "$APP_DIR/.env" << EOF
# Configurações de Produção - KingHost
SECRET_KEY=GERE_UMA_CHAVE_SECRETA_MUITO_LONGA_E_SEGURA_AQUI
DEBUG=False

# Domínio
DOMAIN_NAME=seu-dominio.com.br
SERVER_IP=IP_DO_SEU_SERVIDOR

# Banco de Dados PostgreSQL
DB_NAME=sistema_imobiliario
DB_USER=postgres
DB_PASSWORD=SENHA_DO_BANCO
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Email
EMAIL_USER=noreply@seu-dominio.com.br
EMAIL_PASSWORD=SENHA_DO_EMAIL

# Sentry (Opcional)
# SENTRY_DSN=https://...
EOF
    error "Configure o arquivo .env em $APP_DIR/.env antes de continuar!"
fi

log "Carregando configurações do .env..."
source "$APP_DIR/.env"

# Verificar variáveis obrigatórias
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "GERE_UMA_CHAVE_SECRETA_MUITO_LONGA_E_SEGURA_AQUI" ]; then
    error "SECRET_KEY não configurada no arquivo .env"
fi

if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "SENHA_DO_BANCO" ]; then
    error "DB_PASSWORD não configurada no arquivo .env"
fi

# Função para criar diretórios
create_directories() {
    log "Criando diretórios necessários..."
    mkdir -p "$STATIC_DIR"
    mkdir -p "$MEDIA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$APP_DIR/staticfiles"
}

# Função para configurar ambiente virtual
setup_virtualenv() {
    log "Configurando ambiente virtual..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    
    log "Atualizando pip..."
    pip install --upgrade pip
    
    log "Instalando dependências..."
    pip install -r "$APP_DIR/requirements.txt"
}

# Função para configurar banco de dados
setup_database() {
    log "Configurando banco de dados..."
    
    source "$VENV_DIR/bin/activate"
    cd "$APP_DIR"
    
    # Verificar conexão com banco
    python manage.py check --database default --settings=sistema_imobiliario.settings_production
    
    # Executar migrações
    log "Executando migrações..."
    python manage.py migrate --settings=sistema_imobiliario.settings_production
    
    # Coletar arquivos estáticos
    log "Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production
}

# Função para configurar Gunicorn
setup_gunicorn() {
    log "Configurando Gunicorn..."
    
    # Criar arquivo de configuração do Gunicorn
    cat > "$APP_DIR/gunicorn.conf.py" << EOF
# Configuração do Gunicorn para KingHost
import multiprocessing

# Servidor
bind = "unix:$APP_DIR/sistema_imo.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2

# Logging
accesslog = "$LOG_DIR/gunicorn_access.log"
errorlog = "$LOG_DIR/gunicorn_error.log"
loglevel = "info"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'

# Processo
user = "$(whoami)"
group = "www-data"
tmp_upload_dir = None
preload_app = True
daemon = False

# Segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
EOF

    # Criar arquivo de serviço systemd
    sudo tee /etc/systemd/system/$APP_NAME.service > /dev/null << EOF
[Unit]
Description=Sistema Imobiliário Gunicorn daemon
After=network.target

[Service]
User=$(whoami)
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
          --config $APP_DIR/gunicorn.conf.py \\
          sistema_imobiliario.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Recarregar systemd e iniciar serviço
    sudo systemctl daemon-reload
    sudo systemctl enable $APP_NAME
    sudo systemctl start $APP_NAME
    
    log "Verificando status do Gunicorn..."
    sudo systemctl status $APP_NAME --no-pager
}

# Função para configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    client_max_body_size 50M;
    
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias $STATIC_DIR/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        gzip_static on;
    }
    
    location /media/ {
        alias $MEDIA_DIR/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/sistema_imo.sock;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

    # Ativar site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Testar configuração
    sudo nginx -t
    
    # Recarregar Nginx
    sudo systemctl reload nginx
    
    log "Nginx configurado com sucesso!"
}

# Função para configurar SSL
setup_ssl() {
    log "Configurando SSL com Let's Encrypt..."
    
    if command -v certbot &> /dev/null; then
        sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
        log "SSL configurado com sucesso!"
    else
        warning "Certbot não encontrado. Instale com: sudo apt install certbot python3-certbot-nginx"
    fi
}

# Função para configurar backup
setup_backup() {
    log "Configurando sistema de backup..."
    
    cat > "$BACKUP_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Script de backup automático

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/$(whoami)/backups"
APP_DIR="/home/$(whoami)/apps/sistema_imo"

# Backup do banco de dados
pg_dump sistema_imobiliario > "$BACKUP_DIR/db_$DATE.sql"

# Backup dos arquivos de mídia
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C "/home/$(whoami)/public_html" media/

# Backup do código (sem venv)
tar --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    -czf "$BACKUP_DIR/code_$DATE.tar.gz" -C "$APP_DIR" .

# Manter apenas os últimos 7 backups
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
EOF

    chmod +x "$BACKUP_DIR/backup.sh"
    
    # Adicionar ao crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_DIR/backup.sh >> $LOG_DIR/backup.log 2>&1") | crontab -
    
    log "Sistema de backup configurado!"
}

# Função para verificar serviços
check_services() {
    log "Verificando serviços..."
    
    services=("postgresql" "redis-server" "nginx" "$APP_NAME")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            echo -e "✅ $service: ${GREEN}ATIVO${NC}"
        else
            echo -e "❌ $service: ${RED}INATIVO${NC}"
        fi
    done
}

# Função para mostrar informações finais
show_final_info() {
    log "Deploy concluído com sucesso! 🎉"
    echo
    echo "📋 Informações importantes:"
    echo "   • Aplicação: http://$DOMAIN_NAME"
    echo "   • Admin: http://$DOMAIN_NAME/admin/"
    echo "   • Logs: $LOG_DIR/"
    echo "   • Backups: $BACKUP_DIR/"
    echo
    echo "🔧 Comandos úteis:"
    echo "   • Reiniciar app: sudo systemctl restart $APP_NAME"
    echo "   • Ver logs: sudo journalctl -u $APP_NAME -f"
    echo "   • Backup manual: $BACKUP_DIR/backup.sh"
    echo
    echo "⚠️  Próximos passos:"
    echo "   1. Configure o DNS do domínio para apontar para este servidor"
    echo "   2. Crie um superusuário: python manage.py createsuperuser --settings=sistema_imobiliario.settings_production"
    echo "   3. Configure o SSL se ainda não foi feito"
    echo "   4. Teste todas as funcionalidades"
}

# Menu principal
case "${1:-all}" in
    "directories")
        create_directories
        ;;
    "venv")
        setup_virtualenv
        ;;
    "database")
        setup_database
        ;;
    "gunicorn")
        setup_gunicorn
        ;;
    "nginx")
        setup_nginx
        ;;
    "ssl")
        setup_ssl
        ;;
    "backup")
        setup_backup
        ;;
    "check")
        check_services
        ;;
    "all")
        create_directories
        setup_virtualenv
        setup_database
        setup_gunicorn
        setup_nginx
        setup_backup
        check_services
        show_final_info
        ;;
    *)
        echo "Uso: $0 [directories|venv|database|gunicorn|nginx|ssl|backup|check|all]"
        exit 1
        ;;
esac

log "Operação concluída!"