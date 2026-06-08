#!/bin/bash

# =============================================================================
# Script de Backup Automático - Sistema Imobiliário KingHost
# =============================================================================

# Configurações
PROJECT_NAME="sistema_imobiliario"
PROJECT_DIR="/home/sistema_imo/apps/sistema_imo"
BACKUP_DIR="/home/sistema_imo/backups"
LOG_FILE="/home/sistema_imo/logs/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING $(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Verificar se o diretório de backup existe
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "Diretório de backup criado: $BACKUP_DIR"
    fi
}

# Backup do banco de dados PostgreSQL
backup_database() {
    log "Iniciando backup do banco de dados..."
    
    # Carregar variáveis de ambiente
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    else
        error "Arquivo .env não encontrado em $PROJECT_DIR"
        return 1
    fi
    
    # Nome do arquivo de backup
    DB_BACKUP_FILE="$BACKUP_DIR/db_${PROJECT_NAME}_${DATE}.sql"
    
    # Executar backup
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-password \
        --verbose \
        --clean \
        --if-exists \
        > "$DB_BACKUP_FILE" 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        # Comprimir backup
        gzip "$DB_BACKUP_FILE"
        success "Backup do banco de dados criado: ${DB_BACKUP_FILE}.gz"
        
        # Verificar tamanho do arquivo
        SIZE=$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)
        log "Tamanho do backup do banco: $SIZE"
    else
        error "Falha no backup do banco de dados"
        return 1
    fi
}

# Backup dos arquivos de mídia
backup_media() {
    log "Iniciando backup dos arquivos de mídia..."
    
    MEDIA_BACKUP_FILE="$BACKUP_DIR/media_${PROJECT_NAME}_${DATE}.tar.gz"
    MEDIA_DIR="/home/sistema_imo/public_html/media"
    
    if [ -d "$MEDIA_DIR" ]; then
        tar -czf "$MEDIA_BACKUP_FILE" -C "$(dirname "$MEDIA_DIR")" "$(basename "$MEDIA_DIR")" 2>> "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            success "Backup dos arquivos de mídia criado: $MEDIA_BACKUP_FILE"
            
            # Verificar tamanho do arquivo
            SIZE=$(du -h "$MEDIA_BACKUP_FILE" | cut -f1)
            log "Tamanho do backup de mídia: $SIZE"
        else
            error "Falha no backup dos arquivos de mídia"
            return 1
        fi
    else
        warning "Diretório de mídia não encontrado: $MEDIA_DIR"
    fi
}

# Backup do código fonte
backup_code() {
    log "Iniciando backup do código fonte..."
    
    CODE_BACKUP_FILE="$BACKUP_DIR/code_${PROJECT_NAME}_${DATE}.tar.gz"
    
    # Excluir arquivos desnecessários
    tar -czf "$CODE_BACKUP_FILE" \
        --exclude="*.pyc" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="node_modules" \
        --exclude="*.log" \
        --exclude=".env" \
        -C "$(dirname "$PROJECT_DIR")" \
        "$(basename "$PROJECT_DIR")" 2>> "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        success "Backup do código fonte criado: $CODE_BACKUP_FILE"
        
        # Verificar tamanho do arquivo
        SIZE=$(du -h "$CODE_BACKUP_FILE" | cut -f1)
        log "Tamanho do backup do código: $SIZE"
    else
        error "Falha no backup do código fonte"
        return 1
    fi
}

# Backup das configurações do sistema
backup_configs() {
    log "Iniciando backup das configurações..."
    
    CONFIG_BACKUP_FILE="$BACKUP_DIR/configs_${PROJECT_NAME}_${DATE}.tar.gz"
    
    # Criar diretório temporário para configurações
    TEMP_CONFIG_DIR="/tmp/sistema_imo_configs_$DATE"
    mkdir -p "$TEMP_CONFIG_DIR"
    
    # Copiar configurações importantes
    cp /etc/nginx/sites-available/sistema_imo "$TEMP_CONFIG_DIR/" 2>/dev/null
    cp /etc/systemd/system/sistema_imo.service "$TEMP_CONFIG_DIR/" 2>/dev/null
    cp "$PROJECT_DIR/gunicorn.conf.py" "$TEMP_CONFIG_DIR/" 2>/dev/null
    
    # Criar arquivo com informações do sistema
    cat > "$TEMP_CONFIG_DIR/system_info.txt" << EOF
Sistema: $(uname -a)
Data do backup: $(date)
Versão Python: $(python3 --version)
Versão PostgreSQL: $(psql --version)
Versão Nginx: $(nginx -v 2>&1)
Versão Redis: $(redis-server --version)
Espaço em disco: $(df -h)
Memória: $(free -h)
EOF
    
    # Criar backup das configurações
    tar -czf "$CONFIG_BACKUP_FILE" -C "/tmp" "sistema_imo_configs_$DATE" 2>> "$LOG_FILE"
    
    # Limpar diretório temporário
    rm -rf "$TEMP_CONFIG_DIR"
    
    if [ $? -eq 0 ]; then
        success "Backup das configurações criado: $CONFIG_BACKUP_FILE"
        
        # Verificar tamanho do arquivo
        SIZE=$(du -h "$CONFIG_BACKUP_FILE" | cut -f1)
        log "Tamanho do backup de configurações: $SIZE"
    else
        error "Falha no backup das configurações"
        return 1
    fi
}

# Limpeza de backups antigos
cleanup_old_backups() {
    log "Iniciando limpeza de backups antigos (mais de $RETENTION_DAYS dias)..."
    
    # Encontrar e remover backups antigos
    DELETED_COUNT=$(find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
    
    if [ $DELETED_COUNT -gt 0 ]; then
        success "Removidos $DELETED_COUNT backups antigos"
    else
        log "Nenhum backup antigo para remover"
    fi
}

# Verificar integridade dos backups
verify_backups() {
    log "Verificando integridade dos backups..."
    
    # Verificar backups do dia atual
    TODAY_BACKUPS=$(find "$BACKUP_DIR" -name "*_${DATE:0:8}_*.gz" -type f)
    
    for backup in $TODAY_BACKUPS; do
        if gzip -t "$backup" 2>/dev/null; then
            success "Backup íntegro: $(basename "$backup")"
        else
            error "Backup corrompido: $(basename "$backup")"
        fi
    done
}

# Enviar notificação por email (opcional)
send_notification() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        if [ ! -z "$BACKUP_EMAIL" ]; then
            SUBJECT="Backup Sistema Imobiliário - $(date '+%d/%m/%Y %H:%M')"
            BODY="Backup do sistema imobiliário executado com sucesso em $(date '+%d/%m/%Y às %H:%M').

Arquivos criados:
$(ls -la "$BACKUP_DIR"/*_${DATE}*.gz 2>/dev/null | awk '{print $9, $5}')

Espaço total usado pelos backups: $(du -sh "$BACKUP_DIR" | cut -f1)

Logs disponíveis em: $LOG_FILE"
            
            echo "$BODY" | mail -s "$SUBJECT" "$BACKUP_EMAIL" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                success "Notificação enviada para $BACKUP_EMAIL"
            else
                warning "Falha ao enviar notificação por email"
            fi
        fi
    fi
}

# Função principal
main() {
    log "=========================================="
    log "Iniciando backup do Sistema Imobiliário"
    log "=========================================="
    
    # Verificar se está rodando como usuário correto
    if [ "$USER" != "sistema_imo" ] && [ "$USER" != "root" ]; then
        warning "Recomendado executar como usuário 'sistema_imo' ou 'root'"
    fi
    
    # Criar diretório de backup
    create_backup_dir
    
    # Executar backups
    backup_database
    backup_media
    backup_code
    backup_configs
    
    # Verificar integridade
    verify_backups
    
    # Limpeza
    cleanup_old_backups
    
    # Notificação
    send_notification
    
    # Resumo final
    log "=========================================="
    log "Backup concluído!"
    log "=========================================="
    
    # Mostrar estatísticas
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*_${DATE}*.gz 2>/dev/null | wc -l)
    
    success "Total de arquivos criados: $BACKUP_COUNT"
    success "Espaço total dos backups: $TOTAL_SIZE"
    success "Logs salvos em: $LOG_FILE"
}

# Verificar argumentos
case "$1" in
    "database")
        log "Executando apenas backup do banco de dados..."
        create_backup_dir
        backup_database
        ;;
    "media")
        log "Executando apenas backup dos arquivos de mídia..."
        create_backup_dir
        backup_media
        ;;
    "code")
        log "Executando apenas backup do código fonte..."
        create_backup_dir
        backup_code
        ;;
    "configs")
        log "Executando apenas backup das configurações..."
        create_backup_dir
        backup_configs
        ;;
    "cleanup")
        log "Executando apenas limpeza de backups antigos..."
        cleanup_old_backups
        ;;
    *)
        main
        ;;
esac

exit 0