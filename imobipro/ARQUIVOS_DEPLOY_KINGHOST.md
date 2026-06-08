# 📁 Arquivos de Deploy - KingHost

## Resumo dos Arquivos Criados

Este documento lista todos os arquivos criados especificamente para facilitar o deploy do Sistema Imobiliário na KingHost.

---

## 📋 Documentação Principal

### 1. `DEPLOY_KINGHOST.md`
**Descrição:** Guia completo e detalhado para hospedagem na KingHost
- Pré-requisitos e preparação
- Configuração passo a passo no servidor
- Configurações específicas da KingHost
- Otimizações de performance
- Procedimentos de manutenção

### 2. `CHECKLIST_KINGHOST.md`
**Descrição:** Checklist interativo para deploy
- Lista de verificação pré-deploy
- Configuração do servidor passo a passo
- Testes finais e validação
- Troubleshooting comum
- Comandos úteis para manutenção

### 3. `ARQUIVOS_DEPLOY_KINGHOST.md` (este arquivo)
**Descrição:** Documentação de todos os arquivos criados para deploy

---

## ⚙️ Configurações de Produção

### 4. `settings_production.py`
**Descrição:** Configurações Django específicas para produção na KingHost
- Configurações de segurança HTTPS
- Banco de dados PostgreSQL
- Cache Redis
- Configurações de email SMTP
- Integração com Sentry
- Configurações de arquivos estáticos

### 5. `.env.production.example`
**Descrição:** Template de variáveis de ambiente para produção
- Configurações básicas (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Banco de dados PostgreSQL
- Redis para cache
- Configurações de email
- Monitoramento (Sentry)
- Configurações específicas da KingHost

### 6. `requirements.txt` (atualizado)
**Descrição:** Dependências Python para produção
- Dependências básicas do Django
- PostgreSQL (psycopg2-binary)
- Redis e cache
- Monitoramento e logging
- Servidor web (Gunicorn)

---

## 🖥️ Configurações do Servidor

### 7. `gunicorn.conf.py`
**Descrição:** Configuração do servidor Gunicorn
- Configurações de workers baseadas na CPU
- Timeouts e logs
- Monitoramento de workers
- Configurações de segurança

### 8. `nginx_kinghost.conf`
**Descrição:** Configuração do Nginx para KingHost
- Rate limiting e cache
- Configurações SSL/HTTPS
- Headers de segurança
- Proxy para Gunicorn
- Configurações para arquivos estáticos

### 9. `sistema_imo.service`
**Descrição:** Arquivo de serviço systemd
- Configuração do serviço Gunicorn
- Dependências e reinicialização automática
- Configurações de segurança
- Limites de recursos

---

## 🚀 Scripts de Automação

### 10. `deploy_kinghost.sh`
**Descrição:** Script principal de deploy automatizado
- Criação de diretórios
- Configuração do ambiente virtual
- Setup do banco PostgreSQL
- Configuração do Gunicorn e Nginx
- Setup SSL com Let's Encrypt
- Sistema de backup

### 11. `backup_kinghost.sh`
**Descrição:** Script de backup automático
- Backup do banco de dados PostgreSQL
- Backup dos arquivos de mídia
- Backup do código fonte
- Backup das configurações
- Limpeza de backups antigos
- Notificações por email/Telegram

### 12. `monitor_kinghost.sh`
**Descrição:** Script de monitoramento do sistema
- Verificação de serviços (Django, Nginx, PostgreSQL, Redis)
- Monitoramento de recursos (CPU, memória, disco)
- Verificação de conectividade
- Monitoramento de logs de erro
- Verificação de certificado SSL
- Alertas por email/Telegram

---

## 📊 Como Usar os Arquivos

### Ordem de Execução Recomendada:

1. **Preparação Local:**
   ```bash
   # Copiar template de ambiente
   cp .env.production.example .env
   # Editar variáveis de ambiente
   nano .env
   ```

2. **Upload para Servidor:**
   ```bash
   # Fazer upload de todos os arquivos para o servidor KingHost
   scp -r * usuario@servidor:/home/sistema_imo/apps/sistema_imo/
   ```

3. **Executar Deploy:**
   ```bash
   # Dar permissão e executar script de deploy
   chmod +x deploy_kinghost.sh
   ./deploy_kinghost.sh
   ```

4. **Configurar Backup Automático:**
   ```bash
   # Configurar backup no crontab
   chmod +x backup_kinghost.sh
   crontab -e
   # Adicionar: 0 2 * * * /home/sistema_imo/apps/sistema_imo/backup_kinghost.sh
   ```

5. **Configurar Monitoramento:**
   ```bash
   # Configurar monitoramento no crontab
   chmod +x monitor_kinghost.sh
   crontab -e
   # Adicionar: */5 * * * * /home/sistema_imo/apps/sistema_imo/monitor_kinghost.sh
   ```

---

## 🔧 Configurações Específicas da KingHost

### Características Consideradas:
- **Painel de Controle:** cPanel/WHM
- **Servidor Web:** Nginx + Apache
- **Banco de Dados:** PostgreSQL disponível
- **SSL:** Let's Encrypt gratuito
- **Email:** SMTP próprio da KingHost
- **Backup:** Backup automático disponível
- **Monitoramento:** Ferramentas próprias + scripts customizados

### Otimizações Implementadas:
- **Cache Redis:** Para melhor performance
- **Compressão Gzip:** Redução do tamanho dos arquivos
- **Headers de Segurança:** Proteção contra ataques
- **Rate Limiting:** Proteção contra spam/DDoS
- **Logs Detalhados:** Para debugging e monitoramento

---

## 📞 Suporte e Manutenção

### Logs Importantes:
- **Django:** `/home/sistema_imo/logs/django.log`
- **Gunicorn:** `/home/sistema_imo/logs/gunicorn.log`
- **Nginx:** `/var/log/nginx/sistema_imo_access.log`
- **Backup:** `/home/sistema_imo/logs/backup.log`
- **Monitor:** `/home/sistema_imo/logs/monitor.log`

### Comandos Úteis:
```bash
# Verificar status dos serviços
sudo systemctl status sistema_imo nginx postgresql redis

# Ver logs em tempo real
sudo journalctl -u sistema_imo -f
tail -f /home/sistema_imo/logs/django.log

# Reiniciar serviços
sudo systemctl restart sistema_imo
sudo systemctl reload nginx

# Executar backup manual
./backup_kinghost.sh

# Executar monitoramento manual
./monitor_kinghost.sh
```

---

## ✅ Checklist de Verificação

Antes de considerar o deploy concluído, verifique:

- [ ] Todos os arquivos foram criados e estão no servidor
- [ ] Variáveis de ambiente configuradas no `.env`
- [ ] Script de deploy executado com sucesso
- [ ] Todos os serviços rodando (Django, Nginx, PostgreSQL, Redis)
- [ ] Site acessível via HTTPS
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Logs sendo gerados corretamente
- [ ] Certificado SSL válido
- [ ] Email funcionando
- [ ] Funcionalidades principais testadas

---

## 🎯 Próximos Passos

Após o deploy bem-sucedido:

1. **Monitoramento Contínuo:** Acompanhar logs e métricas
2. **Backup Regular:** Verificar se backups estão sendo criados
3. **Atualizações:** Manter sistema e dependências atualizados
4. **Otimização:** Ajustar configurações baseado no uso real
5. **Documentação:** Manter documentação atualizada
6. **Treinamento:** Treinar equipe para manutenção

---

**📧 Suporte KingHost:**
- Telefone: 0800 033 7777
- Chat: Disponível no painel
- Email: suporte@kinghost.com.br

**🔗 Links Úteis:**
- [Documentação KingHost](https://king.host/wiki/)
- [Suporte Django](https://docs.djangoproject.com/)
- [Gunicorn Docs](https://gunicorn.org/)
- [Nginx Docs](https://nginx.org/en/docs/)

---

*Última atualização: $(date '+%d/%m/%Y')*