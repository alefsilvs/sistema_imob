#!/bin/bash

# Script de Configuração SSL/HTTPS com Let's Encrypt
# Sistema Imobiliário - Produção

set -e

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

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
   error "Este script deve ser executado como root (use sudo)"
fi

# Verificar argumentos
if [ $# -lt 1 ]; then
    echo "Uso: $0 <dominio> [email]"
    echo "Exemplo: $0 meusite.com.br admin@meusite.com.br"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}
APP_USER="imobiliario"
APP_DIR="/home/$APP_USER/sistema-imobiliario"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

log "Iniciando configuração SSL/HTTPS para $DOMAIN"
log "Email para certificado: $EMAIL"

# Função para verificar se um comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Instalar Certbot se não existir
install_certbot() {
    log "Instalando Certbot..."
    
    # Atualizar repositórios
    apt update
    
    # Instalar snapd se não existir
    if ! command_exists snap; then
        apt install -y snapd
        systemctl enable snapd
        systemctl start snapd
    fi
    
    # Instalar certbot via snap
    snap install core; snap refresh core
    snap install --classic certbot
    
    # Criar link simbólico
    ln -sf /snap/bin/certbot /usr/bin/certbot
    
    log "Certbot instalado com sucesso"
}

# Configurar Nginx para HTTP (temporário)
configure_nginx_http() {
    log "Configurando Nginx para HTTP temporário..."
    
    cat > "$NGINX_AVAILABLE/imobiliario" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Permitir acesso ao .well-known para validação SSL
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirecionar todo o resto para HTTPS (será configurado depois)
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
    
    # Ativar site
    ln -sf "$NGINX_AVAILABLE/imobiliario" "$NGINX_ENABLED/"
    
    # Remover configuração padrão se existir
    rm -f "$NGINX_ENABLED/default"
    
    # Testar configuração
    nginx -t || error "Erro na configuração do Nginx"
    
    # Recarregar Nginx
    systemctl reload nginx
    
    log "Nginx configurado para HTTP"
}

# Obter certificado SSL
obtain_ssl_certificate() {
    log "Obtendo certificado SSL do Let's Encrypt..."
    
    # Criar diretório para validação
    mkdir -p /var/www/html/.well-known/acme-challenge
    chown -R www-data:www-data /var/www/html
    
    # Obter certificado
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN,www.$DOMAIN" \
        --non-interactive
    
    if [ $? -eq 0 ]; then
        log "Certificado SSL obtido com sucesso"
    else
        error "Falha ao obter certificado SSL"
    fi
}

# Configurar Nginx com SSL
configure_nginx_ssl() {
    log "Configurando Nginx com SSL..."
    
    # Gerar parâmetros DH para segurança extra
    if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
        log "Gerando parâmetros Diffie-Hellman (isso pode demorar)..."
        openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
    fi
    
    cat > "$NGINX_AVAILABLE/imobiliario" << EOF
# Redirecionar HTTP para HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

# Configuração HTTPS
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configurações SSL modernas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Outras headers de segurança
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https:; frame-src 'self';" always;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Diffie-Hellman
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # Configurações do site
    client_max_body_size 100M;
    
    # Logs
    access_log /var/log/nginx/imobiliario_access.log;
    error_log /var/log/nginx/imobiliario_error.log;
    
    # Arquivos estáticos
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        gzip_static on;
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Favicon
    location = /favicon.ico {
        alias $APP_DIR/staticfiles/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Robots.txt
    location = /robots.txt {
        alias $APP_DIR/staticfiles/robots.txt;
        expires 1d;
    }
    
    # Proxy para Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # WebSocket support (se necessário)
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Bloquear acesso a arquivos sensíveis
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~\$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
EOF
    
    # Testar configuração
    nginx -t || error "Erro na configuração SSL do Nginx"
    
    # Recarregar Nginx
    systemctl reload nginx
    
    log "Nginx configurado com SSL"
}

# Configurar renovação automática
setup_auto_renewal() {
    log "Configurando renovação automática do certificado..."
    
    # Criar script de renovação
    cat > /etc/cron.d/certbot-renew << EOF
# Renovar certificados Let's Encrypt automaticamente
0 12 * * * root /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
    
    # Testar renovação
    certbot renew --dry-run
    
    if [ $? -eq 0 ]; then
        log "Renovação automática configurada com sucesso"
    else
        warn "Teste de renovação falhou, mas o certificado foi instalado"
    fi
}

# Configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    
    if command_exists ufw; then
        # Permitir HTTP e HTTPS
        ufw allow 'Nginx Full'
        ufw allow 'OpenSSH'
        
        # Ativar firewall se não estiver ativo
        ufw --force enable
        
        log "Firewall configurado"
    else
        warn "UFW não encontrado, configure o firewall manualmente"
    fi
}

# Verificar status dos serviços
check_services() {
    log "Verificando status dos serviços..."
    
    # Verificar Nginx
    if systemctl is-active --quiet nginx; then
        log "✓ Nginx está rodando"
    else
        error "✗ Nginx não está rodando"
    fi
    
    # Verificar certificado
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        log "✓ Certificado SSL encontrado"
        
        # Mostrar informações do certificado
        CERT_EXPIRY=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
        log "✓ Certificado expira em: $CERT_EXPIRY"
    else
        error "✗ Certificado SSL não encontrado"
    fi
}

# Função principal
main() {
    log "=== Configuração SSL/HTTPS - Sistema Imobiliário ==="
    
    # Verificar se Nginx está instalado
    if ! command_exists nginx; then
        error "Nginx não está instalado. Execute o script de deploy primeiro."
    fi
    
    # Verificar se o domínio resolve para este servidor
    log "Verificando DNS para $DOMAIN..."
    DOMAIN_IP=$(dig +short "$DOMAIN" | tail -n1)
    SERVER_IP=$(curl -s ifconfig.me)
    
    if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
        warn "O domínio $DOMAIN não aponta para este servidor ($SERVER_IP)"
        warn "IP do domínio: $DOMAIN_IP"
        warn "Certifique-se de que o DNS está configurado corretamente"
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "✓ DNS configurado corretamente"
    fi
    
    # Instalar Certbot
    if ! command_exists certbot; then
        install_certbot
    else
        log "Certbot já está instalado"
    fi
    
    # Configurar Nginx para HTTP temporário
    configure_nginx_http
    
    # Obter certificado SSL
    obtain_ssl_certificate
    
    # Configurar Nginx com SSL
    configure_nginx_ssl
    
    # Configurar renovação automática
    setup_auto_renewal
    
    # Configurar firewall
    setup_firewall
    
    # Verificar serviços
    check_services
    
    log "=== Configuração SSL/HTTPS concluída com sucesso! ==="
    log ""
    log "Seu site agora está disponível em:"
    log "  https://$DOMAIN"
    log "  https://www.$DOMAIN"
    log ""
    log "Comandos úteis:"
    log "  - Verificar status do certificado: certbot certificates"
    log "  - Renovar certificados: certbot renew"
    log "  - Testar renovação: certbot renew --dry-run"
    log "  - Ver logs do Nginx: tail -f /var/log/nginx/imobiliario_error.log"
    log "  - Recarregar Nginx: systemctl reload nginx"
    log ""
    log "O certificado será renovado automaticamente a cada 12h."
}

# Executar função principal
main "$@"