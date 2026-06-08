#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
INSTANCE_NAME = "sistema_imobiliario"

def verificar_status_instancia():
    """Verifica o status da instância"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            instances = response.json()
            print(f"✅ Instâncias encontradas: {len(instances)}")
            
            for instance in instances:
                if instance.get('instance', {}).get('instanceName') == INSTANCE_NAME:
                    status = instance.get('instance', {}).get('status', 'unknown')
                    print(f"📱 Instância '{INSTANCE_NAME}': {status}")
                    return status
            
            print(f"❌ Instância '{INSTANCE_NAME}' não encontrada")
            return None
        else:
            print(f"❌ Erro ao buscar instâncias: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def gerar_qrcode():
    """Gera QR Code para conectar WhatsApp"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'base64' in data:
                print("📱 QR Code gerado com sucesso!")
                print("🔗 Escaneie o QR Code abaixo com seu WhatsApp:")
                print("\n" + "="*50)
                print(f"QR Code Base64: {data['base64'][:100]}...")
                print("="*50)
                
                # Salva o QR Code em arquivo
                with open('qrcode_whatsapp.txt', 'w') as f:
                    f.write(data['base64'])
                print("💾 QR Code salvo em 'qrcode_whatsapp.txt'")
                
                return True
            else:
                print("❌ QR Code não encontrado na resposta")
                return False
        else:
            print(f"❌ Erro ao gerar QR Code: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao gerar QR Code: {e}")
        return False

def main():
    print("🔍 Verificando status da instância WhatsApp...")
    
    status = verificar_status_instancia()
    
    if status == 'open':
        print("✅ WhatsApp já está conectado!")
    elif status in ['close', 'connecting']:
        print(f"📱 Status atual: {status}")
        print("🔄 Gerando QR Code para conexão...")
        gerar_qrcode()
    elif status is None:
        print("❌ Instância não encontrada. Criando nova instância...")
        # Aqui você pode adicionar código para criar uma nova instância
    else:
        print(f"⚠️ Status desconhecido: {status}")
        print("🔄 Tentando gerar QR Code...")
        gerar_qrcode()

if __name__ == "__main__":
    main()