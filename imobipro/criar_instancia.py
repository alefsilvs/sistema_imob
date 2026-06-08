#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
import time

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
INSTANCE_NAME = "sistema_imobiliario"

def criar_instancia():
    """Cria uma nova instância do WhatsApp"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/create"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "instanceName": INSTANCE_NAME,
            "token": EVOLUTION_API_KEY,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        print(f"🔄 Criando instância '{INSTANCE_NAME}'...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Instância criada com sucesso!")
            print(f"📱 Nome: {result.get('instance', {}).get('instanceName')}")
            return True
        else:
            print(f"❌ Erro ao criar instância: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar instância: {e}")
        return False

def conectar_instancia():
    """Conecta a instância e gera QR Code"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔄 Conectando instância '{INSTANCE_NAME}'...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'base64' in data:
                print("📱 QR Code gerado com sucesso!")
                print("🔗 Escaneie o QR Code abaixo com seu WhatsApp:")
                print("\n" + "="*50)
                
                # Salva o QR Code em arquivo
                with open('qrcode_whatsapp.txt', 'w') as f:
                    f.write(data['base64'])
                print("💾 QR Code salvo em 'qrcode_whatsapp.txt'")
                
                # Mostra uma parte do QR Code para verificação
                qr_preview = data['base64'][:100] + "..."
                print(f"📄 Preview: {qr_preview}")
                print("="*50)
                
                return True
            else:
                print("❌ QR Code não encontrado na resposta")
                print(f"Resposta: {response.text}")
                return False
        else:
            print(f"❌ Erro ao conectar instância: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar instância: {e}")
        return False

def main():
    print("🚀 Configurando WhatsApp para o Sistema Imobiliário")
    print("="*50)
    
    # Primeiro, tenta criar a instância
    if criar_instancia():
        print("\n⏳ Aguardando 3 segundos...")
        time.sleep(3)
        
        # Depois, conecta e gera o QR Code
        if conectar_instancia():
            print("\n✅ Configuração concluída!")
            print("📱 Agora escaneie o QR Code com seu WhatsApp")
            print("📁 O QR Code foi salvo no arquivo 'qrcode_whatsapp.txt'")
        else:
            print("\n❌ Falha ao gerar QR Code")
    else:
        print("\n❌ Falha ao criar instância")

if __name__ == "__main__":
    main()