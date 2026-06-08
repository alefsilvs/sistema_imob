#!/bin/bash

# Script de Deploy Automatizado - Sistema Imobiliário
# Autor: Sistema ImobilPro
# Versão: 1.0

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_NAME="sistema-imobiliario"
APP_USER="imobiliario"
APP_DIR="/opt/imobiliario"
APP_PATH="$APP_DIR/app"
VENV_PATH="$APP_PATH/venv"
LOGS_DIR="$APP_DIR/logs"
BACKUP_DIR="$APP_DIR/backups"
STATIC_DIR="$APP_DIR/static"
MEDIA_DIR="$APP_DIR/media"

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

# Verificar se é root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "Este script não deve ser executado como root!"
    fi
}

# Verificar dependências
check_dependencies() {
    log "Verificando dependências..."
    
    command -v python3.12 >/dev/null 2>&1 || error "Python 3.12 não encontrado"
    command -v pip >/dev/null 2>&1 || error "pip não encontrado"
    command -v psql >/dev/null 2>&1 || error "PostgreSQL não encontrado"
    command -v nginx >/dev/null 2>&1 || error "Nginx não encontrado"
    command -v node >/dev/null 2>&1 || error "Node.js não encontrado"
    command -v npm >/dev/null 2>&1 || error "npm não encontrado"
    
    log "Todas as dependências encontradas!"
}

# Configurar usuário do sistema
setup_user() {
    log "Configurando usuário do sistema..."
    
    if ! id "$APP_USER" &>/dev/null; then
        sudo adduser --system --group --home $APP_DIR $APP_USER
        log "Usuário $APP_USER criado"
    else
        info "Usuário $APP_USER já existe"
    fi
    
    sudo mkdir -p $APP_DIR $LOGS_DIR $BACKUP_DIR $STATIC_DIR $MEDIA_DIR
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
}

# Configurar banco de dados
setup_database() {
    log "Configurando banco de dados PostgreSQL..."
    
    # Verificar se o banco já existe
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw sistema_imobiliario; then
        warning "Banco de dados já existe"
        return
    fi
    
    # Criar banco e usuário
    sudo -u postgres psql << EOF
CREATE DATABASE sistema_imobiliario;
CREATE USER imobiliario_user WITH PASSWORD 'senha_super_segura_123';
GRANT ALL PRIVILEGES ON DATABASE sistema_imobiliario TO imobiliario_user;
ALTER USER imobiliario_user CREATEDB;
\q
EOF
    
    log "Banco de dados configurado!"
}

# Configurar aplicação
setup_application() {
    log "Configurando aplicação Django..."
    
    # Mudar para usuário da aplicação
    sudo -u $APP_USER bash << EOF
cd $APP_PATH

# Criar ambiente virtual se não existir
if [ ! -d "$VENV_PATH" ]; then
    python3.12 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Executar migrações
python manage.py migrate --settings=sistema_imobiliario.settings_production

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production

# Criar superusuário se não existir
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@exemplo.com', 'admin123')" | python manage.py shell --settings=sistema_imobiliario.settings_production

EOF
    
    log "Aplicação configurada!"
}

# Configurar Gunicorn
setup_gunicorn() {
    log "Configurando Gunicorn..."
    
    # Criar arquivo de configuração do Gunicorn
    sudo -u $APP_USER tee $APP_DIR/gunicorn.conf.py > /dev/null << EOF
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5
user = "$APP_USER"
group = "$APP_USER"
tmp_upload_dir = None
logfile = "$LOGS_DIR/gunicorn.log"
loglevel = "info"
access_logfile = "$LOGS_DIR/gunicorn_access.log"
error_logfile = "$LOGS_DIR/gunicorn_error.log"
EOF
    
    # Criar serviço systemd
    sudo tee /etc/systemd/system/gunicorn-$APP_NAME.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_PATH
Environment="PATH=$VENV_PATH/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_PATH/bin/gunicorn --config $APP_DIR/gunicorn.conf.py sistema_imobiliario.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    log "Gunicorn configurado!"
}

# Configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    # Criar configuração do Nginx
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Arquivos estáticos
    location /static/ {
        alias /opt/imobiliario/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /opt/imobiliario/media/;
        expires 30d;
    }
    
    # Aplicação Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Logs
    access_log /var/log/nginx/imobiliario_access.log;
    error_log /var/log/nginx/imobiliario_error.log;
}
EOF
    
    # Ativar site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Testar configuração
    sudo nginx -t || error "Erro na configuração do Nginx"
    
    log "Nginx configurado!"
}

# Configurar Evolution API
setup_evolution_api() {
    log "Configurando Evolution API..."
    
    # Clonar Evolution API se não existir
    if [ ! -d "$APP_DIR/evolution-api" ]; then
        sudo -u $APP_USER git clone https://github.com/EvolutionAPI/evolution-api.git $APP_DIR/evolution-api
    fi
    
    # Instalar dependências
    sudo -u $APP_USER bash << EOF
cd $APP_DIR/evolution-api
npm install
EOF
    
    # Criar arquivo .env
    sudo -u $APP_USER tee $APP_DIR/evolution-api/.env > /dev/null << EOF
# Servidor
SERVER_PORT=8080
SERVER_URL=http://localhost

# Banco de dados
DATABASE_ENABLED=true
DATABASE_CONNECTION_URI=postgresql://imobiliario_user:senha_super_segura_123@localhost:5432/evolution_api

# Autenticação
AUTHENTICATION_TYPE=apikey
AUTHENTICATION_API_KEY=sua_chave_api_super_segura

# Webhook
WEBHOOK_GLOBAL_URL=http://localhost/api/webhook/whatsapp/
WEBHOOK_GLOBAL_ENABLED=true

# Logs
LOG_LEVEL=info
LOG_COLOR=true
EOF
    
    # Criar banco para Evolution API
    sudo -u postgres psql << EOF
CREATE DATABASE evolution_api;
GRANT ALL PRIVILEGES ON DATABASE evolution_api TO imobiliario_user;
\q
EOF
    
    # Criar serviço systemd
    sudo tee /etc/systemd/system/evolution-api.service > /dev/null << EOF
[Unit]
Description=Evolution API WhatsApp
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR/evolution-api
EnvironmentFile=$APP_DIR/evolution-api/.env
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    log "Evolution API configurada!"
}

# Criar arquivo .env
setup_env() {
    log "Criando arquivo de ambiente..."
    
    sudo -u $APP_USER tee $APP_DIR/.env > /dev/null << EOF
# Django
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_production
SECRET_KEY=sua_chave_secreta_super_longa_e_segura_$(openssl rand -hex 32)

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# WhatsApp
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_chave_api_super_segura
WHATSAPP_INSTANCE_NAME=sistema_imobiliario

# Banco de dados
DB_NAME=sistema_imobiliario
DB_USER=imobiliario_user
DB_PASSWORD=senha_super_segura_123
DB_HOST=localhost
DB_PORT=5432
EOF
    
    log "Arquivo .env criado!"
}

# Configurar backup
setup_backup() {
    log "Configurando sistema de backup..."
    
    # Criar script de backup
    sudo -u $APP_USER tee $APP_DIR/backup.sh > /dev/null << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/imobiliario/backups"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump -U imobiliario_user -h localhost sistema_imobiliario > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos de media
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /opt/imobiliario/media/

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
EOF
    
    sudo chmod +x $APP_DIR/backup.sh
    
    # Adicionar ao cron
    (sudo -u $APP_USER crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh >> $LOGS_DIR/backup.log 2>&1") | sudo -u $APP_USER crontab -
    
    log "Sistema de backup configurado!"
}

# Iniciar serviços
start_services() {
    log "Iniciando serviços..."
    
    # Recarregar systemd
    sudo systemctl daemon-reload
    
    # Habilitar e iniciar serviços
    sudo systemctl enable gunicorn-$APP_NAME
    sudo systemctl enable evolution-api
    sudo systemctl enable nginx
    sudo systemctl enable postgresql
    
    sudo systemctl start postgresql
    sudo systemctl start gunicorn-$APP_NAME
    sudo systemctl start evolution-api
    sudo systemctl restart nginx
    
    # Verificar status
    sleep 5
    
    if sudo systemctl is-active --quiet gunicorn-$APP_NAME; then
        log "✓ Gunicorn está rodando"
    else
        error "✗ Gunicorn falhou ao iniciar"
    fi
    
    if sudo systemctl is-active --quiet evolution-api; then
        log "✓ Evolution API está rodando"
    else
        warning "✗ Evolution API falhou ao iniciar (verifique logs)"
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        log "✓ Nginx está rodando"
    else
        error "✗ Nginx falhou ao iniciar"
    fi
    
    log "Serviços iniciados!"
}

# Mostrar informações finais
show_info() {
    log "\n=== DEPLOY CONCLUÍDO ==="
    info "Sistema: $APP_NAME"
    info "Usuário: $APP_USER"
    info "Diretório: $APP_DIR"
    info "URL: http://localhost (ou IP do servidor)"
    info "Admin: http://localhost/admin (admin/admin123)"
    info "\nPróximos passos:"
    info "1. Configure seu domínio no arquivo /etc/nginx/sites-available/$APP_NAME"
    info "2. Configure SSL com: sudo certbot --nginx -d seu-dominio.com"
    info "3. Edite $APP_DIR/.env com suas configurações de email"
    info "4. Configure a instância do WhatsApp na Evolution API"
    info "\nLogs importantes:"
    info "- Django: $LOGS_DIR/django.log"
    info "- Gunicorn: $LOGS_DIR/gunicorn.log"
    info "- Nginx: /var/log/nginx/imobiliario_*.log"
    info "\nComandos úteis:"
    info "- Reiniciar app: sudo systemctl restart gunicorn-$APP_NAME"
    info "- Ver logs: sudo journalctl -u gunicorn-$APP_NAME -f"
    info "- Backup manual: $APP_DIR/backup.sh"
}

# Função principal
main() {
    log "Iniciando deploy do Sistema Imobiliário..."
    
    check_root
    check_dependencies
    setup_user
    setup_database
    setup_application
    setup_gunicorn
    setup_nginx
    setup_evolution_api
    setup_env
    setup_backup
    start_services
    show_info
    
    log "\n🎉 Deploy concluído com sucesso!"
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi