#!/bin/bash

# ========================================
# SCRIPT DE CONFIGURAÇÃO INICIAL DO SERVIDOR
# Sistema Imobiliário - ImobilPro
# ========================================

echo "🚀 Configurando servidor para o Sistema Imobiliário..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log colorido
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    error "Este script deve ser executado como root (sudo)"
    exit 1
fi

log "📦 Atualizando sistema..."
apt update && apt upgrade -y

log "🐍 Instalando Python e dependências..."
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y postgresql postgresql-contrib
apt install -y nginx
apt install -y git curl wget unzip
apt install -y supervisor
apt install -y certbot python3-certbot-nginx

log "📱 Instalando Node.js para Evolution API..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

log "🗄️ Configurando PostgreSQL..."
sudo -u postgres createuser --interactive --pwprompt sistema_imo_user
sudo -u postgres createdb -O sistema_imo_user sistema_imo_db

log "📁 Criando estrutura de diretórios..."
mkdir -p /opt/sistema_imobiliario
mkdir -p /opt/backups/sistema_imobiliario
mkdir -p /var/log/sistema_imobiliario

log "👤 Configurando usuário da aplicação..."
useradd --system --shell /bin/bash --home /opt/sistema_imobiliario --create-home sistema_imo
usermod -a -G www-data sistema_imo

log "🔐 Configurando permissões..."
chown -R sistema_imo:www-data /opt/sistema_imobiliario
chown -R sistema_imo:www-data /var/log/sistema_imobiliario
chmod -R 755 /opt/sistema_imobiliario

log "📥 Clonando repositório..."
cd /opt/sistema_imobiliario
sudo -u sistema_imo git clone https://github.com/SEU_USUARIO/sistema-imobiliario.git .

log "🐍 Configurando ambiente virtual Python..."
sudo -u sistema_imo python3 -m venv .venv
sudo -u sistema_imo .venv/bin/pip install --upgrade pip
sudo -u sistema_imo .venv/bin/pip install -r requirements.txt

log "📱 Configurando Evolution API..."
cd /opt/sistema_imobiliario/evolution-api
sudo -u sistema_imo npm install

log "⚙️ Configurando Gunicorn..."
cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=Gunicorn instance to serve Sistema Imobiliário
After=network.target

[Service]
User=sistema_imo
Group=www-data
WorkingDirectory=/opt/sistema_imobiliario
Environment="PATH=/opt/sistema_imobiliario/.venv/bin"
ExecStart=/opt/sistema_imobiliario/.venv/bin/gunicorn --workers 3 --bind unix:/opt/sistema_imobiliario/gunicorn.sock core.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

log "📱 Configurando Evolution API como serviço..."
cat > /etc/systemd/system/evolution-api.service << EOF
[Unit]
Description=Evolution API WhatsApp
After=network.target

[Service]
Type=simple
User=sistema_imo
WorkingDirectory=/opt/sistema_imobiliario/evolution-api
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

log "🌐 Configurando Nginx..."
cat > /etc/nginx/sites-available/sistema_imobiliario << EOF
server {
    listen 80;
    server_name SEU_DOMINIO.com.br;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /opt/sistema_imobiliario;
    }
    
    location /media/ {
        root /opt/sistema_imobiliario;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/sistema_imobiliario/gunicorn.sock;
    }
    
    # Evolution API
    location /evolution/ {
        proxy_pass http://localhost:8081/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

ln -s /etc/nginx/sites-available/sistema_imobiliario /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

log "🔄 Configurando webhook de deploy..."
cat > /etc/systemd/system/webhook-deploy.service << EOF
[Unit]
Description=Webhook Deploy Sistema Imobiliário
After=network.target

[Service]
Type=simple
User=sistema_imo
WorkingDirectory=/opt/sistema_imobiliario
Environment="PATH=/opt/sistema_imobiliario/.venv/bin"
ExecStart=/opt/sistema_imobiliario/.venv/bin/python webhook_deploy.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

log "🔧 Habilitando e iniciando serviços..."
systemctl daemon-reload
systemctl enable gunicorn
systemctl enable evolution-api
systemctl enable webhook-deploy
systemctl enable nginx

systemctl start gunicorn
systemctl start evolution-api
systemctl start webhook-deploy
systemctl restart nginx

log "🔒 Configurando SSL (Let's Encrypt)..."
warning "Execute manualmente: certbot --nginx -d SEU_DOMINIO.com.br"

log "🔥 Configurando firewall..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 5000  # Webhook
ufw --force enable

log "✅ Configuração inicial concluída!"
info "🌐 Acesse: http://SEU_DOMINIO.com.br"
info "📱 Evolution API: http://SEU_DOMINIO.com.br/evolution/manager"
info "🔄 Webhook: http://SEU_DOMINIO.com.br:5000/webhook/deploy"

echo ""
log "📋 PRÓXIMOS PASSOS:"
echo "1. Configure o arquivo .env no servidor"
echo "2. Execute as migrações: python manage.py migrate"
echo "3. Crie um superusuário: python manage.py createsuperuser"
echo "4. Configure o webhook no GitHub/GitLab"
echo "5. Teste o deploy automático"

echo ""
warning "⚠️ IMPORTANTE:"
echo "- Altere as senhas padrão"
echo "- Configure backup automático"
echo "- Monitore os logs regularmente"