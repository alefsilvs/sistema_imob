#!/usr/bin/env bash
# build.sh - Script de build para Render.com

set -o errexit  # exit on error

echo "🚀 Iniciando build para Render.com..."

# Atualizar pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Coletar arquivos estáticos
echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --no-input --settings=sistema_imobiliario.settings_render

# Executar migrações
echo "🗄️ Executando migrações do banco de dados..."
python manage.py migrate --settings=sistema_imobiliario.settings_render

# Criar tabela de cache se necessário
echo "💾 Criando tabela de cache..."
python manage.py createcachetable --settings=sistema_imobiliario.settings_render || echo "Tabela de cache já existe ou não é necessária"

echo "✅ Build concluído com sucesso!"
echo "🌐 Aplicação pronta para deploy no Render.com"