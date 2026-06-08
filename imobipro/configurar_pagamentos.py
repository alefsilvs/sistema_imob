#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Configuração Rápida de Pagamentos

Este script ajuda a configurar pagamentos reais no sistema.
Execute: python configurar_pagamentos.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
    django.setup()

from pagamentos.models import ConfiguracaoPagamento
from pagamentos.utils import validar_configuracao_pagamento


def configurar_mercadopago():
    """
    Configura o Mercado Pago como gateway de pagamento
    """
    print("\n=== CONFIGURAÇÃO MERCADO PAGO ===")
    print("\n1. Acesse: https://www.mercadopago.com.br/developers/panel/credentials")
    print("2. Copie seu Access Token (sandbox para testes, produção para uso real)")
    print("3. Cole abaixo:")
    
    access_token = input("\nAccess Token: ").strip()
    
    if not access_token:
        print("❌ Access Token é obrigatório!")
        return False
    
    # Detectar se é sandbox ou produção
    is_sandbox = 'TEST-' in access_token
    ambiente = "SANDBOX (Testes)" if is_sandbox else "PRODUÇÃO"
    
    print(f"\n🔍 Detectado ambiente: {ambiente}")
    
    if not is_sandbox:
        confirm = input("\n⚠️  ATENÇÃO: Você está configurando PRODUÇÃO. Confirma? (s/N): ")
        if confirm.lower() != 's':
            print("Configuração cancelada.")
            return False
    
    # Configurar PIX
    print("\n--- Configuração PIX ---")
    pix_chave = input("Chave PIX (CPF, CNPJ, email ou telefone): ").strip()
    pix_nome = input("Nome do recebedor PIX: ").strip()
    
    # Obter configuração
    config = ConfiguracaoPagamento.get_configuracao()
    
    # Atualizar configurações
    config.pix_habilitado = True
    config.cartao_habilitado = True
    config.boleto_habilitado = False  # Mercado Pago não tem boleto direto
    
    config.gateway_api_key = access_token
    config.gateway_endpoint = "https://api.mercadopago.com"
    
    if pix_chave:
        config.pix_chave = pix_chave
    if pix_nome:
        config.pix_nome_recebedor = pix_nome
    
    # URLs de retorno (ajuste conforme seu domínio)
    base_url = input("\nURL base do seu site (ex: https://meusite.com): ").strip()
    if base_url:
        config.url_sucesso = f"{base_url}/pagamentos/sucesso/"
        config.url_erro = f"{base_url}/pagamentos/erro/"
        config.url_cancelamento = f"{base_url}/pagamentos/cancelado/"
    
    config.save()
    
    print("\n✅ Configuração salva com sucesso!")
    
    # Testar conexão
    print("\n🔄 Testando conexão...")
    try:
        import mercadopago
        sdk = mercadopago.SDK(access_token)
        
        # Testar API
        payment_methods = sdk.payment_methods().list_all()
        
        if payment_methods['status'] == 200:
            print("✅ Conexão com Mercado Pago OK!")
            print(f"📊 {len(payment_methods['response'])} métodos de pagamento disponíveis")
            
            # Mostrar alguns métodos
            credit_cards = [m for m in payment_methods['response'] if m.get('payment_type_id') == 'credit_card']
            print(f"💳 {len(credit_cards)} cartões de crédito suportados")
            
            return True
        else:
            print("❌ Erro na conexão com Mercado Pago")
            print(f"Status: {payment_methods['status']}")
            return False
            
    except ImportError:
        print("⚠️  SDK do Mercado Pago não instalado")
        print("Execute: pip install mercadopago")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar: {str(e)}")
        return False


def configurar_asaas():
    """
    Configura o Asaas como gateway de pagamento
    """
    print("\n=== CONFIGURAÇÃO ASAAS ===")
    print("\n1. Acesse: https://www.asaas.com/api/v3/")
    print("2. Gere sua API Key")
    print("3. Cole abaixo:")
    
    api_key = input("\nAPI Key: ").strip()
    
    if not api_key:
        print("❌ API Key é obrigatória!")
        return False
    
    # Detectar ambiente
    is_sandbox = api_key.startswith('$aact_YTU5YTE0M2M2N2I4MTliNzk0YTI5N2U5MzdjNWZmNDQ6OjAwMDAwMDAwMDAwMDAwNzI1Mjk6OiRhYWRkOmY3YjJhMjljLTI0YjItNGY4Yy1iNzI4LWI4NzZkNDVkNGY4Nw==')
    ambiente = "SANDBOX (Testes)" if is_sandbox else "PRODUÇÃO"
    
    print(f"\n🔍 Ambiente: {ambiente}")
    
    # Configurar PIX
    print("\n--- Configuração PIX ---")
    pix_chave = input("Chave PIX: ").strip()
    pix_nome = input("Nome do recebedor: ").strip()
    
    # Obter configuração
    config = ConfiguracaoPagamento.get_configuracao()
    
    # Atualizar configurações
    config.pix_habilitado = True
    config.cartao_habilitado = True
    config.boleto_habilitado = True
    
    config.gateway_api_key = api_key
    config.gateway_endpoint = "https://www.asaas.com/api/v3" if not is_sandbox else "https://sandbox.asaas.com/api/v3"
    
    if pix_chave:
        config.pix_chave = pix_chave
    if pix_nome:
        config.pix_nome_recebedor = pix_nome
    
    config.save()
    
    print("\n✅ Configuração Asaas salva!")
    
    # Testar conexão
    print("\n🔄 Testando conexão...")
    try:
        import requests
        
        headers = {
            'access_token': api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{config.gateway_endpoint}/myAccount",
            headers=headers
        )
        
        if response.status_code == 200:
            account = response.json()
            print("✅ Conexão com Asaas OK!")
            print(f"📊 Conta: {account.get('name', 'N/A')}")
            return True
        else:
            print(f"❌ Erro na conexão: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar: {str(e)}")
        return False


def verificar_configuracao():
    """
    Verifica se a configuração está correta
    """
    print("\n=== VERIFICAÇÃO DA CONFIGURAÇÃO ===")
    
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        validacao = validar_configuracao_pagamento()
        
        print(f"\n📊 Status: {'✅ VÁLIDA' if validacao['valido'] else '❌ INVÁLIDA'}")
        
        print("\n--- Métodos Habilitados ---")
        print(f"PIX: {'✅' if config.pix_habilitado else '❌'}")
        print(f"Cartão: {'✅' if config.cartao_habilitado else '❌'}")
        print(f"Boleto: {'✅' if config.boleto_habilitado else '❌'}")
        
        if validacao['erros']:
            print("\n❌ ERROS:")
            for erro in validacao['erros']:
                print(f"  • {erro}")
        
        if validacao['avisos']:
            print("\n⚠️  AVISOS:")
            for aviso in validacao['avisos']:
                print(f"  • {aviso}")
        
        if validacao['valido']:
            print("\n🎉 Configuração está pronta para uso!")
            
            # Mostrar próximos passos
            print("\n--- PRÓXIMOS PASSOS ---")
            print("1. ✅ Configuração completa")
            print("2. 🔄 Teste os pagamentos em ambiente sandbox")
            print("3. 🌐 Configure webhooks para confirmação automática")
            print("4. 🚀 Mude para produção quando estiver pronto")
            
            # Mostrar URLs importantes
            print("\n--- URLs IMPORTANTES ---")
            print(f"Página de pagamento: /pagamentos/pagar/<token>/")
            print(f"Webhook (configure no gateway): /pagamentos/webhook/mercadopago/")
            print(f"Admin: /admin/pagamentos/configuracaopagamento/")
        
        return validacao['valido']
        
    except Exception as e:
        print(f"❌ Erro ao verificar: {str(e)}")
        return False


def instalar_dependencias():
    """
    Instala dependências necessárias
    """
    print("\n=== INSTALAÇÃO DE DEPENDÊNCIAS ===")
    
    dependencias = {
        'mercadopago': 'Mercado Pago SDK',
        'requests': 'HTTP requests (para Asaas)',
        'qrcode': 'Geração de QR codes',
        'pillow': 'Processamento de imagens'
    }
    
    for pacote, descricao in dependencias.items():
        try:
            __import__(pacote)
            print(f"✅ {pacote} - {descricao}")
        except ImportError:
            print(f"❌ {pacote} - {descricao} (não instalado)")
            
            install = input(f"Instalar {pacote}? (s/N): ")
            if install.lower() == 's':
                os.system(f"pip install {pacote}")


def menu_principal():
    """
    Menu principal do configurador
    """
    while True:
        print("\n" + "="*50)
        print("🏠 CONFIGURADOR DE PAGAMENTOS - SISTEMA IMOBILIÁRIO")
        print("="*50)
        
        print("\n1. 🔧 Instalar dependências")
        print("2. 💳 Configurar Mercado Pago (Recomendado)")
        print("3. 🏦 Configurar Asaas")
        print("4. ✅ Verificar configuração atual")
        print("5. 📖 Ver guia completo")
        print("6. 🚪 Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == '1':
            instalar_dependencias()
        elif opcao == '2':
            configurar_mercadopago()
        elif opcao == '3':
            configurar_asaas()
        elif opcao == '4':
            verificar_configuracao()
        elif opcao == '5':
            print("\n📖 Consulte o arquivo: GUIA_IMPLEMENTACAO_PAGAMENTOS_REAIS.md")
            print("📝 Exemplo prático: exemplo_mercadopago.py")
        elif opcao == '6':
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")


def verificar_ambiente():
    """
    Verifica se o ambiente Django está configurado
    """
    try:
        from django.conf import settings
        print(f"✅ Django configurado: {settings.DEBUG and 'DEBUG' or 'PRODUÇÃO'}")
        return True
    except Exception as e:
        print(f"❌ Erro no Django: {str(e)}")
        print("\n🔧 Execute este script no diretório do projeto Django")
        print("📁 Certifique-se de que manage.py está no mesmo diretório")
        return False


if __name__ == '__main__':
    print("🚀 Iniciando configurador de pagamentos...")
    
    if verificar_ambiente():
        menu_principal()
    else:
        print("\n❌ Não foi possível inicializar o Django")
        sys.exit(1)