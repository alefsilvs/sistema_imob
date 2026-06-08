# 🇧🇷 GUIA COMPLETO - VPS NACIONAL BRASILEIRO
## Sistema Imobiliário - ImobilPro

---

## 🏆 **MELHORES PROVEDORES VPS NACIONAIS 2024**

### 🥇 **KINGHOST** - Recomendado
- **💰 Preço:** R$ 22,90 - R$ 189,90/mês <mcreference link="https://king.host/servidor-vps" index="1">1</mcreference>
- **🇧🇷 Vantagens:**
  - Infraestrutura 100% nacional
  - SLA 99,9% garantido
  - Suporte 24/7 em português
  - Pagamento em reais (sem IOF)
  - Baixa latência no Brasil
- **📊 Planos:**
  - **VPS 1GB:** R$ 22,90/mês - 1GB RAM, 50GB SSD
  - **VPS 4GB:** R$ 34,90/mês - 4GB RAM, 70GB SSD ⭐ **RECOMENDADO**
  - **VPS 8GB:** R$ 139,90/mês - 8GB RAM, 170GB SSD

### 🥈 **LOCAWEB** - Tradicional
- **💰 Preço:** R$ 15,90 - R$ 200+/mês <mcreference link="https://tudosobrehospedagemdesites.com.br/melhor-vps/" index="3">3</mcreference>
- **🇧🇷 Vantagens:**
  - Empresa brasileira tradicional
  - Datacenter no Brasil
  - Suporte em português
  - Windows e Linux disponíveis
- **📊 Planos:**
  - **VPS Básico:** R$ 15,90/mês - 512MB RAM, 20GB SSD
  - **VPS Intermediário:** R$ 45,90/mês - 2GB RAM, 40GB SSD

### 🥉 **HOSTINGER BRASIL** - Custo-Benefício
- **💰 Preço:** R$ 27,99 - R$ 150+/mês <mcreference link="https://tudosobrehospedagemdesites.com.br/melhor-vps/" index="3">3</mcreference>
- **🇧🇷 Vantagens:**
  - Excelente custo-benefício
  - Tecnologia KVM
  - Backup semanal incluído
  - 30 dias garantia
- **📊 Planos:**
  - **VPS 1:** R$ 27,99/mês - 4GB RAM, 50GB SSD ⭐ **MELHOR CUSTO-BENEFÍCIO**

---

## 🚀 **CONFIGURAÇÃO RÁPIDA - PASSO A PASSO**

### **1. Contratar VPS**
1. Escolha um provedor (recomendo **KingHost VPS 4GB**)
2. Contrate o plano
3. Anote IP, usuário e senha do servidor

### **2. Conectar ao Servidor**
```bash
# Windows (PowerShell)
ssh root@SEU_IP_DO_SERVIDOR

# Ou use PuTTY se preferir interface gráfica
```

### **3. Executar Configuração Automática**
```bash
# Baixar script de configuração
wget https://raw.githubusercontent.com/SEU_USUARIO/sistema-imobiliario/main/setup_vps_brasil.sh

# Dar permissão de execução
chmod +x setup_vps_brasil.sh

# Executar configuração (demora ~10 minutos)
sudo bash setup_vps_brasil.sh
```

### **4. Configurar Variáveis de Ambiente**
```bash
# Editar arquivo .env
nano /opt/sistema_imobiliario/.env
```

**Conteúdo do .env para produção:**
```env
# CONFIGURAÇÃO DE PRODUÇÃO
DEBUG=False
SECRET_KEY=sua_chave_super_secreta_aqui_com_50_caracteres
ALLOWED_HOSTS=seudominio.com.br,www.seudominio.com.br,SEU_IP

# BANCO DE DADOS
DATABASE_URL=postgresql://sistema_imo_user:SUA_SENHA@localhost:5432/sistema_imo_db

# EVOLUTION API
EVOLUTION_API_URL=http://localhost:8081
EVOLUTION_API_KEY=F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5
EVOLUTION_INSTANCE_NAME=sistema_imo

# EMAIL (Configure com seu provedor)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha_de_app

# CONFIGURAÇÕES DE MÍDIA
MEDIA_URL=/media/
STATIC_URL=/static/
MEDIA_ROOT=/opt/sistema_imobiliario/media
STATIC_ROOT=/opt/sistema_imobiliario/staticfiles

# CONFIGURAÇÕES DE SEGURANÇA
SECURE_SSL_REDIRECT=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
```

### **5. Finalizar Configuração**
```bash
# Ativar ambiente virtual
cd /opt/sistema_imobiliario
source .venv/bin/activate

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviços
sudo systemctl restart gunicorn
sudo systemctl restart evolution-api
sudo systemctl restart nginx
```

---

## 🌐 **CONFIGURAR DOMÍNIO .COM.BR**

### **Registrar Domínio:**
- **Registro.br** (oficial): R$ 40/ano
- **KingHost Domínios**: R$ 45/ano
- **Locaweb Domínios**: R$ 50/ano

### **Configurar DNS:**
```
Tipo: A
Nome: @
Valor: SEU_IP_DO_VPS

Tipo: A  
Nome: www
Valor: SEU_IP_DO_VPS

Tipo: CNAME
Nome: evolution
Valor: seudominio.com.br
```

### **Configurar SSL Gratuito:**
```bash
# Instalar certificado Let's Encrypt
sudo certbot --nginx -d seudominio.com.br -d www.seudominio.com.br

# Renovação automática já configurada
```

---

## 🔄 **DEPLOY AUTOMÁTICO VIA TRAE AI**

### **1. Configurar Repositório Git**
```bash
# No Trae AI, inicializar Git
git init
git add .
git commit -m "Configuração inicial do sistema"

# Criar repositório no GitHub
# Fazer push do código
git remote add origin https://github.com/SEU_USUARIO/sistema-imobiliario.git
git push -u origin main
```

### **2. Configurar Webhook**
**No GitHub:**
1. Vá em **Settings > Webhooks**
2. **Add webhook**
3. **Payload URL:** `http://seudominio.com.br:5000/webhook/deploy`
4. **Content type:** `application/json`
5. **Secret:** `sistema_imo_webhook_secret_2024`
6. **Events:** `Just the push event`

### **3. Testar Deploy Automático**
```bash
# No Trae AI, fazer uma mudança
# Exemplo: editar um arquivo
git add .
git commit -m "Teste de deploy automático"
git push origin main

# Em segundos, o site será atualizado automaticamente! 🚀
```

---

## 📊 **MONITORAMENTO E MANUTENÇÃO**

### **Verificar Status dos Serviços:**
```bash
# Status geral
sudo systemctl status gunicorn
sudo systemctl status evolution-api
sudo systemctl status nginx
sudo systemctl status webhook-deploy

# Logs em tempo real
sudo tail -f /var/log/sistema_imobiliario/monitor.log
sudo tail -f /var/log/nginx/sistema_imo_access.log
```

### **Comandos Úteis:**
```bash
# Ver uso de recursos
htop

# Espaço em disco
df -h

# Memória
free -h

# Reiniciar todos os serviços
sudo systemctl restart gunicorn evolution-api nginx

# Backup manual
sudo /opt/sistema_imobiliario/backup_sistema.sh
```

### **Logs Importantes:**
- **Sistema:** `/var/log/sistema_imobiliario/`
- **Nginx:** `/var/log/nginx/`
- **Deploy:** `/var/log/deploy_sistema.log`
- **Monitor:** `/var/log/sistema_imobiliario/monitor.log`

---

## 💰 **CUSTOS MENSAIS ESTIMADOS**

### **Configuração Recomendada:**
- **VPS KingHost 4GB:** R$ 34,90/mês
- **Domínio .com.br:** R$ 3,33/mês (R$ 40/ano)
- **SSL:** Gratuito (Let's Encrypt)
- **Backup:** Incluído
- **Total:** **R$ 38,23/mês**

### **Configuração Econômica:**
- **VPS Locaweb Básico:** R$ 15,90/mês
- **Domínio .com.br:** R$ 3,33/mês
- **Total:** **R$ 19,23/mês**

### **Configuração Premium:**
- **VPS KingHost 8GB:** R$ 139,90/mês
- **Domínio .com.br:** R$ 3,33/mês
- **Total:** **R$ 143,23/mês**

---

## 🛡️ **SEGURANÇA E BACKUP**

### **Recursos de Segurança Incluídos:**
✅ Firewall UFW configurado  
✅ Fail2Ban contra ataques  
✅ SSL/HTTPS obrigatório  
✅ Headers de segurança  
✅ Backup automático diário  
✅ Monitoramento de recursos  
✅ Logs de auditoria  

### **Backup Automático:**
```bash
# Backup é executado automaticamente às 2h da manhã
# Localização: /opt/backups/sistema_imobiliario/
# Mantém os 5 backups mais recentes

# Restaurar backup manualmente:
sudo cp -r /opt/backups/sistema_imobiliario/backup_YYYYMMDD_HHMMSS/* /opt/sistema_imobiliario/
sudo systemctl restart gunicorn evolution-api
```

---

## 🚨 **TROUBLESHOOTING VPS NACIONAL**

### **Site Não Carrega:**
```bash
# Verificar Nginx
sudo nginx -t
sudo systemctl restart nginx

# Verificar Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f
```

### **Evolution API Não Funciona:**
```bash
# Verificar serviço
sudo systemctl status evolution-api
sudo journalctl -u evolution-api -f

# Reiniciar
sudo systemctl restart evolution-api
```

### **Deploy Não Funciona:**
```bash
# Verificar webhook
curl http://seudominio.com.br:5000/webhook/status

# Ver logs
sudo tail -f /var/log/webhook_deploy.log
```

### **Performance Lenta:**
```bash
# Verificar recursos
htop
iotop

# Otimizar banco
sudo -u postgres vacuumdb -d sistema_imo_db --analyze --verbose
```

---

## 📞 **SUPORTE TÉCNICO**

### **Contatos dos Provedores:**
- **KingHost:** 0800 7000 141 / chat online
- **Locaweb:** 0800 888 0100 / suporte@locaweb.com.br
- **Hostinger:** Chat online 24/7

### **Documentação Oficial:**
- **Let's Encrypt:** https://letsencrypt.org/pt-br/
- **Nginx:** https://nginx.org/en/docs/
- **PostgreSQL:** https://www.postgresql.org/docs/

---

## 🎉 **VANTAGENS DO VPS NACIONAL**

✅ **Latência baixa** - Servidores no Brasil  
✅ **Suporte em português** - Atendimento nacional  
✅ **Pagamento em reais** - Sem IOF ou variação cambial  
✅ **Conformidade LGPD** - Dados no território nacional  
✅ **Horário comercial brasileiro** - Suporte no nosso fuso  
✅ **Legislação brasileira** - Proteção legal nacional  

---

## 🚀 **CONCLUSÃO**

Com um VPS nacional brasileiro, você terá:

🇧🇷 **Infraestrutura nacional** - Melhor performance no Brasil  
💰 **Custo previsível** - Pagamento em reais  
🔄 **Deploy automático** - Atualizações via Trae AI  
🛡️ **Segurança completa** - SSL, firewall, backup  
📞 **Suporte em português** - Atendimento nacional  

**💡 Recomendação:** Comece com o **KingHost VPS 4GB** por R$ 34,90/mês. É o melhor custo-benefício para o sistema imobiliário!

**🚀 Pronto para hospedar? Siga o passo a passo acima e em 30 minutos seu sistema estará online!**