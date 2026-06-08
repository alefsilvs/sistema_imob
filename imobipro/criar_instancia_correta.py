#!/usr/bin/env python3
import requests
import json
import os
import time
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')

def criar_instancia():
    """Cria uma instância com parâmetros corretos"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/create"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Dados corretos para criar instância
        data = {
            "instanceName": "sistema_imo",
            "integration": "WHATSAPP-BAILEYS"
        }
        
        print("🔄 Criando instância 'sistema_imo'...")
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Instância criada com sucesso!")
            return True
        else:
            print("❌ Falha ao criar instância")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar instância: {e}")
        return False

def conectar_e_gerar_qr():
    """Conecta instância e gera QR Code"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/sistema_imo"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print("🔄 Conectando instância e gerando QR Code...")
        response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'base64' in data:
                print("📱 QR Code gerado com sucesso!")
                print("🔗 Escaneie o QR Code com seu WhatsApp:")
                print("\n" + "="*60)
                
                # Salva o QR Code
                with open('qrcode_sistema_imo.txt', 'w') as f:
                    f.write(data['base64'])
                print("💾 QR Code salvo em 'qrcode_sistema_imo.txt'")
                
                # Mostra preview
                qr_preview = data['base64'][:100] + "..."
                print(f"📄 Preview: {qr_preview}")
                print("="*60)
                print("✅ Agora escaneie o QR Code com seu WhatsApp!")
                
                return True
            else:
                print("❌ QR Code não encontrado na resposta")
                print(f"Resposta completa: {response.text}")
                return False
        else:
            print(f"❌ Erro ao conectar: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def main():
    print("🚀 Criando Instância WhatsApp para Sistema Imobiliário")
    print("="*60)
    
    # Cria a instância
    if criar_instancia():
        print("\n⏳ Aguardando 2 segundos...")
        time.sleep(2)
        
        # Conecta e gera QR Code
        conectar_e_gerar_qr()
    else:
        print("❌ Não foi possível criar a instância")

if __name__ == "__main__":
    main()