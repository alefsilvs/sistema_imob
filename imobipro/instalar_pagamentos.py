#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador Automático de Dependências para Pagamentos

Este script instala todas as dependências necessárias para pagamentos reais
Execute: python instalar_pagamentos.py
"""

import subprocess
import sys
import os
from pathlib import Path


def executar_comando(comando, descricao=""):
    """
    Executa um comando e mostra o resultado
    """
    print(f"\n🔄 {descricao}...")
    print(f"💻 Executando: {comando}")
    
    try:
        result = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ {descricao} - Sucesso!")
        if result.stdout:
            print(f"📄 Output: {result.stdout.strip()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {descricao} - Erro!")
        print(f"🚨 Código de erro: {e.returncode}")
        if e.stdout:
            print(f"📄 Output: {e.stdout.strip()}")
        if e.stderr:
            print(f"🔴 Erro: {e.stderr.strip()}")
        
        return False


def verificar_python():
    """
    Verifica se o Python está instalado e a versão
    """
    print("\n=== VERIFICAÇÃO DO PYTHON ===")
    
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é requerido!")
        return False
    
    print("✅ Versão do Python OK")
    return True


def verificar_pip():
    """
    Verifica se o pip está instalado
    """
    print("\n=== VERIFICAÇÃO DO PIP ===")
    
    try:
        import pip
        print(f"📦 pip {pip.__version__}")
        print("✅ pip instalado")
        return True
    except ImportError:
        print("❌ pip não encontrado!")
        return False


def instalar_dependencias_basicas():
    """
    Instala dependências básicas
    """
    print("\n=== INSTALAÇÃO DE DEPENDÊNCIAS BÁSICAS ===")
    
    dependencias = [
        ("requests", "Biblioteca para requisições HTTP"),
        ("pillow", "Processamento de imagens"),
        ("qrcode[pil]", "Geração de QR codes"),
        ("python-decouple", "Gerenciamento de configurações"),
    ]
    
    sucesso = True
    
    for pacote, descricao in dependencias:
        if not executar_comando(
            f"pip install {pacote}",
            f"Instalando {pacote} - {descricao}"
        ):
            sucesso = False
    
    return sucesso


def instalar_mercadopago():
    """
    Instala SDK do Mercado Pago
    """
    print("\n=== INSTALAÇÃO MERCADO PAGO ===")
    
    return executar_comando(
        "pip install mercadopago",
        "Instalando SDK do Mercado Pago"
    )


def instalar_asaas():
    """
    Instala dependências para Asaas
    """
    print("\n=== CONFIGURAÇÃO ASAAS ===")
    
    # Asaas usa requests, que já foi instalado
    print("✅ Asaas usa requests (já instalado)")
    return True


def criar_requirements():
    """
    Cria arquivo requirements.txt com as dependências
    """
    print("\n=== CRIANDO REQUIREMENTS.TXT ===")
    
    requirements_content = """# Dependências para Pagamentos Reais
# Sistema Imobiliário

# Gateways de Pagamento
mercadopago>=2.2.0
requests>=2.28.0

# Geração de QR Codes e Imagens
qrcode[pil]>=7.4.0
Pillow>=9.0.0

# Configurações
python-decouple>=3.6

# Django (se não estiver no requirements principal)
Django>=4.0.0
django-cors-headers>=3.13.0

# Banco de dados (opcional)
psycopg2-binary>=2.9.0  # PostgreSQL
# mysqlclient>=2.1.0     # MySQL

# Produção (opcional)
gunicorn>=20.1.0
whitenoise>=6.2.0
"""
    
    try:
        with open("requirements_pagamentos.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        print("✅ Arquivo requirements_pagamentos.txt criado")
        print("📄 Para instalar: pip install -r requirements_pagamentos.txt")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar requirements: {str(e)}")
        return False


def verificar_instalacao():
    """
    Verifica se todas as dependências foram instaladas corretamente
    """
    print("\n=== VERIFICAÇÃO DA INSTALAÇÃO ===")
    
    dependencias = {
        'requests': 'Requisições HTTP',
        'PIL': 'Processamento de imagens (Pillow)',
        'qrcode': 'Geração de QR codes',
        'mercadopago': 'SDK Mercado Pago',
        'decouple': 'Configurações'
    }
    
    sucesso = True
    
    for modulo, descricao in dependencias.items():
        try:
            if modulo == 'PIL':
                from PIL import Image
            else:
                __import__(modulo)
            
            print(f"✅ {modulo} - {descricao}")
            
        except ImportError:
            print(f"❌ {modulo} - {descricao} (não instalado)")
            sucesso = False
    
    return sucesso


def configurar_django():
    """
    Verifica e configura o Django para pagamentos
    """
    print("\n=== CONFIGURAÇÃO DJANGO ===")
    
    # Verificar se estamos em um projeto Django
    if not os.path.exists("manage.py"):
        print("❌ manage.py não encontrado!")
        print("🔧 Execute este script no diretório raiz do projeto Django")
        return False
    
    print("✅ Projeto Django detectado")
    
    # Verificar se o app pagamentos existe
    if os.path.exists("pagamentos"):
        print("✅ App 'pagamentos' encontrado")
    else:
        print("⚠️  App 'pagamentos' não encontrado")
        print("🔧 Certifique-se de que o app pagamentos está criado")
    
    return True


def mostrar_proximos_passos():
    """
    Mostra os próximos passos após a instalação
    """
    print("\n" + "="*60)
    print("🎉 INSTALAÇÃO CONCLUÍDA!")
    print("="*60)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1. 🔧 CONFIGURAR GATEWAY:")
    print("   python configurar_pagamentos.py")
    
    print("\n2. 📝 AJUSTAR CONFIGURAÇÕES:")
    print("   - Copie config_pagamentos_exemplo.py para config_pagamentos.py")
    print("   - Ajuste suas credenciais de API")
    
    print("\n3. 🧪 TESTAR PAGAMENTOS:")
    print("   - Use ambiente sandbox primeiro")
    print("   - Teste PIX, cartão e boleto")
    
    print("\n4. 🌐 CONFIGURAR WEBHOOKS:")
    print("   - Configure URLs de notificação no gateway")
    print("   - Teste confirmação automática")
    
    print("\n5. 🚀 PRODUÇÃO:")
    print("   - Mude para credenciais de produção")
    print("   - Configure domínio real")
    
    print("\n📚 DOCUMENTAÇÃO:")
    print("   - GUIA_IMPLEMENTACAO_PAGAMENTOS_REAIS.md")
    print("   - exemplo_mercadopago.py")
    
    print("\n🆘 SUPORTE:")
    print("   - Mercado Pago: https://www.mercadopago.com.br/developers/")
    print("   - Asaas: https://docs.asaas.com/")


def main():
    """
    Função principal do instalador
    """
    print("🚀 INSTALADOR DE PAGAMENTOS - SISTEMA IMOBILIÁRIO")
    print("="*60)
    
    # Verificações básicas
    if not verificar_python():
        sys.exit(1)
    
    if not verificar_pip():
        sys.exit(1)
    
    if not configurar_django():
        sys.exit(1)
    
    # Instalações
    print("\n🔄 Iniciando instalação das dependências...")
    
    sucesso = True
    
    if not instalar_dependencias_basicas():
        sucesso = False
    
    if not instalar_mercadopago():
        print("⚠️  Falha ao instalar Mercado Pago (opcional)")
    
    if not instalar_asaas():
        print("⚠️  Falha ao configurar Asaas (opcional)")
    
    # Criar requirements
    criar_requirements()
    
    # Verificação final
    if verificar_instalacao():
        print("\n✅ Todas as dependências instaladas com sucesso!")
        mostrar_proximos_passos()
    else:
        print("\n❌ Algumas dependências falharam")
        print("🔧 Tente instalar manualmente:")
        print("   pip install -r requirements_pagamentos.txt")
        sucesso = False
    
    return sucesso


if __name__ == '__main__':
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Instalação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro inesperado: {str(e)}")
        sys.exit(1)