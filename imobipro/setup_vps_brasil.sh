#!/bin/bash

# ========================================
# CONFIGURAÇÃO VPS NACIONAL BRASILEIRO
# Sistema Imobiliário - ImobilPro
# Otimizado para: KingHost, Locaweb, Hostinger BR
# ========================================

echo "🇧🇷 Configurando VPS Nacional Brasileiro..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%d/%m/%Y %H:%M:%S')]${NC} $1"
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
    error "Execute como root: sudo bash setup_vps_brasil.sh"
    exit 1
fi

log "🇧🇷 Iniciando configuração para VPS Nacional..."

# Configurar timezone para Brasil
log "🕐 Configurando timezone para São Paulo..."
timedatectl set-timezone America/Sao_Paulo

# Configurar locale para português brasileiro
log "🌍 Configurando idioma para português brasileiro..."
locale-gen pt_BR.UTF-8
update-locale LANG=pt_BR.UTF-8

# Atualizar repositórios para mirrors brasileiros (Ubuntu)
if [ -f /etc/lsb-release ]; then
    log "📦 Configurando repositórios brasileiros..."
    cp /etc/apt/sources.list /etc/apt/sources.list.backup
    sed -i 's/archive.ubuntu.com/br.archive.ubuntu.com/g' /etc/apt/sources.list
    sed -i 's/security.ubuntu.com/br.archive.ubuntu.com/g' /etc/apt/sources.list
fi

log "📦 Atualizando sistema..."
apt update && apt upgrade -y

log "🐍 Instalando Python e dependências..."
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y postgresql postgresql-contrib
apt install -y nginx
apt install -y git curl wget unzip htop
apt install -y supervisor
apt install -y certbot python3-certbot-nginx
apt install -y ufw fail2ban

log "📱 Instalando Node.js LTS..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt install -y nodejs

log "🗄️ Configurando PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Configurar PostgreSQL com senha segura
POSTGRES_PASSWORD=$(openssl rand -base64 32)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';"
sudo -u postgres createuser --interactive --pwprompt sistema_imo_user
sudo -u postgres createdb -O sistema_imo_user sistema_imo_db

log "📁 Criando estrutura de diretórios..."
mkdir -p /opt/sistema_imobiliario
mkdir -p /opt/backups/sistema_imobiliario
mkdir -p /var/log/sistema_imobiliario
mkdir -p /etc/sistema_imobiliario

log "👤 Configurando usuário da aplicação..."
useradd --system --shell /bin/bash --home /opt/sistema_imobiliario --create-home sistema_imo
usermod -a -G www-data sistema_imo

log "🔐 Configurando permissões..."
chown -R sistema_imo:www-data /opt/sistema_imobiliario
chown -R sistema_imo:www-data /var/log/sistema_imobiliario
chmod -R 755 /opt/sistema_imobiliario

log "📥 Clonando repositório..."
cd /opt/sistema_imobiliario
# Substitua pela URL do seu repositório
sudo -u sistema_imo git clone https://github.com/SEU_USUARIO/sistema-imobiliario.git .

log "🐍 Configurando ambiente virtual Python..."
sudo -u sistema_imo python3 -m venv .venv
sudo -u sistema_imo .venv/bin/pip install --upgrade pip
sudo -u sistema_imo .venv/bin/pip install gunicorn
sudo -u sistema_imo .venv/bin/pip install -r requirements.txt

log "📱 Configurando Evolution API..."
cd /opt/sistema_imobiliario/evolution-api
sudo -u sistema_imo npm install --production

log "⚙️ Configurando Gunicorn..."
cat > /etc/systemd/system/gunicorn.service << 'EOF'
[Unit]
Description=Gunicorn instance to serve Sistema Imobiliário
After=network.target

[Service]
User=sistema_imo
Group=www-data
WorkingDirectory=/opt/sistema_imobiliario
Environment="PATH=/opt/sistema_imobiliario/.venv/bin"
Environment="DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings"
ExecStart=/opt/sistema_imobiliario/.venv/bin/gunicorn --workers 3 --bind unix:/opt/sistema_imobiliario/gunicorn.sock sistema_imobiliario.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log "📱 Configurando Evolution API como serviço..."
cat > /etc/systemd/system/evolution-api.service << 'EOF'
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

log "🌐 Configurando Nginx para domínio brasileiro..."
cat > /etc/nginx/sites-available/sistema_imobiliario << 'EOF'
server {
    listen 80;
    server_name SEU_DOMINIO.com.br www.SEU_DOMINIO.com.br;

    # Logs específicos
    access_log /var/log/nginx/sistema_imo_access.log;
    error_log /var/log/nginx/sistema_imo_error.log;

    # Configurações de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Favicon
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    # Arquivos estáticos
    location /static/ {
        alias /opt/sistema_imobiliario/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Arquivos de mídia
    location /media/ {
        alias /opt/sistema_imobiliario/media/;
        expires 7d;
    }

    # Evolution API
    location /evolution/ {
        proxy_pass http://localhost:8081/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Aplicação Django
    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/sistema_imobiliario/gunicorn.sock;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Bloquear acesso a arquivos sensíveis
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|git|svn)$ {
        deny all;
    }
}
EOF

ln -s /etc/nginx/sites-available/sistema_imobiliario /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

log "🔄 Configurando webhook de deploy..."
cat > /etc/systemd/system/webhook-deploy.service << 'EOF'
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
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log "🔥 Configurando firewall brasileiro..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp  # Webhook
ufw --force enable

log "🛡️ Configurando Fail2Ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl start fail2ban

log "📊 Configurando monitoramento..."
cat > /opt/sistema_imobiliario/monitor_sistema.sh << 'EOF'
#!/bin/bash
# Monitor do sistema para VPS brasileiro

LOG_FILE="/var/log/sistema_imobiliario/monitor.log"
DATE=$(date '+%d/%m/%Y %H:%M:%S')

# Verificar uso de CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')

# Verificar uso de memória
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')

# Verificar espaço em disco
DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}')

# Verificar se serviços estão rodando
GUNICORN_STATUS=$(systemctl is-active gunicorn)
EVOLUTION_STATUS=$(systemctl is-active evolution-api)
NGINX_STATUS=$(systemctl is-active nginx)

echo "[$DATE] CPU: ${CPU_USAGE}% | MEM: ${MEM_USAGE}% | DISK: ${DISK_USAGE} | Gunicorn: $GUNICORN_STATUS | Evolution: $EVOLUTION_STATUS | Nginx: $NGINX_STATUS" >> $LOG_FILE

# Alertar se CPU > 80%
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "[$DATE] ALERTA: CPU alta - ${CPU_USAGE}%" >> $LOG_FILE
fi

# Alertar se memória > 85%
if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
    echo "[$DATE] ALERTA: Memória alta - ${MEM_USAGE}%" >> $LOG_FILE
fi
EOF

chmod +x /opt/sistema_imobiliario/monitor_sistema.sh

# Configurar cron para monitoramento
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/sistema_imobiliario/monitor_sistema.sh") | crontab -

log "🔧 Habilitando e iniciando serviços..."
systemctl daemon-reload
systemctl enable gunicorn
systemctl enable evolution-api
systemctl enable webhook-deploy
systemctl enable nginx

# Testar configuração do Nginx
nginx -t

if [ $? -eq 0 ]; then
    systemctl start gunicorn
    systemctl start evolution-api
    systemctl start webhook-deploy
    systemctl restart nginx
    log "✅ Todos os serviços iniciados com sucesso!"
else
    error "❌ Erro na configuração do Nginx!"
    exit 1
fi

log "📝 Criando arquivo de configuração..."
cat > /etc/sistema_imobiliario/config.txt << EOF
# Configuração do Sistema Imobiliário
# VPS Nacional Brasileiro
# Data de instalação: $(date '+%d/%m/%Y %H:%M:%S')

POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SISTEMA_PATH=/opt/sistema_imobiliario
BACKUP_PATH=/opt/backups/sistema_imobiliario
LOG_PATH=/var/log/sistema_imobiliario

# Próximos passos:
# 1. Configure o arquivo .env
# 2. Execute: python manage.py migrate
# 3. Crie superusuário: python manage.py createsuperuser
# 4. Configure SSL: certbot --nginx -d SEU_DOMINIO.com.br
# 5. Configure webhook no GitHub/GitLab
EOF

log "✅ Configuração VPS Nacional concluída!"
info "🌐 Acesse: http://SEU_DOMINIO.com.br"
info "📱 Evolution API: http://SEU_DOMINIO.com.br/evolution/manager"
info "🔄 Webhook: http://SEU_DOMINIO.com.br:5000/webhook/deploy"

echo ""
log "📋 PRÓXIMOS PASSOS OBRIGATÓRIOS:"
echo "1. 📝 Configure o arquivo .env:"
echo "   nano /opt/sistema_imobiliario/.env"
echo ""
echo "2. 🗄️ Execute as migrações:"
echo "   cd /opt/sistema_imobiliario"
echo "   source .venv/bin/activate"
echo "   python manage.py migrate"
echo ""
echo "3. 👤 Crie um superusuário:"
echo "   python manage.py createsuperuser"
echo ""
echo "4. 🔒 Configure SSL (Let's Encrypt):"
echo "   certbot --nginx -d SEU_DOMINIO.com.br"
echo ""
echo "5. 🔄 Configure webhook no GitHub/GitLab:"
echo "   URL: http://SEU_DOMINIO.com.br:5000/webhook/deploy"
echo "   Secret: sistema_imo_webhook_secret_2024"

echo ""
warning "⚠️ IMPORTANTE:"
echo "- Senha do PostgreSQL salva em: /etc/sistema_imobiliario/config.txt"
echo "- Logs do sistema em: /var/log/sistema_imobiliario/"
echo "- Backups automáticos em: /opt/backups/sistema_imobiliario/"
echo "- Monitoramento ativo a cada 5 minutos"

echo ""
info "🇧🇷 VPS Nacional configurado com sucesso!"
info "📞 Suporte: Verifique documentação em DEPLOY_GUIDE.md"