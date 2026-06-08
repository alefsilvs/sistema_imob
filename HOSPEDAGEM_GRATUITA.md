# 🚀 Hospedagem Gratuita - Sistema Imobiliário

## 📋 Visão Geral

Este documento apresenta as **melhores opções de hospedagem gratuita** para o Sistema Imobiliário Django, com configurações completas e guias passo a passo.

## 🎯 Plataformas Recomendadas

### 🥇 1. Railway (MAIS RECOMENDADO)
- ✅ **500 horas gratuitas/mês**
- ✅ **1GB RAM**
- ✅ **PostgreSQL incluído**
- ✅ **Deploy automático via GitHub**
- ✅ **SSL automático**
- ✅ **Domínio personalizado gratuito**

**📖 Guia:** [HOSPEDAGEM_GRATUITA_RAILWAY.md](HOSPEDAGEM_GRATUITA_RAILWAY.md)

### 🥈 2. Render.com
- ✅ **750 horas gratuitas/mês**
- ✅ **512MB RAM**
- ✅ **PostgreSQL incluído**
- ✅ **Deploy automático via GitHub**
- ✅ **SSL automático**
- ✅ **Interface intuitiva**

**📖 Guia:** [HOSPEDAGEM_GRATUITA_RENDER.md](HOSPEDAGEM_GRATUITA_RENDER.md)

### 🥉 3. Heroku (PAGO)
- ❌ **Plano gratuito descontinuado**
- 💰 **$10+/mês mínimo**
- ✅ **Plataforma madura**
- ✅ **Muitos add-ons**

**📖 Guia:** [HOSPEDAGEM_GRATUITA_HEROKU.md](HOSPEDAGEM_GRATUITA_HEROKU.md)

## 📊 Comparação Detalhada

| Recurso | Railway | Render | Heroku |
|---------|---------|--------|--------|
| **Horas gratuitas** | 500h/mês | 750h/mês | ❌ Pago |
| **RAM** | 1GB | 512MB | 512MB+ |
| **Armazenamento** | 1GB | 1GB | Variável |
| **PostgreSQL** | ✅ Grátis | ✅ Grátis | 💰 $5/mês |
| **Redis** | ✅ Grátis | ❌ Pago | 💰 $3/mês |
| **SSL** | ✅ Auto | ✅ Auto | ✅ Auto |
| **Domínio custom** | ✅ Grátis | ✅ Grátis | 💰 Pago |
| **Deploy automático** | ✅ GitHub | ✅ GitHub | ✅ GitHub |
| **Hibernação** | Após inatividade | 15min inativo | N/A |
| **Suporte** | Comunidade | Comunidade | Pago |

## 🚀 Início Rápido

### 1. Executar Script de Configuração

```bash
python setup_hospedagem_gratuita.py
```

### 2. Escolher Plataforma

O script apresentará as opções e configurará automaticamente os arquivos necessários.

### 3. Seguir Guia Específico

Cada plataforma tem um guia detalhado com instruções passo a passo.

## 📁 Arquivos de Configuração

### Railway
- `railway.json` - Configurações da plataforma
- `Procfile` - Comandos de execução
- `runtime.txt` - Versão do Python
- `settings_railway.py` - Configurações Django
- `.env.railway.example` - Variáveis de ambiente

### Render.com
- `render.yaml` - Configurações da plataforma
- `build.sh` - Script de build
- `settings_render.py` - Configurações Django
- `.env.render.example` - Variáveis de ambiente

### Heroku
- `Procfile` - Comandos de execução
- `runtime.txt` - Versão do Python
- `settings_heroku.py` - Configurações Django
- `.env.heroku.example` - Variáveis de ambiente

## ⚙️ Configurações Comuns

### Variáveis de Ambiente Essenciais

```bash
# Básicas
SECRET_KEY=sua_chave_secreta_super_segura
DEBUG=False
DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_railway

# Email
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app_gmail
DEFAULT_FROM_EMAIL=seu_email@gmail.com

# Domínio (opcional)
CUSTOM_DOMAIN=seudominio.com
```

### Dependências Adicionais

```txt
# requirements.txt - Adicionar para hospedagem
dj-database-url>=2.1.0
django-redis>=5.4.0
gunicorn>=21.2.0
whitenoise>=6.5.0
```

## 🔧 Configuração de Email

### Gmail (Recomendado)

1. **Ativar verificação em 2 etapas**
2. **Gerar senha de app específica**
3. **Usar a senha de app nas variáveis de ambiente**

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app_de_16_caracteres
```

## 🌐 Domínio Personalizado

### Configuração DNS

```bash
# CNAME Record
www.seudominio.com -> seu-app.railway.app
# ou
www.seudominio.com -> seu-app.onrender.com
```

### Certificado SSL

Todas as plataformas oferecem SSL automático e gratuito via Let's Encrypt.

## 📊 Monitoramento

### Logs em Tempo Real

```bash
# Railway CLI
railway logs

# Render Dashboard
# Acesse Logs tab no dashboard

# Heroku CLI
heroku logs --tail
```

### Métricas Disponíveis

- **CPU Usage**
- **Memory Usage**
- **Response Time**
- **Error Rate**
- **Uptime**

## 🔒 Segurança

### Configurações Implementadas

- ✅ **HTTPS obrigatório**
- ✅ **Headers de segurança**
- ✅ **CSRF protection**
- ✅ **XSS protection**
- ✅ **Content Security Policy**
- ✅ **HSTS headers**

### Variáveis Sensíveis

- ❌ **Nunca commitar** chaves secretas
- ✅ **Usar variáveis de ambiente**
- ✅ **Gerar chaves únicas** para produção
- ✅ **Rotacionar chaves** periodicamente

## 🚨 Limitações dos Planos Gratuitos

### Railway
- **500 horas/mês** (≈ 20 dias)
- **Hibernação** após inatividade
- **1GB** de armazenamento

### Render.com
- **750 horas/mês** (≈ 31 dias)
- **Hibernação** após 15min inativo
- **512MB** RAM

### Soluções para Hibernação

1. **Ping services** (UptimeRobot, etc.)
2. **Cron jobs** para manter ativo
3. **Upgrade** para plano pago

## 🔄 Migração Entre Plataformas

### Backup de Dados

```bash
# PostgreSQL
pg_dump DATABASE_URL > backup.sql

# Arquivos de mídia
tar -czf media_backup.tar.gz media/
```

### Processo de Migração

1. **Exportar dados** da plataforma atual
2. **Configurar nova plataforma**
3. **Importar dados**
4. **Testar funcionalidades**
5. **Atualizar DNS**

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Build Falha
- Verificar `requirements.txt`
- Conferir versão do Python
- Checar logs de build

#### 2. Aplicação Não Inicia
- Verificar `Procfile`/comando de start
- Conferir configurações Django
- Verificar variáveis de ambiente

#### 3. Erro de Banco
- Verificar `DATABASE_URL`
- Executar migrações
- Conferir conexão

#### 4. Arquivos Estáticos
- Executar `collectstatic`
- Verificar configurações do WhiteNoise
- Conferir `STATIC_ROOT`

## 📚 Recursos Adicionais

### Documentação Oficial
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Heroku Docs](https://devcenter.heroku.com/)

### Tutoriais Django
- [Django Deployment](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [Django Security](https://docs.djangoproject.com/en/4.2/topics/security/)

### Ferramentas Úteis
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Sentry](https://sentry.io/) - Monitoramento de erros
- [UptimeRobot](https://uptimerobot.com/) - Monitoramento de uptime

## 🎯 Recomendações

### Para Desenvolvimento
1. **Use Railway** - Melhor experiência gratuita
2. **Configure monitoramento** desde o início
3. **Implemente backup** automático
4. **Teste em ambiente** similar à produção

### Para Produção
1. **Considere upgrade** para planos pagos
2. **Configure CDN** para arquivos estáticos
3. **Implemente cache** Redis
4. **Configure alertas** de monitoramento

## 🚀 Próximos Passos

1. **Escolher plataforma** (Railway recomendado)
2. **Executar script** de configuração
3. **Seguir guia específico** da plataforma
4. **Configurar domínio** personalizado
5. **Implementar monitoramento**
6. **Testar funcionalidades**

---

**💡 Dica:** Comece com o Railway para a melhor experiência gratuita, e considere o Render.com como alternativa. Ambos oferecem excelente suporte ao Django com PostgreSQL incluído!