# 🐙 Hospedagem no GitHub - Sistema Imobiliário

Guia sobre as possibilidades e limitações de hospedar o Sistema Imobiliário no GitHub.

## ❌ Limitações do GitHub para Hospedagem

### GitHub Pages
O **GitHub Pages** é limitado para:
- ✅ Sites estáticos (HTML, CSS, JS)
- ✅ Sites Jekyll/Hugo
- ❌ **NÃO suporta aplicações Django/Python**
- ❌ **NÃO suporta banco de dados**
- ❌ **NÃO suporta processamento server-side**

### GitHub Codespaces
O **GitHub Codespaces** é apenas para:
- ✅ Desenvolvimento
- ✅ Testes
- ❌ **NÃO é para produção**
- ❌ **Limitado em tempo de uso**

## 🔄 Alternativas Recomendadas

### 1. 🚀 **Heroku** (Mais Fácil)

**Vantagens:**
- ✅ Deploy direto do GitHub
- ✅ Suporte nativo ao Django
- ✅ PostgreSQL incluído
- ✅ SSL automático
- ✅ Fácil configuração

**Limitações:**
- ❌ Plano gratuito limitado
- ❌ Dorme após 30min de inatividade (plano gratuito)
- ❌ Custo pode ser alto para tráfego intenso

**Como usar:**
```bash
# 1. Instalar Heroku CLI
# 2. Criar arquivo Procfile
echo "web: gunicorn sistema_imobiliario.wsgi" > Procfile

# 3. Criar runtime.txt
echo "python-3.11.0" > runtime.txt

# 4. Deploy
heroku create seu-sistema-imobiliario
git push heroku main
```

### 2. ☁️ **Railway** (Alternativa ao Heroku)

**Vantagens:**
- ✅ Deploy automático do GitHub
- ✅ PostgreSQL incluído
- ✅ Preços mais baixos que Heroku
- ✅ Não dorme (plano pago)

**Como usar:**
1. Conectar repositório GitHub
2. Railway detecta Django automaticamente
3. Configurar variáveis de ambiente
4. Deploy automático

### 3. 🌊 **DigitalOcean App Platform**

**Vantagens:**
- ✅ Deploy do GitHub
- ✅ Escalabilidade automática
- ✅ Banco de dados gerenciado
- ✅ Preços competitivos

### 4. ⚡ **Vercel** (Para Frontend + API)

**Limitações:**
- ✅ Excelente para frontend
- ⚠️ Limitado para Django (apenas serverless functions)
- ❌ Não ideal para sistema completo

### 5. 🔥 **Firebase/Google Cloud**

**Para sistema completo:**
- ✅ Google Cloud Run (containers)
- ✅ Cloud SQL (PostgreSQL)
- ✅ Deploy do GitHub Actions

## 🎯 **Recomendação Principal: VPS Tradicional**

Para um sistema imobiliário completo, a melhor opção é:

### **VPS (Virtual Private Server)**

**Provedores Recomendados:**
1. **DigitalOcean** - $5-20/mês
2. **Linode** - $5-20/mês
3. **Vultr** - $3.50-20/mês
4. **AWS Lightsail** - $3.50-20/mês
5. **Contabo** - €4-15/mês (mais barato)

**Vantagens:**
- ✅ Controle total
- ✅ Melhor custo-benefício
- ✅ Suporte a todas as tecnologias
- ✅ Escalabilidade
- ✅ Performance superior

## 🔧 Configuração com GitHub + VPS

### 1. Repositório no GitHub
```bash
# Estrutura recomendada
sistema-imobiliario/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── deploy.sh
└── ... (código do projeto)
```

### 2. GitHub Actions para Deploy Automático

Criar `.github/workflows/deploy.yml`:
```yaml
name: Deploy to VPS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/imobiliario
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart gunicorn-imobiliario
          sudo systemctl restart nginx
```

### 3. Configuração de Secrets no GitHub

Em **Settings > Secrets and variables > Actions**:
- `HOST`: IP do seu servidor
- `USERNAME`: usuário SSH
- `SSH_KEY`: chave privada SSH

## 🐳 Opção com Docker

### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "sistema_imobiliario.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 2. docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/imobiliario
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: imobiliario
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web

volumes:
  postgres_data:
```

## 💰 Comparação de Custos (Mensal)

| Provedor | Plano Básico | Plano Médio | Recursos |
|----------|--------------|-------------|----------|
| **Heroku** | $7 | $25 | 512MB-1GB RAM |
| **Railway** | $5 | $20 | 1GB-4GB RAM |
| **DigitalOcean** | $5 | $20 | 1GB-4GB RAM, SSD |
| **Contabo** | €4 | €12 | 4GB-16GB RAM, SSD |
| **AWS Lightsail** | $3.50 | $20 | 512MB-4GB RAM |

## 🎯 Recomendação Final

### Para Desenvolvimento/Teste:
- ✅ **Heroku** ou **Railway** (deploy fácil do GitHub)

### Para Produção Séria:
- ✅ **VPS (DigitalOcean/Contabo)** + GitHub Actions
- ✅ Usar os guias de configuração já criados
- ✅ Deploy automatizado via GitHub

### Configuração Ideal:
1. **Código no GitHub** (versionamento)
2. **VPS para hospedagem** (performance)
3. **GitHub Actions** (deploy automático)
4. **Backup automático** (segurança)

## 🚀 Próximos Passos

1. **Escolher provedor VPS**
2. **Configurar servidor** (usar guias criados)
3. **Configurar GitHub Actions**
4. **Testar deploy automático**
5. **Configurar monitoramento**

## ❓ FAQ

**P: Posso usar GitHub Pages?**
R: Não, GitHub Pages só serve sites estáticos. Django precisa de servidor Python.

**P: E o GitHub Codespaces?**
R: Apenas para desenvolvimento, não para produção.

**P: Qual a opção mais barata?**
R: Contabo VPS (€4/mês) ou AWS Lightsail ($3.50/mês).

**P: Qual a mais fácil?**
R: Heroku ou Railway para começar rapidamente.

**P: Qual a melhor para produção?**
R: VPS (DigitalOcean/Contabo) com configuração completa.

## 📚 Links Úteis

- [DigitalOcean](https://www.digitalocean.com/)
- [Heroku](https://www.heroku.com/)
- [Railway](https://railway.app/)
- [Contabo](https://contabo.com/)
- [GitHub Actions](https://github.com/features/actions)

---

**Conclusão**: GitHub é excelente para armazenar código e automatizar deploy, mas você precisará de um servidor real (VPS) para hospedar o sistema Django completo em produção! 🚀