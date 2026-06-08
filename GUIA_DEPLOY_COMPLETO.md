# 🚀 Guia Completo de Deploy - Sistema Imobiliário

Guia passo a passo para hospedar o Sistema Imobiliário completo em produção com todas as APIs e tecnologias integradas.

## 📋 Visão Geral do Sistema

### Tecnologias Utilizadas
- **Backend**: Django 4.2+ com Python 3.11+
- **Banco de Dados**: PostgreSQL 14+
- **Cache/Sessões**: Redis 6+
- **Servidor Web**: Nginx
- **WSGI**: Gunicorn
- **WhatsApp**: Evolution API
- **Tarefas Assíncronas**: Celery + Redis
- **SSL**: Let's Encrypt (Certbot)
- **Sistema Operacional**: Ubuntu 22.04 LTS

### Arquitetura do Sistema
```
[Internet] → [Nginx] → [Gunicorn] → [Django]
                ↓
           [Evolution API] → [WhatsApp]
                ↓
         [PostgreSQL] ← [Redis] → [Celery]
```

## 🖥️ Preparação do Servidor

### 1. Requisitos Mínimos
- **CPU**: 2 vCPUs
- **RAM**: 4GB (recomendado 8GB)
- **Storage**: 50GB SSD
- **Banda**: 100 Mbps
- **OS**: Ubuntu 22.04 LTS

### 2. Configuração Inicial do Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y curl wget git vim htop unzip software-properties-common

# Configurar timezone
sudo timedatectl set-timezone America/Sao_Paulo

# Configurar firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

## 🐍 Instalação do Python e Dependências

```bash
# Instalar Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Instalar dependências do sistema
sudo apt install -y build-essential libpq-dev libssl-dev libffi-dev
sudo apt install -y libjpeg-dev libpng-dev libwebp-dev
sudo apt install -y pkg-config libcairo2-dev libgirepository1.0-dev
```

## 🗄️ Instalação e Configuração do PostgreSQL

```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Configurar PostgreSQL
sudo -u postgres psql << EOF
CREATE USER imobiliario_user WITH PASSWORD 'senha_super_segura';
CREATE DATABASE imobiliario_db OWNER imobiliario_user;
GRANT ALL PRIVILEGES ON DATABASE imobiliario_db TO imobiliario_user;

CREATE USER evolution_user WITH PASSWORD 'evolution_pass';
CREATE DATABASE evolution_db OWNER evolution_user;
GRANT ALL PRIVILEGES ON DATABASE evolution_db TO evolution_user;
\q
EOF

# Configurar acesso
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/g" /etc/postgresql/14/main/postgresql.conf
sudo systemctl restart postgresql
```

## 🔴 Instalação e Configuração do Redis

```bash
# Instalar Redis
sudo apt install -y redis-server

# Configurar Redis
sudo sed -i 's/supervised no/supervised systemd/g' /etc/redis/redis.conf
sudo sed -i 's/# maxmemory <bytes>/maxmemory 1gb/g' /etc/redis/redis.conf
sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/g' /etc/redis/redis.conf

# Reiniciar Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## 🌐 Instalação e Configuração do Nginx

```bash
# Instalar Nginx
sudo apt install -y nginx

# Copiar configuração (usar arquivo nginx_config.conf)
sudo cp nginx_config.conf /etc/nginx/sites-available/imobiliario
sudo ln -s /etc/nginx/sites-available/imobiliario /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 📦 Instalação do Node.js (para Evolution API)

```bash
# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar instalação
node --version
npm --version
```

## 🚀 Deploy da Aplicação Django

### 1. Preparar Ambiente

```bash
# Criar usuário para aplicação
sudo useradd -r -s /bin/bash -d /opt/imobiliario imobiliario
sudo mkdir -p /opt/imobiliario
sudo chown imobiliario:imobiliario /opt/imobiliario

# Mudar para usuário da aplicação
sudo su - imobiliario
```

### 2. Clonar e Configurar Projeto

```bash
# Clonar projeto (substitua pela URL do seu repositório)
git clone https://github.com/seu-usuario/sistema-imobiliario.git /opt/imobiliario/app
cd /opt/imobiliario/app

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env (usar VARIAVEIS_AMBIENTE.md como referência)
cp .env.example .env
vim .env

# Configurar variáveis principais:
# DEBUG=False
# SECRET_KEY=sua_chave_secreta_aqui
# DATABASE_URL=postgresql://imobiliario_user:senha_super_segura@localhost:5432/imobiliario_db
# REDIS_URL=redis://localhost:6379/0
# ALLOWED_HOSTS=seudominio.com.br,www.seudominio.com.br
```

### 4. Executar Migrações e Coletar Arquivos Estáticos

```bash
# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar diretórios de mídia
mkdir -p media/imoveis media/documentos media/temp
```

## 📱 Configuração da Evolution API

### 1. Instalar Evolution API

```bash
# Criar usuário para Evolution API
sudo useradd -r -s /bin/bash -d /opt/evolution-api evolution
sudo mkdir -p /opt/evolution-api
sudo chown evolution:evolution /opt/evolution-api

# Mudar para usuário evolution
sudo su - evolution

# Clonar e instalar
git clone https://github.com/EvolutionAPI/evolution-api.git /opt/evolution-api
cd /opt/evolution-api
npm install
npm run build
```

### 2. Configurar Evolution API

```bash
# Criar arquivo .env (usar EVOLUTION_API_SETUP.md como referência)
vim /opt/evolution-api/.env

# Configurações principais:
# NODE_ENV=production
# PORT=8080
# SERVER_URL=https://seudominio.com.br
# DATABASE_CONNECTION_URI=postgresql://evolution_user:evolution_pass@localhost:5432/evolution_db
# REDIS_URI=redis://localhost:6379/5
```

## ⚙️ Configuração dos Serviços Systemd

```bash
# Copiar configurações de serviço (usar systemd_services.conf)
sudo cp systemd_services.conf /tmp/

# Extrair e instalar serviços
sudo systemctl daemon-reload

# Ativar serviços
sudo systemctl enable gunicorn-imobiliario.service
sudo systemctl enable celery-imobiliario.service
sudo systemctl enable celerybeat-imobiliario.service
sudo systemctl enable evolution-api.service
sudo systemctl enable notificacoes-imobiliario.service

# Iniciar serviços
sudo systemctl start gunicorn-imobiliario.service
sudo systemctl start celery-imobiliario.service
sudo systemctl start celerybeat-imobiliario.service
sudo systemctl start evolution-api.service
sudo systemctl start notificacoes-imobiliario.service
```

## 🔒 Configuração SSL com Let's Encrypt

```bash
# Executar script SSL (usar ssl_setup.sh)
chmod +x ssl_setup.sh
sudo ./ssl_setup.sh seudominio.com.br admin@seudominio.com.br

# Verificar certificado
sudo certbot certificates

# Testar renovação automática
sudo certbot renew --dry-run
```

## 🔍 Verificação e Testes

### 1. Verificar Serviços

```bash
# Status dos serviços
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status gunicorn-imobiliario
sudo systemctl status celery-imobiliario
sudo systemctl status evolution-api

# Verificar portas
sudo netstat -tlnp | grep -E ':(80|443|5432|6379|8000|8080)'
```

### 2. Testes de Conectividade

```bash
# Testar aplicação Django
curl -I https://seudominio.com.br

# Testar Evolution API
curl -I https://seudominio.com.br/evolution/

# Testar admin Django
curl -I https://seudominio.com.br/admin/

# Testar API
curl -I https://seudominio.com.br/api/
```

### 3. Verificar Logs

```bash
# Logs do Django/Gunicorn
sudo journalctl -u gunicorn-imobiliario -f

# Logs do Celery
sudo journalctl -u celery-imobiliario -f

# Logs da Evolution API
sudo journalctl -u evolution-api -f

# Logs do Nginx
sudo tail -f /var/log/nginx/imobiliario_access.log
sudo tail -f /var/log/nginx/imobiliario_error.log
```

## 📱 Configuração Final do WhatsApp

### 1. Criar Instância WhatsApp

```bash
# Criar instância
curl -X POST "https://seudominio.com.br/evolution/instance/create" \
  -H "apikey: sua_chave_da_api" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "sistema_imobiliario",
    "token": "token_da_instancia",
    "qrcode": true,
    "webhook": "https://seudominio.com.br/webhook/whatsapp/"
  }'
```

### 2. Conectar WhatsApp

```bash
# Obter QR Code
curl -X GET "https://seudominio.com.br/evolution/instance/connect/sistema_imobiliario" \
  -H "apikey: sua_chave_da_api"

# Escanear QR Code com WhatsApp
# Verificar conexão
curl -X GET "https://seudominio.com.br/evolution/instance/connectionState/sistema_imobiliario" \
  -H "apikey: sua_chave_da_api"
```

## 🔄 Configuração de Backup Automático

```bash
# Configurar script de backup (usar backup_script.sh)
chmod +x backup_script.sh
sudo cp backup_script.sh /opt/imobiliario/

# Configurar cron para backup diário
sudo crontab -e
# Adicionar linha:
# 0 2 * * * /opt/imobiliario/backup_script.sh

# Testar backup
sudo /opt/imobiliario/backup_script.sh
```

## 📊 Monitoramento e Manutenção

### 1. Comandos de Monitoramento

```bash
# Verificar uso de recursos
htop
df -h
free -h

# Verificar conexões
sudo netstat -an | grep ESTABLISHED | wc -l

# Verificar logs de erro
sudo grep -i error /var/log/nginx/imobiliario_error.log
sudo journalctl -u gunicorn-imobiliario --since "1 hour ago" | grep -i error
```

### 2. Manutenção Regular

```bash
# Atualizar sistema (mensal)
sudo apt update && sudo apt upgrade -y

# Limpar logs antigos (semanal)
sudo journalctl --vacuum-time=30d

# Verificar espaço em disco (diário)
df -h

# Verificar backup (diário)
ls -la /backup/imobiliario/
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro 502 Bad Gateway**
   ```bash
   # Verificar se Gunicorn está rodando
   sudo systemctl status gunicorn-imobiliario
   
   # Reiniciar se necessário
   sudo systemctl restart gunicorn-imobiliario
   ```

2. **WhatsApp desconectado**
   ```bash
   # Verificar Evolution API
   sudo systemctl status evolution-api
   
   # Reconectar instância
   curl -X GET "https://seudominio.com.br/evolution/instance/connect/sistema_imobiliario" \
     -H "apikey: sua_chave_da_api"
   ```

3. **Banco de dados lento**
   ```bash
   # Verificar conexões ativas
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Analisar queries lentas
   sudo -u postgres psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

4. **Erro de memória**
   ```bash
   # Verificar uso de memória
   free -h
   
   # Verificar processos que mais consomem
   ps aux --sort=-%mem | head -10
   
   # Reiniciar serviços se necessário
   sudo systemctl restart celery-imobiliario
   ```

## ✅ Checklist Final de Deploy

### Infraestrutura
- [ ] Servidor Ubuntu 22.04 configurado
- [ ] Firewall configurado (portas 80, 443, 22)
- [ ] Domínio apontando para o servidor
- [ ] Certificado SSL ativo

### Banco de Dados
- [ ] PostgreSQL instalado e configurado
- [ ] Usuários e bancos criados
- [ ] Backup automático configurado

### Aplicação Django
- [ ] Código clonado e dependências instaladas
- [ ] Variáveis de ambiente configuradas
- [ ] Migrações executadas
- [ ] Superusuário criado
- [ ] Arquivos estáticos coletados
- [ ] Gunicorn configurado e rodando

### Servidor Web
- [ ] Nginx instalado e configurado
- [ ] Proxy reverso funcionando
- [ ] SSL/HTTPS ativo
- [ ] Rate limiting configurado

### Cache e Sessões
- [ ] Redis instalado e configurado
- [ ] Cache funcionando
- [ ] Sessões no Redis

### Tarefas Assíncronas
- [ ] Celery worker rodando
- [ ] Celery beat rodando
- [ ] Tarefas sendo processadas

### WhatsApp Integration
- [ ] Evolution API instalada
- [ ] Instância criada
- [ ] WhatsApp conectado
- [ ] Webhook funcionando
- [ ] Envio de mensagens testado

### Monitoramento
- [ ] Logs configurados
- [ ] Backup automático ativo
- [ ] Monitoramento de recursos
- [ ] Alertas configurados

### Testes Finais
- [ ] Site acessível via HTTPS
- [ ] Admin Django funcionando
- [ ] API respondendo
- [ ] WhatsApp enviando mensagens
- [ ] Cadastro de imóveis funcionando
- [ ] Upload de imagens funcionando
- [ ] Notificações por email funcionando
- [ ] Backup testado e funcionando

## 🎉 Conclusão

Com este guia, você terá um Sistema Imobiliário completo e robusto rodando em produção com:

- ✅ **Alta Performance**: Nginx + Gunicorn + Redis
- ✅ **Segurança**: SSL/HTTPS + Firewall + Rate Limiting
- ✅ **Escalabilidade**: Celery + Redis + PostgreSQL
- ✅ **Integração WhatsApp**: Evolution API completa
- ✅ **Backup Automático**: Dados protegidos
- ✅ **Monitoramento**: Logs e alertas
- ✅ **Manutenção**: Scripts automatizados

Seu sistema estará pronto para receber milhares de usuários e processar centenas de imóveis com total confiabilidade!

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte os logs do sistema
2. Verifique o status dos serviços
3. Consulte a documentação específica de cada componente
4. Execute os comandos de troubleshooting

**Boa sorte com seu Sistema Imobiliário em produção! 🏠🚀**