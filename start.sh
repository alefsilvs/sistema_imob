#!/bin/bash

# Script de inicialização para Railway/Railpack
# Projeto Django - Sistema Imobiliário

echo "🚀 Iniciando Sistema Imobiliário Django..."

# Instalar dependências
echo "📦 Instalando dependências..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Iniciar servidor Gunicorn
echo "🌐 Iniciando servidor..."
exec gunicorn sistema_imobiliario.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
