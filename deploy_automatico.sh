#!/bin/bash

# ========================================
# SCRIPT DE DEPLOY AUTOMÁTICO - VPS BRASIL
# Sistema Imobiliário - ImobilPro
# Otimizado para provedores brasileiros
# ========================================

set -e

echo "🚀 Iniciando deploy automático..."

# Configurações para VPS Nacional
PROJECT_DIR="/opt/sistema_imobiliario"
BACKUP_DIR="/opt/backups/sistema_imobiliario"
VENV_PATH="$PROJECT_DIR/.venv"
LOG_FILE="/var/log/deploy_sistema.log"
BRANCH="main"
REPO_URL="https://github.com/SEU_USUARIO/sistema-imobiliario.git"

# Configurações específicas para Brasil
TIMEZONE="America/Sao_Paulo"
LOCALE="pt_BR.UTF-8"

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Função de backup
backup_current() {
    log "📦 Criando backup da versão atual..."
    mkdir -p $BACKUP_DIR
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    cp -r $PROJECT_DIR $BACKUP_DIR/$BACKUP_NAME
    log "✅ Backup criado: $BACKUP_DIR/$BACKUP_NAME"
}

# Função de rollback
rollback() {
    log "⚠️ Erro detectado! Iniciando rollback..."
    LATEST_BACKUP=$(ls -t $BACKUP_DIR | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        rm -rf $PROJECT_DIR
        cp -r $BACKUP_DIR/$LATEST_BACKUP $PROJECT_DIR
        log "🔄 Rollback concluído para: $LATEST_BACKUP"
        restart_services
    else
        log "❌ Nenhum backup encontrado para rollback!"
    fi
}

# Função para reiniciar serviços
restart_services() {
    log "🔄 Reiniciando serviços..."
    
    # Reiniciar Django (Gunicorn)
    sudo systemctl restart gunicorn
    
    # Reiniciar Nginx
    sudo systemctl restart nginx
    
    # Reiniciar Evolution API
    sudo systemctl restart evolution-api
    
    log "✅ Serviços reiniciados"
}

# Função principal de deploy
deploy() {
    log "🚀 Iniciando processo de deploy..."
    
    # Navegar para o diretório do projeto
    cd $PROJECT_DIR || { log "❌ Erro: Diretório do projeto não encontrado"; exit 1; }
    
    # Fazer backup da versão atual
    backup_current
    
    # Atualizar código do repositório
    log "📥 Baixando atualizações do repositório..."
    git fetch origin
    git reset --hard origin/main
    
    # Ativar ambiente virtual
    log "🐍 Ativando ambiente virtual..."
    source $VENV_PATH/bin/activate
    
    # Instalar/atualizar dependências
    log "📦 Instalando dependências..."
    pip install -r requirements.txt
    
    # Executar migrações do banco
    log "🗄️ Executando migrações do banco..."
    python manage.py migrate
    
    # Coletar arquivos estáticos
    log "📁 Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput
    
    # Verificar se o sistema está funcionando
    log "🔍 Verificando integridade do sistema..."
    python manage.py check
    
    if [ $? -eq 0 ]; then
        log "✅ Verificação passou! Reiniciando serviços..."
        restart_services
        
        # Testar se o site está respondendo
        sleep 5
        if curl -f -s http://localhost > /dev/null; then
            log "🎉 Deploy concluído com sucesso!"
            
            # Limpar backups antigos (manter apenas os 5 mais recentes)
            cd $BACKUP_DIR
            ls -t | tail -n +6 | xargs rm -rf
            
        else
            log "❌ Site não está respondendo após deploy!"
            rollback
            exit 1
        fi
    else
        log "❌ Verificação do sistema falhou!"
        rollback
        exit 1
    fi
}

# Executar deploy
deploy

log "🏁 Processo de deploy finalizado!"