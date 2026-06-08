# ✅ Checklist de Deploy - KingHost

## Pré-Deploy (Local)

### 📋 Preparação dos Arquivos
- [ ] Arquivo `requirements.txt` atualizado com dependências de produção
- [ ] Arquivo `settings_production.py` configurado
- [ ] Arquivo `.env.production.example` copiado para `.env` e configurado
- [ ] Script `deploy_kinghost.sh` com permissões de execução
- [ ] Arquivos de configuração do servidor preparados

### 🔐 Configurações de Segurança
- [ ] `SECRET_KEY` gerada e configurada no `.env`
- [ ] `DEBUG=False` no arquivo de produção
- [ ] Senhas seguras definidas para banco e email
- [ ] Domínio correto configurado em `ALLOWED_HOSTS`

### 📦 Código
- [ ] Código commitado no Git
- [ ] Repositório acessível do servidor
- [ ] Migrações testadas localmente
- [ ] Arquivos estáticos coletados e testados

## Configuração do Servidor KingHost

### 🖥️ Acesso e Ambiente
- [ ] Acesso SSH ao VPS configurado
- [ ] Usuário `sistema_imo` criado
- [ ] Diretórios necessários criados:
  - [ ] `/home/sistema_imo/apps/sistema_imo/`
  - [ ] `/home/sistema_imo/public_html/static/`
  - [ ] `/home/sistema_imo/public_html/media/`
  - [ ] `/home/sistema_imo/logs/`
  - [ ] `/home/sistema_imo/backups/`

### 🐘 PostgreSQL
- [ ] PostgreSQL instalado e rodando
- [ ] Banco `sistema_imobiliario` criado
- [ ] Usuário do banco criado com permissões
- [ ] Conexão testada

### 🔴 Redis
- [ ] Redis instalado e rodando
- [ ] Configuração de cache testada
- [ ] Conexão verificada

### 🐍 Python e Aplicação
- [ ] Python 3.8+ instalado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas via `pip install -r requirements.txt`
- [ ] Código clonado do repositório
- [ ] Arquivo `.env` configurado no servidor

### 🔧 Configuração da Aplicação
- [ ] Migrações executadas: `python manage.py migrate --settings=sistema_imobiliario.settings_production`
- [ ] Arquivos estáticos coletados: `python manage.py collectstatic --noinput --settings=sistema_imobiliario.settings_production`
- [ ] Superusuário criado: `python manage.py createsuperuser --settings=sistema_imobiliario.settings_production`
- [ ] Aplicação testada: `python manage.py check --settings=sistema_imobiliario.settings_production`

### 🦄 Gunicorn
- [ ] Arquivo `gunicorn.conf.py` copiado
- [ ] Arquivo de serviço `sistema_imo.service` instalado em `/etc/systemd/system/`
- [ ] Serviço habilitado: `sudo systemctl enable sistema_imo`
- [ ] Serviço iniciado: `sudo systemctl start sistema_imo`
- [ ] Status verificado: `sudo systemctl status sistema_imo`

### 🌐 Nginx
- [ ] Nginx instalado
- [ ] Arquivo de configuração copiado para `/etc/nginx/sites-available/sistema_imo`
- [ ] Site habilitado: `sudo ln -s /etc/nginx/sites-available/sistema_imo /etc/nginx/sites-enabled/`
- [ ] Configuração testada: `sudo nginx -t`
- [ ] Nginx recarregado: `sudo systemctl reload nginx`

### 🔒 SSL/HTTPS
- [ ] Certbot instalado
- [ ] Certificado SSL obtido: `sudo certbot --nginx -d seu-dominio.com.br -d www.seu-dominio.com.br`
- [ ] Renovação automática configurada
- [ ] HTTPS funcionando

### 📧 Email
- [ ] Configurações SMTP testadas
- [ ] Email de teste enviado
- [ ] Notificações funcionando

## Configurações de DNS

### 🌍 Domínio
- [ ] Registro A apontando para o IP do servidor
- [ ] Registro CNAME para `www` (opcional)
- [ ] Registros MX configurados (se necessário)
- [ ] TTL configurado adequadamente

## Testes Finais

### 🧪 Funcionalidades Básicas
- [ ] Site carrega em `https://seu-dominio.com.br`
- [ ] Login funcionando
- [ ] Admin acessível em `/admin/`
- [ ] Arquivos estáticos carregando
- [ ] Upload de arquivos funcionando

### 🧪 Funcionalidades Específicas
- [ ] Sistema de imóveis funcionando
- [ ] Contratos sendo criados
- [ ] Notificações sendo enviadas
- [ ] Relatórios sendo gerados
- [ ] Integração WhatsApp (se aplicável)
- [ ] Sistema de pagamentos (se aplicável)

### 🧪 Performance e Segurança
- [ ] Site carregando rapidamente
- [ ] Headers de segurança configurados
- [ ] Rate limiting funcionando
- [ ] Logs sendo gerados corretamente

## Monitoramento e Backup

### 📊 Monitoramento
- [ ] Logs configurados e acessíveis
- [ ] Sentry configurado (se aplicável)
- [ ] Monitoramento de recursos ativo

### 💾 Backup
- [ ] Script de backup configurado
- [ ] Backup automático agendado no crontab
- [ ] Teste de restore realizado
- [ ] Backup testado e funcionando

## Documentação

### 📚 Documentação Criada
- [ ] Credenciais documentadas e seguras
- [ ] Procedimentos de manutenção documentados
- [ ] Contatos de suporte anotados
- [ ] URLs importantes documentadas

### 📞 Suporte
- [ ] Contato da KingHost salvo
- [ ] Documentação de APIs salva
- [ ] Procedimentos de emergência definidos

## Pós-Deploy

### 🎯 Otimizações
- [ ] Cache configurado e funcionando
- [ ] Compressão Gzip ativa
- [ ] CDN configurado (se necessário)
- [ ] Performance otimizada

### 👥 Usuários
- [ ] Usuários migrados (se aplicável)
- [ ] Permissões configuradas
- [ ] Treinamento realizado

### 📈 Analytics
- [ ] Google Analytics configurado (se aplicável)
- [ ] Métricas de performance configuradas
- [ ] Relatórios de uso configurados

## ⚠️ Troubleshooting Comum

### Problemas Frequentes
- [ ] **Erro 502**: Verificar se Gunicorn está rodando
- [ ] **Erro 500**: Verificar logs do Django em `/home/sistema_imo/logs/`
- [ ] **Arquivos estáticos não carregam**: Verificar configuração do Nginx
- [ ] **Banco não conecta**: Verificar credenciais e firewall
- [ ] **Email não envia**: Verificar configurações SMTP

### Comandos Úteis
```bash
# Verificar status dos serviços
sudo systemctl status sistema_imo nginx postgresql redis

# Ver logs em tempo real
sudo journalctl -u sistema_imo -f
tail -f /home/sistema_imo/logs/django.log

# Reiniciar serviços
sudo systemctl restart sistema_imo
sudo systemctl reload nginx

# Testar configurações
python manage.py check --settings=sistema_imobiliario.settings_production
sudo nginx -t
```

## 🎉 Deploy Concluído!

Quando todos os itens estiverem marcados, seu Sistema Imobiliário estará rodando com sucesso na KingHost!

### Próximos Passos
1. Monitorar logs nas primeiras 24h
2. Realizar backup de teste
3. Configurar monitoramento contínuo
4. Treinar usuários finais
5. Documentar procedimentos específicos

---

**📞 Suporte KingHost:**
- Telefone: 0800 033 7777
- Chat: Disponível no painel
- Email: suporte@kinghost.com.br