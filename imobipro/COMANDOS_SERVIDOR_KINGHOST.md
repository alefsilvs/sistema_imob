# 🏆 COMANDOS PARA SERVIDOR KINGHOST

## 📋 PASSO A PASSO COMPLETO

### 1. CONECTAR AO SERVIDOR
```bash
# Substitua SEU_IP_KINGHOST pelo IP real
ssh root@SEU_IP_KINGHOST
```

### 2. CONFIGURAÇÃO AUTOMÁTICA
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Baixar script de configuração
wget https://raw.githubusercontent.com/alefsilvs/sistema-imobili-rio/main/setup_vps_brasil.sh

# Dar permissão
chmod +x setup_vps_brasil.sh

# Executar configuração (demora ~10 minutos)
sudo bash setup_vps_brasil.sh
```

### 3. CONFIGURAR VARIÁVEIS DE AMBIENTE
```bash
# Editar arquivo .env
nano /opt/sistema_imobiliario/.env

# Copie o conteúdo do arquivo .env.servidor (criado localmente)
# Substitua os valores pelos seus dados reais
```

### 4. FINALIZAR CONFIGURAÇÃO
```bash
# Ir para diretório do projeto
cd /opt/sistema_imobiliario

# Ativar ambiente virtual
source .venv/bin/activate

# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar serviços
sudo systemctl restart gunicorn evolution-api nginx
```

### 5. VERIFICAR SE ESTÁ FUNCIONANDO
```bash
# Verificar status dos serviços
sudo systemctl status gunicorn
sudo systemctl status evolution-api
sudo systemctl status nginx

# Ver logs em tempo real
sudo tail -f /var/log/sistema_imobiliario/monitor.log
```

### 6. CONFIGURAR SSL (OPCIONAL)
```bash
# Se você tem um domínio
sudo certbot --nginx -d seudominio.com.br -d www.seudominio.com.br
```

## 🔧 COMANDOS ÚTEIS

### Reiniciar Serviços
```bash
sudo systemctl restart gunicorn evolution-api nginx
```

### Ver Logs
```bash
# Logs do Django
sudo tail -f /var/log/sistema_imobiliario/django.log

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Logs do sistema
sudo tail -f /var/log/sistema_imobiliario/monitor.log
```

### Backup Manual
```bash
sudo /opt/sistema_imobiliario/backup_sistema.sh
```

### Atualizar Sistema
```bash
# Fazer pull do GitHub
cd /opt/sistema_imobiliario
git pull origin main

# Reinstalar dependências se necessário
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic --noinput

# Reiniciar
sudo systemctl restart gunicorn
```

## 📞 SUPORTE KINGHOST
- **Telefone:** 0800 7000 141
- **Chat:** Disponível 24/7 no painel
- **Email:** suporte@kinghost.com.br

## 🎯 PRÓXIMOS PASSOS
1. Contratar VPS KingHost
2. Conectar via SSH
3. Executar comandos acima
4. Configurar .env com seus dados
5. Testar sistema funcionando

## ✅ SISTEMA FUNCIONANDO
Após configuração, acesse:
- **Site:** http://SEU_IP_KINGHOST
- **Admin:** http://SEU_IP_KINGHOST/admin
- **Evolution API:** http://SEU_IP_KINGHOST/evolution/manager