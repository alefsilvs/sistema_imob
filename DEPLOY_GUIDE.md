# 🚀 GUIA COMPLETO DE DEPLOY E HOSPEDAGEM
## Sistema Imobiliário - ImobilPro

---

## 📋 ÍNDICE
1. [Opções de Hospedagem](#opções-de-hospedagem)
2. [Configuração Inicial](#configuração-inicial)
3. [Deploy Automático](#deploy-automático)
4. [Atualizações via Trae AI](#atualizações-via-trae-ai)
5. [Monitoramento](#monitoramento)
6. [Troubleshooting](#troubleshooting)

---

## 🏠 OPÇÕES DE HOSPEDAGEM

### 🥇 **DIGITALOCEAN (RECOMENDADO)**
- **Custo:** $5-20/mês
- **Vantagens:** 
  - Interface simples
  - Boa performance
  - Suporte 24/7
  - Backup automático
- **Configuração:** 1-click apps disponíveis

### 🥈 **AWS EC2**
- **Custo:** $10-30/mês
- **Vantagens:**
  - Escalabilidade infinita
  - Muitos serviços integrados
  - Free tier disponível
- **Configuração:** Mais complexa

### 🥉 **HEROKU**
- **Custo:** $7-25/mês
- **Vantagens:**
  - Deploy super simples
  - Git push automático
  - Add-ons prontos
- **Limitações:** Menos controle

### 💰 **VPS NACIONAL**
- **Custo:** R$ 15-50/mês
- **Vantagens:**
  - Suporte em português
  - Latência baixa no Brasil
  - Preços em reais

---

## ⚙️ CONFIGURAÇÃO INICIAL

### 1. **Preparar o Servidor**

```bash
# Conectar ao servidor
ssh root@SEU_IP

# Executar script de configuração
wget https://raw.githubusercontent.com/SEU_USUARIO/sistema-imobiliario/main/setup_servidor.sh
chmod +x setup_servidor.sh
./setup_servidor.sh
```

### 2. **Configurar Variáveis de Ambiente**

```bash
# Criar arquivo .env no servidor
nano /opt/sistema_imobiliario/.env
```

```env
# Configurações de produção
DEBUG=False
SECRET_KEY=sua_chave_secreta_super_segura_aqui
ALLOWED_HOSTS=seudominio.com.br,www.seudominio.com.br

# Banco de dados
DATABASE_URL=postgresql://sistema_imo_user:senha@localhost:5432/sistema_imo_db

# Evolution API
EVOLUTION_API_URL=http://localhost:8081
EVOLUTION_API_KEY=F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5
EVOLUTION_INSTANCE_NAME=sistema_imo

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha_app

# Configurações de mídia
MEDIA_URL=/media/
STATIC_URL=/static/
```

### 3. **Configurar Banco de Dados**

```bash
# Ativar ambiente virtual
source /opt/sistema_imobiliario/.venv/bin/activate

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

---

## 🔄 DEPLOY AUTOMÁTICO

### **Como Funciona:**

1. **Você edita código no Trae AI** ✏️
2. **Faz commit das mudanças** 📝
3. **Push para repositório Git** 📤
4. **Webhook detecta mudanças** 🔔
5. **Deploy automático executado** 🚀
6. **Site atualizado sem downtime** ✅

### **Configurar Webhook no GitHub:**

1. Vá em **Settings > Webhooks**
2. Clique em **Add webhook**
3. Configure:
   - **Payload URL:** `http://seudominio.com.br:5000/webhook/deploy`
   - **Content type:** `application/json`
   - **Secret:** `sistema_imo_webhook_secret_2024`
   - **Events:** `Just the push event`

### **Configurar Webhook no GitLab:**

1. Vá em **Settings > Webhooks**
2. Configure:
   - **URL:** `http://seudominio.com.br:5000/webhook/deploy`
   - **Secret Token:** `sistema_imo_webhook_secret_2024`
   - **Trigger:** `Push events`

---

## 🎯 ATUALIZAÇÕES VIA TRAE AI

### **Fluxo de Trabalho:**

```mermaid
graph LR
    A[Editar no Trae AI] --> B[Commit]
    B --> C[Push para Git]
    C --> D[Webhook Triggered]
    D --> E[Deploy Automático]
    E --> F[Site Atualizado]
```

### **Comandos no Trae AI:**

```bash
# 1. Fazer mudanças no código
# (editar arquivos normalmente)

# 2. Commit das mudanças
git add .
git commit -m "Atualização: nova funcionalidade X"

# 3. Push para repositório
git push origin main

# 4. Deploy automático acontece em segundos!
```

### **Monitorar Deploy:**

```bash
# Ver logs do deploy
curl http://seudominio.com.br:5000/webhook/logs

# Ver status dos serviços
systemctl status gunicorn
systemctl status evolution-api
systemctl status webhook-deploy
```

---

## 📊 MONITORAMENTO

### **Logs Importantes:**

```bash
# Logs do Django
tail -f /var/log/sistema_imobiliario/django.log

# Logs do deploy
tail -f /var/log/deploy_sistema.log

# Logs do webhook
tail -f /var/log/webhook_deploy.log

# Logs do Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### **Verificações de Saúde:**

```bash
# Testar se site está respondendo
curl -I http://seudominio.com.br

# Testar Evolution API
curl http://localhost:8081/instance/fetchInstances

# Verificar espaço em disco
df -h

# Verificar memória
free -h

# Verificar processos
ps aux | grep python
ps aux | grep node
```

---

## 🔧 TROUBLESHOOTING

### **Problemas Comuns:**

#### **1. Deploy Falhou**
```bash
# Ver logs do deploy
tail -f /var/log/deploy_sistema.log

# Executar deploy manual
cd /opt/sistema_imobiliario
./deploy_automatico.sh
```

#### **2. Site Não Carrega**
```bash
# Verificar Nginx
systemctl status nginx
systemctl restart nginx

# Verificar Gunicorn
systemctl status gunicorn
systemctl restart gunicorn
```

#### **3. Evolution API Não Funciona**
```bash
# Verificar serviço
systemctl status evolution-api
systemctl restart evolution-api

# Ver logs
journalctl -u evolution-api -f
```

#### **4. Banco de Dados com Erro**
```bash
# Verificar PostgreSQL
systemctl status postgresql

# Conectar ao banco
sudo -u postgres psql sistema_imo_db
```

### **Rollback de Emergência:**

```bash
# Listar backups disponíveis
ls -la /opt/backups/sistema_imobiliario/

# Restaurar backup
cd /opt/backups/sistema_imobiliario/
cp -r backup_YYYYMMDD_HHMMSS/* /opt/sistema_imobiliario/

# Reiniciar serviços
systemctl restart gunicorn
systemctl restart evolution-api
```

---

## 🛡️ SEGURANÇA

### **Checklist de Segurança:**

- [ ] Firewall configurado (UFW)
- [ ] SSL/HTTPS ativo (Let's Encrypt)
- [ ] Senhas fortes em todos os serviços
- [ ] Backup automático configurado
- [ ] Logs sendo monitorados
- [ ] Atualizações automáticas do sistema
- [ ] Webhook com secret configurado
- [ ] Usuários com permissões mínimas

### **Comandos de Segurança:**

```bash
# Verificar firewall
ufw status

# Renovar SSL
certbot renew

# Atualizar sistema
apt update && apt upgrade

# Verificar tentativas de login
tail -f /var/log/auth.log
```

---

## 📞 SUPORTE

### **Contatos Úteis:**

- **DigitalOcean:** https://cloud.digitalocean.com/support
- **AWS:** https://aws.amazon.com/support/
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **Nginx:** https://nginx.org/en/docs/

### **Comandos de Diagnóstico:**

```bash
# Relatório completo do sistema
./diagnostico_sistema.sh

# Teste de conectividade
ping google.com
curl -I https://seudominio.com.br

# Verificar recursos
htop
iotop
```

---

## 🎉 CONCLUSÃO

Com essa configuração, você terá:

✅ **Deploy automático** - Atualizações instantâneas via Trae AI  
✅ **Backup automático** - Segurança dos dados  
✅ **Monitoramento** - Logs e alertas  
✅ **SSL/HTTPS** - Segurança na comunicação  
✅ **Escalabilidade** - Fácil de expandir  
✅ **Rollback** - Volta rápida em caso de problemas  

**🚀 Agora é só hospedar e começar a usar!**