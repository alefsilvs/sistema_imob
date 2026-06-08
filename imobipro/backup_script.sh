#!/bin/bash

# Script de Backup Automático - Sistema Imobiliário
# Arquivo: /home/imobiliario/sistema-imobiliario/scripts/backup.sh

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

# Configurações
APP_DIR="/home/imobiliario/sistema-imobiliario"
BACKUP_DIR="/var/backups/sistema-imobiliario"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${DATE}"
RETENTION_DAYS=30
MAX_BACKUP_SIZE="10G"

# Configurações do banco de dados
DB_NAME="sistema_imobiliario"
DB_USER="imobiliario_user"
DB_HOST="localhost"
DB_PORT="5432"

# Configurações de notificação
NOTIFY_EMAIL="admin@seudominio.com.br"
SMTP_SERVER="localhost"

# Carregar variáveis de ambiente
if [ -f "$APP_DIR/.env" ]; then
    source "$APP_DIR/.env"
else
    warn "Arquivo .env não encontrado em $APP_DIR"
fi

# Verificar se está rodando como usuário correto
if [ "$(whoami)" != "imobiliario" ] && [ "$(whoami)" != "root" ]; then
    error "Este script deve ser executado como usuário 'imobiliario' ou 'root'"
fi

# Função para verificar espaço em disco
check_disk_space() {
    log "Verificando espaço em disco..."
    
    AVAILABLE_SPACE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=5242880  # 5GB em KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        error "Espaço insuficiente em disco. Disponível: ${AVAILABLE_SPACE}KB, Necessário: ${REQUIRED_SPACE}KB"
    fi
    
    log "✓ Espaço em disco suficiente: $(($AVAILABLE_SPACE / 1024 / 1024))GB disponível"
}

# Função para criar diretório de backup
create_backup_dir() {
    log "Criando diretório de backup..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    chmod 750 "$BACKUP_DIR/$BACKUP_NAME"
    
    log "✓ Diretório criado: $BACKUP_DIR/$BACKUP_NAME"
}

# Função para backup do banco de dados
backup_database() {
    log "Iniciando backup do banco de dados..."
    
    # Verificar se PostgreSQL está rodando
    if ! systemctl is-active --quiet postgresql; then
        error "PostgreSQL não está rodando"
    fi
    
    # Fazer backup do banco
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="$BACKUP_DIR/$BACKUP_NAME/database.dump"
    
    if [ $? -eq 0 ]; then
        log "✓ Backup do banco de dados concluído"
        
        # Verificar integridade do backup
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            --list \
            "$BACKUP_DIR/$BACKUP_NAME/database.dump" > /dev/null
        
        if [ $? -eq 0 ]; then
            log "✓ Integridade do backup verificada"
        else
            error "Backup do banco corrompido"
        fi
    else
        error "Falha no backup do banco de dados"
    fi
    
    # Criar backup SQL também (para facilitar restauração)
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=plain \
        --file="$BACKUP_DIR/$BACKUP_NAME/database.sql"
    
    # Comprimir SQL
    gzip "$BACKUP_DIR/$BACKUP_NAME/database.sql"
    
    log "✓ Backup SQL comprimido criado"
}

# Função para backup dos arquivos de mídia
backup_media() {
    log "Iniciando backup dos arquivos de mídia..."
    
    if [ -d "$APP_DIR/media" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/media.tar.gz" \
            -C "$APP_DIR" \
            media/ \
            --exclude='*.tmp' \
            --exclude='*.log' \
            --exclude='cache/*'
        
        if [ $? -eq 0 ]; then
            log "✓ Backup dos arquivos de mídia concluído"
        else
            error "Falha no backup dos arquivos de mídia"
        fi
    else
        warn "Diretório de mídia não encontrado: $APP_DIR/media"
    fi
}

# Função para backup dos arquivos estáticos
backup_static() {
    log "Iniciando backup dos arquivos estáticos..."
    
    if [ -d "$APP_DIR/staticfiles" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/staticfiles.tar.gz" \
            -C "$APP_DIR" \
            staticfiles/
        
        if [ $? -eq 0 ]; then
            log "✓ Backup dos arquivos estáticos concluído"
        else
            warn "Falha no backup dos arquivos estáticos (não crítico)"
        fi
    else
        warn "Diretório de arquivos estáticos não encontrado: $APP_DIR/staticfiles"
    fi
}

# Função para backup do código fonte
backup_source() {
    log "Iniciando backup do código fonte..."
    
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/source.tar.gz" \
        -C "$APP_DIR" \
        --exclude='venv/*' \
        --exclude='__pycache__/*' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.git/*' \
        --exclude='node_modules/*' \
        --exclude='staticfiles/*' \
        --exclude='media/*' \
        --exclude='*.log' \
        --exclude='*.pid' \
        .
    
    if [ $? -eq 0 ]; then
        log "✓ Backup do código fonte concluído"
    else
        error "Falha no backup do código fonte"
    fi
}

# Função para backup das configurações
backup_configs() {
    log "Iniciando backup das configurações..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/configs"
    
    # Backup do .env (sem senhas)
    if [ -f "$APP_DIR/.env" ]; then
        cp "$APP_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/configs/env.backup"
        # Mascarar senhas no backup
        sed -i 's/\(PASSWORD\|SECRET\|KEY\|TOKEN\)=.*/\1=***MASKED***/g' "$BACKUP_DIR/$BACKUP_NAME/configs/env.backup"
    fi
    
    # Backup das configurações do Nginx
    if [ -f "/etc/nginx/sites-available/imobiliario" ]; then
        cp "/etc/nginx/sites-available/imobiliario" "$BACKUP_DIR/$BACKUP_NAME/configs/nginx.conf"
    fi
    
    # Backup das configurações do Gunicorn
    if [ -f "$APP_DIR/gunicorn_config.py" ]; then
        cp "$APP_DIR/gunicorn_config.py" "$BACKUP_DIR/$BACKUP_NAME/configs/"
    fi
    
    # Backup dos serviços systemd
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/configs/systemd"
    cp /etc/systemd/system/*imobiliario* "$BACKUP_DIR/$BACKUP_NAME/configs/systemd/" 2>/dev/null || true
    
    log "✓ Backup das configurações concluído"
}

# Função para backup dos logs
backup_logs() {
    log "Iniciando backup dos logs..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/logs"
    
    # Logs do sistema
    if [ -d "/var/log/sistema-imobiliario" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/logs/system_logs.tar.gz" \
            -C "/var/log" \
            sistema-imobiliario/
    fi
    
    # Logs do Nginx
    if [ -f "/var/log/nginx/imobiliario_access.log" ]; then
        cp "/var/log/nginx/imobiliario_access.log" "$BACKUP_DIR/$BACKUP_NAME/logs/"
        cp "/var/log/nginx/imobiliario_error.log" "$BACKUP_DIR/$BACKUP_NAME/logs/"
    fi
    
    # Logs do Gunicorn
    if [ -d "/var/log/gunicorn" ]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/logs/gunicorn_logs.tar.gz" \
            -C "/var/log" \
            gunicorn/
    fi
    
    log "✓ Backup dos logs concluído"
}

# Função para criar manifesto do backup
create_manifest() {
    log "Criando manifesto do backup..."
    
    cat > "$BACKUP_DIR/$BACKUP_NAME/MANIFEST.txt" << EOF
# Manifesto do Backup - Sistema Imobiliário
# Data: $(date)
# Servidor: $(hostname)
# Usuário: $(whoami)

## Informações do Sistema
Sistema Operacional: $(lsb_release -d | cut -f2)
Kernel: $(uname -r)
Arquitetura: $(uname -m)
Uptime: $(uptime)

## Informações do Backup
Data/Hora: $(date)
Diretório: $BACKUP_DIR/$BACKUP_NAME
Tamanho Total: $(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)

## Arquivos Incluídos
$(ls -la "$BACKUP_DIR/$BACKUP_NAME")

## Versões dos Serviços
PostgreSQL: $(psql --version | head -n1)
Nginx: $(nginx -v 2>&1)
Python: $(python3 --version)
Django: $(cd "$APP_DIR" && python manage.py --version 2>/dev/null || echo "N/A")

## Status dos Serviços
$(systemctl status postgresql --no-pager -l)
$(systemctl status nginx --no-pager -l)
$(systemctl status gunicorn-imobiliario --no-pager -l)

## Configurações do Banco
Banco: $DB_NAME
Host: $DB_HOST
Porta: $DB_PORT
Usuário: $DB_USER

## Checksums
$(cd "$BACKUP_DIR/$BACKUP_NAME" && find . -type f -exec sha256sum {} \;)
EOF
    
    log "✓ Manifesto criado"
}

# Função para comprimir backup final
compress_backup() {
    log "Comprimindo backup final..."
    
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME/"
    
    if [ $? -eq 0 ]; then
        # Remover diretório não comprimido
        rm -rf "$BACKUP_NAME/"
        
        # Verificar integridade do arquivo comprimido
        tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null
        
        if [ $? -eq 0 ]; then
            log "✓ Backup comprimido com sucesso: ${BACKUP_NAME}.tar.gz"
            log "✓ Tamanho: $(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)"
        else
            error "Arquivo de backup corrompido"
        fi
    else
        error "Falha na compressão do backup"
    fi
}

# Função para limpar backups antigos
cleanup_old_backups() {
    log "Limpando backups antigos (mais de $RETENTION_DAYS dias)..."
    
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    
    REMOVED_COUNT=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS | wc -l)
    
    if [ $REMOVED_COUNT -gt 0 ]; then
        log "✓ $REMOVED_COUNT backups antigos removidos"
    else
        log "✓ Nenhum backup antigo para remover"
    fi
    
    # Listar backups restantes
    log "Backups disponíveis:"
    ls -lah "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | while read line; do
        log "  $line"
    done
}

# Função para enviar notificação
send_notification() {
    local status=$1
    local message=$2
    
    if [ -n "$NOTIFY_EMAIL" ]; then
        local subject="[Sistema Imobiliário] Backup $status - $(date)"
        
        echo "$message" | mail -s "$subject" "$NOTIFY_EMAIL" 2>/dev/null || true
    fi
    
    # Log no sistema
    logger -t "backup-imobiliario" "$status: $message"
}

# Função para verificar pré-requisitos
check_prerequisites() {
    log "Verificando pré-requisitos..."
    
    # Verificar se PostgreSQL está rodando
    if ! systemctl is-active --quiet postgresql; then
        error "PostgreSQL não está rodando"
    fi
    
    # Verificar se usuário do banco existe
    if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        error "Banco de dados '$DB_NAME' não encontrado"
    fi
    
    # Verificar comandos necessários
    for cmd in pg_dump tar gzip find; do
        if ! command -v $cmd >/dev/null 2>&1; then
            error "Comando '$cmd' não encontrado"
        fi
    done
    
    log "✓ Todos os pré-requisitos atendidos"
}

# Função para testar restauração (opcional)
test_restore() {
    if [ "$1" = "--test-restore" ]; then
        log "Testando restauração do backup..."
        
        # Criar banco temporário para teste
        TEST_DB="${DB_NAME}_test_restore"
        
        sudo -u postgres createdb "$TEST_DB" 2>/dev/null || true
        
        # Tentar restaurar
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$TEST_DB" \
            --verbose \
            --no-password \
            "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "✓ Teste de restauração bem-sucedido"
        else
            warn "Teste de restauração falhou (backup pode estar corrompido)"
        fi
        
        # Limpar banco de teste
        sudo -u postgres dropdb "$TEST_DB" 2>/dev/null || true
    fi
}

# Função principal
main() {
    log "=== Iniciando Backup do Sistema Imobiliário ==="
    log "Data/Hora: $(date)"
    log "Servidor: $(hostname)"
    log "Backup: $BACKUP_NAME"
    
    START_TIME=$(date +%s)
    
    # Verificar pré-requisitos
    check_prerequisites
    
    # Verificar espaço em disco
    check_disk_space
    
    # Criar diretório de backup
    create_backup_dir
    
    # Executar backups
    backup_database
    backup_media
    backup_static
    backup_source
    backup_configs
    backup_logs
    
    # Criar manifesto
    create_manifest
    
    # Comprimir backup
    compress_backup
    
    # Limpar backups antigos
    cleanup_old_backups
    
    # Testar restauração se solicitado
    test_restore "$1"
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    log "=== Backup Concluído com Sucesso ==="
    log "Tempo total: ${DURATION}s"
    log "Arquivo: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    log "Tamanho: $(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)"
    
    # Enviar notificação de sucesso
    send_notification "SUCESSO" "Backup concluído com sucesso em ${DURATION}s. Arquivo: ${BACKUP_NAME}.tar.gz"
}

# Função para tratamento de erros
trap 'error "Backup interrompido por erro"' ERR
trap 'send_notification "FALHA" "Backup falhou ou foi interrompido"' EXIT

# Executar função principal
main "$@"

# Remover trap de erro se chegou até aqui
trap - EXIT

log "Backup finalizado com sucesso!"