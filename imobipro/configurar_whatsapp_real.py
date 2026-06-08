#!/usr/bin/env python
"""
Script para configurar WhatsApp real com Evolution API
"""

import requests
import json
import qrcode
import io
import base64
from PIL import Image
import time

# Configurações
EVOLUTION_URL = "http://localhost:8080"
API_KEY = "sistema_imo_2024_secure_key_789"
INSTANCE_NAME = "sistema_imo_producao"
SEU_NUMERO = "5561983036586"  # Seu número

def criar_instancia():
    """Cria uma nova instância do WhatsApp"""
    print("🔧 Criando instância do WhatsApp...")
    
    url = f"{EVOLUTION_URL}/instance/create"
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    data = {
        "instanceName": INSTANCE_NAME,
        "token": API_KEY,
        "qrcode": True,
        "number": SEU_NUMERO,
        "webhook": {
            "url": "",
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "CONNECTION_UPDATE"
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print("✅ Instância criada com sucesso!")
            return response.json()
        else:
            print(f"❌ Erro ao criar instância: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def conectar_whatsapp():
    """Conecta o WhatsApp e mostra o QR Code"""
    print("📱 Conectando WhatsApp...")
    
    url = f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}"
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            if 'qrcode' in data:
                print("\n📱 QR CODE PARA CONECTAR SEU WHATSAPP:")
                print("="*50)
                
                # Decodificar e mostrar QR Code
                qr_data = data['qrcode']['code']
                
                # Criar QR Code
                qr = qrcode.QRCode(version=1, box_size=2, border=1)
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Mostrar no terminal
                qr.print_ascii()
                
                print("\n📋 INSTRUÇÕES:")
                print("1. Abra o WhatsApp no seu celular")
                print("2. Vá em Configurações > Aparelhos conectados")
                print("3. Toque em 'Conectar um aparelho'")
                print("4. Escaneie o QR Code acima")
                print("\n⏳ Aguardando conexão...")
                
                return True
            else:
                print("❌ QR Code não disponível")
                return False
        else:
            print(f"❌ Erro ao conectar: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def verificar_status():
    """Verifica o status da conexão"""
    url = f"{EVOLUTION_URL}/instance/connectionState/{INSTANCE_NAME}"
    headers = {"apikey": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data.get('instance', {}).get('state', 'unknown')
            print(f"📊 Status da conexão: {status}")
            return status == 'open'
        else:
            print(f"❌ Erro ao verificar status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def enviar_mensagem_teste():
    """Envia uma mensagem de teste para seu número"""
    print(f"📤 Enviando mensagem de teste para {SEU_NUMERO}...")
    
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "Content-Type": "application/json",
        "apikey": API_KEY
    }
    
    data = {
        "number": SEU_NUMERO,
        "text": "🎉 SUCESSO! Seu Sistema Imobiliário está conectado ao WhatsApp!\n\n✅ As notificações agora serão enviadas para números reais.\n\n🤖 Mensagem de teste enviada automaticamente."
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print("✅ Mensagem de teste enviada com sucesso!")
            print("📱 Verifique seu WhatsApp!")
            return True
        else:
            print(f"❌ Erro ao enviar mensagem: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🚀 CONFIGURAÇÃO DO WHATSAPP REAL")
    print("="*40)
    print(f"📱 Seu número: {SEU_NUMERO}")
    print(f"🔗 Evolution API: {EVOLUTION_URL}")
    print(f"🏷️  Instância: {INSTANCE_NAME}")
    print()
    
    # Passo 1: Criar instância
    resultado = criar_instancia()
    if not resultado:
        print("❌ Falha ao criar instância. Verifique se a Evolution API está rodando.")
        return
    
    time.sleep(2)
    
    # Passo 2: Conectar WhatsApp
    if conectar_whatsapp():
        print("\n⏳ Aguardando você escanear o QR Code...")
        
        # Aguardar conexão (máximo 2 minutos)
        for i in range(24):  # 24 x 5s = 2 minutos
            time.sleep(5)
            if verificar_status():
                print("\n🎉 WhatsApp conectado com sucesso!")
                
                # Enviar mensagem de teste
                time.sleep(3)
                enviar_mensagem_teste()
                
                print("\n✅ CONFIGURAÇÃO CONCLUÍDA!")
                print("\n💡 PRÓXIMOS PASSOS:")
                print("1. Seu WhatsApp está conectado")
                print("2. O sistema está em modo PRODUÇÃO")
                print("3. As notificações serão enviadas para números reais")
                print("4. Teste enviando uma notificação pelo sistema")
                return
            
            print(f"⏳ Aguardando conexão... ({i+1}/24)")
        
        print("\n⏰ Tempo limite atingido. Tente novamente.")
    else:
        print("❌ Falha ao iniciar conexão")

if __name__ == '__main__':
    main()