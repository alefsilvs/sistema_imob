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
INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'sistema_imo')

def deletar_instancia_se_existir():
    """Deleta a instância se ela existir (para garantir limpeza)"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/delete/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🧹 Verificando se '{INSTANCE_NAME}' existe para limpeza...")
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Instância '{INSTANCE_NAME}' deletada")
        elif response.status_code == 404:
            print(f"✅ Instância '{INSTANCE_NAME}' não existia")
        else:
            print(f"⚠️ Status: {response.status_code} - {response.text}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Erro na limpeza: {e}")
        return True  # Continua mesmo com erro

def criar_instancia():
    """Cria a instância específica do .env"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/create"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Dados mínimos para criação
        data = {
            "instanceName": INSTANCE_NAME,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        print(f"🔧 Criando instância '{INSTANCE_NAME}'...")
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Instância criada com sucesso!")
            print(f"📱 ID: {result.get('instance', {}).get('instanceId', 'N/A')}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            
            # Se o erro for de nome em uso, tenta deletar e criar novamente
            if "already in use" in response.text:
                print("🔄 Nome em uso, tentando forçar limpeza...")
                time.sleep(2)
                deletar_instancia_se_existir()
                time.sleep(3)
                
                # Tenta criar novamente
                print(f"🔧 Tentando criar '{INSTANCE_NAME}' novamente...")
                response2 = requests.post(url, headers=headers, json=data)
                
                if response2.status_code == 201:
                    print("✅ Instância criada após limpeza!")
                    return True
                else:
                    print(f"❌ Falha mesmo após limpeza: {response2.text}")
                    return False
            
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def conectar_instancia():
    """Conecta a instância e gera QR Code"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"📱 Conectando instância '{INSTANCE_NAME}'...")
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'base64' in data:
                print("✅ QR Code gerado com sucesso!")
                
                # Salva o QR Code
                filename = f'qrcode_{INSTANCE_NAME}.txt'
                with open(filename, 'w') as f:
                    f.write(data['base64'])
                
                print(f"💾 QR Code salvo em '{filename}'")
                print("\n" + "="*60)
                print("📱 ESCANEIE O QR CODE COM SEU WHATSAPP AGORA!")
                print("="*60)
                print(f"📄 Arquivo: {filename}")
                print(f"📋 Instância: {INSTANCE_NAME}")
                print("="*60)
                
                return True
            else:
                print(f"⚠️ Resposta: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🚀 Criar e Conectar Instância do .env")
    print("="*60)
    print(f"📋 Instância: {INSTANCE_NAME}")
    print(f"🔗 API URL: {EVOLUTION_API_URL}")
    print("="*60)
    
    # 1. Limpeza preventiva
    deletar_instancia_se_existir()
    
    print("\n⏳ Aguardando 3 segundos...")
    time.sleep(3)
    
    # 2. Cria a instância
    print("\n" + "="*60)
    if criar_instancia():
        print("✅ Instância criada!")
        
        # 3. Aguarda um pouco
        print("⏳ Aguardando 5 segundos para estabilizar...")
        time.sleep(5)
        
        # 4. Conecta e gera QR Code
        print("\n" + "="*60)
        if conectar_instancia():
            print(f"\n🎉 SUCESSO! Instância '{INSTANCE_NAME}' criada e conectada!")
            print("📱 Agora escaneie o QR Code com seu WhatsApp")
            
            # Salva confirmação
            with open('instancia_ativa.txt', 'w') as f:
                f.write(INSTANCE_NAME)
            print(f"💾 Instância ativa salva em 'instancia_ativa.txt'")
        else:
            print(f"\n❌ Falha ao conectar instância '{INSTANCE_NAME}'")
    else:
        print("❌ Falha ao criar instância")

if __name__ == "__main__":
    main()