#!/bin/bash

# ========================================
# CONFIGURADOR DE DOMÍNIO .COM.BR
# Sistema Imobiliário - ImobilPro
# ========================================

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

warning() {
    echo -e "${YELLOW}[AVISO] $1${NC}"
}

error() {
    echo -e "${RED}[ERRO] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "=========================================="
echo "🇧🇷 CONFIGURADOR DE DOMÍNIO .COM.BR"
echo "Sistema Imobiliário - ImobilPro"
echo "=========================================="
echo -e "${NC}"

# Verificar se está rodando como root
if [[ $EUID -ne 0 ]]; then
   error "Este script deve ser executado como root (sudo)"
   exit 1
fi

# Solicitar informações do domínio
echo ""
info "📝 CONFIGURAÇÃO DO DOMÍNIO"
echo ""

read -p "🌐 Digite seu domínio (ex: meusite.com.br): " DOMAIN
read -p "📧 Digite seu email para SSL (ex: admin@$DOMAIN): " EMAIL

# Validar domínio
if [[ ! $DOMAIN =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
    error "Domínio inválido! Use o formato: exemplo.com.br"
    exit 1
fi

# Validar email
if [[ ! $EMAIL =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    error "Email inválido!"
    exit 1
fi

# Obter IP do servidor
SERVER_IP=$(curl -s ifconfig.me)
if [[ -z "$SERVER_IP" ]]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
fi

log "🔍 IP do servidor detectado: $SERVER_IP"

# Verificar se domínio aponta para este servidor
echo ""
info "🔍 VERIFICANDO CONFIGURAÇÃO DNS..."

DOMAIN_IP=$(dig +short $DOMAIN @8.8.8.8)
WWW_IP=$(dig +short www.$DOMAIN @8.8.8.8)

if [[ "$DOMAIN_IP" != "$SERVER_IP" ]]; then
    warning "⚠️  O domínio $DOMAIN não aponta para este servidor!"
    echo ""
    echo "📋 CONFIGURE SEU DNS COM ESTAS INFORMAÇÕES:"
    echo "   Tipo: A"
    echo "   Nome: @"
    echo "   Valor: $SERVER_IP"
    echo ""
    echo "   Tipo: A"
    echo "   Nome: www"
    echo "   Valor: $SERVER_IP"
    echo ""
    read -p "Pressione ENTER após configurar o DNS..." -r
fi

# Backup da configuração atual do Nginx
log "💾 Fazendo backup da configuração atual..."
cp /etc/nginx/sites-available/sistema_imo /etc/nginx/sites-available/sistema_imo.backup.$(date +%Y%m%d_%H%M%S)

# Configurar Nginx para o domínio
log "⚙️  Configurando Nginx para o domínio $DOMAIN..."

cat > /etc/nginx/sites-available/sistema_imo << EOF
# Configuração do Sistema Imobiliário - Domínio: $DOMAIN
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirecionar HTTP para HTTPS (será configurado após SSL)
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Configurações SSL (serão preenchidas pelo Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Configurações de segurança SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Headers de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Configurações do site
    root /opt/sistema_imobiliario;
    index index.html index.htm;
    
    # Tamanho máximo de upload
    client_max_body_size 100M;
    
    # Logs específicos do domínio
    access_log /var/log/nginx/${DOMAIN}_access.log;
    error_log /var/log/nginx/${DOMAIN}_error.log;
    
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
        add_header Cache-Control "public";
    }
    
    # Favicon
    location /favicon.ico {
        alias /opt/sistema_imobiliario/staticfiles/favicon.ico;
        expires 30d;
    }
    
    # Aplicação Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Evolution API
    location /evolution/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Webhook de deploy
    location /webhook/ {
        proxy_pass http://127.0.0.1:5000/webhook/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Bloquear acesso a arquivos sensíveis
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|log|conf)$ {
        deny all;
    }
}
EOF

# Testar configuração do Nginx
log "🧪 Testando configuração do Nginx..."
if nginx -t; then
    log "✅ Configuração do Nginx válida!"
else
    error "❌ Erro na configuração do Nginx!"
    exit 1
fi

# Recarregar Nginx
log "🔄 Recarregando Nginx..."
systemctl reload nginx

# Instalar Certbot se não estiver instalado
if ! command -v certbot &> /dev/null; then
    log "📦 Instalando Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Configurar SSL com Let's Encrypt
log "🔒 Configurando SSL com Let's Encrypt..."
echo ""
info "📧 Será usado o email: $EMAIL"
info "🌐 Será configurado SSL para: $DOMAIN e www.$DOMAIN"
echo ""

# Obter certificado SSL
if certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect; then
    log "✅ SSL configurado com sucesso!"
else
    warning "⚠️  Erro ao configurar SSL. Tentando sem www..."
    if certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect; then
        log "✅ SSL configurado para $DOMAIN (sem www)"
    else
        error "❌ Falha ao configurar SSL!"
        exit 1
    fi
fi

# Atualizar arquivo .env com o domínio
log "📝 Atualizando configurações do sistema..."

ENV_FILE="/opt/sistema_imobiliario/.env"
if [[ -f "$ENV_FILE" ]]; then
    # Backup do .env
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Atualizar ALLOWED_HOSTS
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,$SERVER_IP/" "$ENV_FILE"
    
    # Adicionar configurações de SSL se não existirem
    if ! grep -q "SECURE_SSL_REDIRECT" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# Configurações de SSL" >> "$ENV_FILE"
        echo "SECURE_SSL_REDIRECT=True" >> "$ENV_FILE"
        echo "SECURE_BROWSER_XSS_FILTER=True" >> "$ENV_FILE"
        echo "SECURE_CONTENT_TYPE_NOSNIFF=True" >> "$ENV_FILE"
        echo "SESSION_COOKIE_SECURE=True" >> "$ENV_FILE"
        echo "CSRF_COOKIE_SECURE=True" >> "$ENV_FILE"
    fi
    
    log "✅ Arquivo .env atualizado!"
else
    warning "⚠️  Arquivo .env não encontrado em $ENV_FILE"
fi

# Reiniciar serviços
log "🔄 Reiniciando serviços..."
systemctl restart gunicorn
systemctl restart nginx

# Configurar renovação automática do SSL
log "⚙️  Configurando renovação automática do SSL..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Testar o site
log "🧪 Testando o site..."
sleep 5

if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200\|301\|302"; then
    log "✅ Site está respondendo!"
else
    warning "⚠️  Site pode não estar respondendo corretamente"
fi

# Criar arquivo de informações do domínio
cat > /opt/sistema_imobiliario/dominio_info.txt << EOF
# INFORMAÇÕES DO DOMÍNIO CONFIGURADO
# Gerado em: $(date)

DOMÍNIO: $DOMAIN
EMAIL_SSL: $EMAIL
IP_SERVIDOR: $SERVER_IP
SSL_CONFIGURADO: Sim
NGINX_CONFIG: /etc/nginx/sites-available/sistema_imo

# URLs de acesso:
SITE_PRINCIPAL: https://$DOMAIN
EVOLUTION_API: https://$DOMAIN/evolution/
WEBHOOK_DEPLOY: https://$DOMAIN/webhook/

# Comandos úteis:
# Renovar SSL: sudo certbot renew
# Testar Nginx: sudo nginx -t
# Recarregar Nginx: sudo systemctl reload nginx
# Ver logs SSL: sudo tail -f /var/log/letsencrypt/letsencrypt.log
EOF

# Resumo final
echo ""
echo -e "${GREEN}=========================================="
echo "🎉 DOMÍNIO CONFIGURADO COM SUCESSO!"
echo "==========================================${NC}"
echo ""
info "🌐 Seu site está disponível em:"
echo "   📱 https://$DOMAIN"
echo "   📱 https://www.$DOMAIN"
echo ""
info "🔗 URLs importantes:"
echo "   🏠 Site principal: https://$DOMAIN"
echo "   📞 Evolution API: https://$DOMAIN/evolution/"
echo "   🚀 Webhook deploy: https://$DOMAIN/webhook/"
echo ""
info "🔒 SSL/HTTPS:"
echo "   ✅ Certificado instalado"
echo "   ✅ Renovação automática configurada"
echo "   ✅ Redirecionamento HTTP → HTTPS ativo"
echo ""
info "📋 Próximos passos:"
echo "   1. Teste o site: https://$DOMAIN"
echo "   2. Configure o webhook no GitHub/GitLab"
echo "   3. Faça um deploy de teste via Trae AI"
echo ""
warning "💡 IMPORTANTE:"
echo "   • Guarde estas informações em local seguro"
echo "   • O SSL será renovado automaticamente"
echo "   • Logs em: /var/log/nginx/${DOMAIN}_*.log"
echo ""

log "✅ Configuração concluída! Seu sistema está online em https://$DOMAIN"