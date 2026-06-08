#!/bin/bash

# =============================================================================
# Script de Monitoramento - Sistema Imobiliário KingHost
# =============================================================================

# Configurações
PROJECT_NAME="sistema_imobiliario"
PROJECT_DIR="/home/sistema_imo/apps/sistema_imo"
LOG_FILE="/home/sistema_imo/logs/monitor.log"
ALERT_EMAIL=""  # Configurar no .env
TELEGRAM_BOT_TOKEN=""  # Configurar no .env
TELEGRAM_CHAT_ID=""    # Configurar no .env

# Thresholds de alerta
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=5000  # ms

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

# Carregar configurações do .env
load_config() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        ALERT_EMAIL="$MONITOR_EMAIL"
        TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
        TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
    fi
}

# Verificar status dos serviços
check_services() {
    log "Verificando status dos serviços..."
    
    local services=("sistema_imo" "nginx" "postgresql" "redis")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            success "✓ $service está rodando"
        else
            error "✗ $service está parado"
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        send_alert "Serviços parados: ${failed_services[*]}"
        return 1
    fi
    
    return 0
}

# Verificar uso de CPU
check_cpu() {
    log "Verificando uso de CPU..."
    
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    cpu_usage=${cpu_usage%.*}  # Remover decimais
    
    log "Uso de CPU: ${cpu_usage}%"
    
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        warning "⚠️  Alto uso de CPU: ${cpu_usage}%"
        send_alert "Alto uso de CPU: ${cpu_usage}%"
        return 1
    fi
    
    return 0
}

# Verificar uso de memória
check_memory() {
    log "Verificando uso de memória..."
    
    local memory_info=$(free | grep Mem)
    local total=$(echo $memory_info | awk '{print $2}')
    local used=$(echo $memory_info | awk '{print $3}')
    local memory_usage=$((used * 100 / total))
    
    log "Uso de memória: ${memory_usage}%"
    
    if [ "$memory_usage" -gt "$MEMORY_THRESHOLD" ]; then
        warning "⚠️  Alto uso de memória: ${memory_usage}%"
        send_alert "Alto uso de memória: ${memory_usage}%"
        return 1
    fi
    
    return 0
}

# Verificar uso de disco
check_disk() {
    log "Verificando uso de disco..."
    
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    log "Uso de disco: ${disk_usage}%"
    
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        warning "⚠️  Alto uso de disco: ${disk_usage}%"
        send_alert "Alto uso de disco: ${disk_usage}%"
        return 1
    fi
    
    return 0
}

# Verificar conectividade do banco de dados
check_database() {
    log "Verificando conectividade do banco de dados..."
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        # Testar conexão com PostgreSQL
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            success "✓ Banco de dados conectado"
            return 0
        else
            error "✗ Falha na conexão com o banco de dados"
            send_alert "Falha na conexão com o banco de dados"
            return 1
        fi
    else
        error "Arquivo .env não encontrado"
        return 1
    fi
}

# Verificar conectividade do Redis
check_redis() {
    log "Verificando conectividade do Redis..."
    
    redis-cli ping > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        success "✓ Redis conectado"
        return 0
    else
        error "✗ Falha na conexão com o Redis"
        send_alert "Falha na conexão com o Redis"
        return 1
    fi
}

# Verificar tempo de resposta da aplicação
check_response_time() {
    log "Verificando tempo de resposta da aplicação..."
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        local url="https://$DOMAIN_NAME"
        local response_time=$(curl -o /dev/null -s -w '%{time_total}' "$url" | awk '{print $1*1000}')
        response_time=${response_time%.*}  # Remover decimais
        
        log "Tempo de resposta: ${response_time}ms"
        
        if [ "$response_time" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            warning "⚠️  Alto tempo de resposta: ${response_time}ms"
            send_alert "Alto tempo de resposta: ${response_time}ms"
            return 1
        fi
        
        return 0
    else
        error "Arquivo .env não encontrado"
        return 1
    fi
}

# Verificar logs de erro
check_error_logs() {
    log "Verificando logs de erro..."
    
    local django_log="/home/sistema_imo/logs/django.log"
    local nginx_error_log="/var/log/nginx/error.log"
    
    # Verificar erros do Django nas últimas 5 minutos
    if [ -f "$django_log" ]; then
        local recent_errors=$(grep -c "ERROR\|CRITICAL" "$django_log" | tail -100)
        if [ "$recent_errors" -gt 0 ]; then
            warning "⚠️  Encontrados $recent_errors erros recentes no Django"
            send_alert "Encontrados $recent_errors erros recentes no Django"
        fi
    fi
    
    # Verificar erros do Nginx nas últimas 5 minutos
    if [ -f "$nginx_error_log" ]; then
        local recent_nginx_errors=$(grep "$(date '+%Y/%m/%d %H:%M' -d '5 minutes ago')" "$nginx_error_log" | wc -l)
        if [ "$recent_nginx_errors" -gt 0 ]; then
            warning "⚠️  Encontrados $recent_nginx_errors erros recentes no Nginx"
            send_alert "Encontrados $recent_nginx_errors erros recentes no Nginx"
        fi
    fi
}

# Verificar certificado SSL
check_ssl_certificate() {
    log "Verificando certificado SSL..."
    
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
        
        local domain="$DOMAIN_NAME"
        local expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        log "Certificado SSL expira em $days_until_expiry dias"
        
        if [ "$days_until_expiry" -lt 30 ]; then
            warning "⚠️  Certificado SSL expira em $days_until_expiry dias"
            send_alert "Certificado SSL expira em $days_until_expiry dias"
            return 1
        fi
        
        return 0
    else
        error "Arquivo .env não encontrado"
        return 1
    fi
}

# Verificar espaço em logs
check_log_space() {
    log "Verificando espaço usado pelos logs..."
    
    local log_dir="/home/sistema_imo/logs"
    local log_size=$(du -sh "$log_dir" 2>/dev/null | cut -f1)
    local log_size_mb=$(du -sm "$log_dir" 2>/dev/null | cut -f1)
    
    log "Espaço usado pelos logs: $log_size"
    
    # Se logs ocupam mais de 1GB, alertar
    if [ "$log_size_mb" -gt 1024 ]; then
        warning "⚠️  Logs ocupando muito espaço: $log_size"
        send_alert "Logs ocupando muito espaço: $log_size"
        return 1
    fi
    
    return 0
}

# Enviar alerta por email
send_email_alert() {
    local message="$1"
    
    if [ ! -z "$ALERT_EMAIL" ]; then
        local subject="[ALERTA] Sistema Imobiliário - $(date '+%d/%m/%Y %H:%M')"
        local body="ALERTA do Sistema Imobiliário:

$message

Servidor: $(hostname)
Data/Hora: $(date '+%d/%m/%Y às %H:%M:%S')

Verifique o sistema o mais rápido possível.

Logs disponíveis em: $LOG_FILE"
        
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "Alerta enviado por email para $ALERT_EMAIL"
        else
            error "Falha ao enviar alerta por email"
        fi
    fi
}

# Enviar alerta por Telegram
send_telegram_alert() {
    local message="$1"
    
    if [ ! -z "$TELEGRAM_BOT_TOKEN" ] && [ ! -z "$TELEGRAM_CHAT_ID" ]; then
        local telegram_message="🚨 *ALERTA Sistema Imobiliário*

$message

🖥️ Servidor: $(hostname)
📅 Data/Hora: $(date '+%d/%m/%Y às %H:%M:%S')

Verifique o sistema o mais rápido possível."
        
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="$telegram_message" \
            -d parse_mode="Markdown" > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            log "Alerta enviado por Telegram"
        else
            error "Falha ao enviar alerta por Telegram"
        fi
    fi
}

# Função principal para envio de alertas
send_alert() {
    local message="$1"
    
    error "$message"
    send_email_alert "$message"
    send_telegram_alert "$message"
}

# Gerar relatório de status
generate_status_report() {
    log "Gerando relatório de status..."
    
    local report_file="/home/sistema_imo/logs/status_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
========================================
RELATÓRIO DE STATUS - SISTEMA IMOBILIÁRIO
========================================

Data/Hora: $(date '+%d/%m/%Y às %H:%M:%S')
Servidor: $(hostname)

SERVIÇOS:
$(systemctl is-active sistema_imo nginx postgresql redis | paste <(echo -e "sistema_imo\nnginx\npostgresql\nredis") -)

RECURSOS DO SISTEMA:
CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
Memória: $(free -h | grep Mem | awk '{print $3"/"$2" ("$3/$2*100"%)"}'  2>/dev/null || echo "N/A")
Disco: $(df -h / | tail -1 | awk '{print $3"/"$2" ("$5")"}')

CONECTIVIDADE:
Banco de dados: $(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1 && echo "OK" || echo "FALHA")
Redis: $(redis-cli ping 2>/dev/null || echo "FALHA")

APLICAÇÃO:
URL: https://$DOMAIN_NAME
Tempo de resposta: $(curl -o /dev/null -s -w '%{time_total}s' "https://$DOMAIN_NAME" 2>/dev/null || echo "N/A")

LOGS RECENTES:
$(tail -5 "$LOG_FILE" 2>/dev/null || echo "Nenhum log disponível")

========================================
EOF
    
    success "Relatório de status salvo em: $report_file"
}

# Função principal
main() {
    log "=========================================="
    log "Iniciando monitoramento do Sistema Imobiliário"
    log "=========================================="
    
    # Carregar configurações
    load_config
    
    local checks_failed=0
    
    # Executar verificações
    check_services || ((checks_failed++))
    check_cpu || ((checks_failed++))
    check_memory || ((checks_failed++))
    check_disk || ((checks_failed++))
    check_database || ((checks_failed++))
    check_redis || ((checks_failed++))
    check_response_time || ((checks_failed++))
    check_error_logs || ((checks_failed++))
    check_ssl_certificate || ((checks_failed++))
    check_log_space || ((checks_failed++))
    
    # Resumo final
    log "=========================================="
    if [ $checks_failed -eq 0 ]; then
        success "✅ Todas as verificações passaram!"
        log "Sistema funcionando normalmente"
    else
        warning "⚠️  $checks_failed verificação(ões) falharam"
        log "Verifique os alertas acima"
    fi
    log "=========================================="
    
    # Gerar relatório se solicitado
    if [ "$1" = "report" ]; then
        generate_status_report
    fi
}

# Verificar argumentos
case "$1" in
    "services")
        log "Verificando apenas serviços..."
        load_config
        check_services
        ;;
    "resources")
        log "Verificando apenas recursos do sistema..."
        check_cpu
        check_memory
        check_disk
        ;;
    "connectivity")
        log "Verificando apenas conectividade..."
        load_config
        check_database
        check_redis
        ;;
    "ssl")
        log "Verificando apenas certificado SSL..."
        load_config
        check_ssl_certificate
        ;;
    "report")
        load_config
        main "report"
        ;;
    *)
        main
        ;;
esac

exit 0