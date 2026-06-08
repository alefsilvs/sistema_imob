#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
INSTANCE_NAME = "sistema_imo"

def conectar_sistema_imo():
    """Conecta especificamente a instância sistema_imo usando endpoint correto"""
    try:
        # Endpoint correto baseado na documentação
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"📱 Conectando instância '{INSTANCE_NAME}'...")
        print(f"🔗 URL: {url}")
        
        # Usa GET conforme documentação
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta completa: {json.dumps(data, indent=2)}")
            
            # Verifica diferentes estruturas de resposta
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
            elif 'qrcode' in data:
                qr_data = data['qrcode']
                if 'base64' in qr_data:
                    print("✅ QR Code gerado com sucesso!")
                    
                    # Salva o QR Code
                    filename = f'qrcode_{INSTANCE_NAME}.txt'
                    with open(filename, 'w') as f:
                        f.write(qr_data['base64'])
                    
                    print(f"💾 QR Code salvo em '{filename}'")
                    print("\n" + "="*60)
                    print("📱 ESCANEIE O QR CODE COM SEU WHATSAPP AGORA!")
                    print("="*60)
                    print(f"📄 Arquivo: {filename}")
                    print(f"📋 Instância: {INSTANCE_NAME}")
                    print("="*60)
                    
                    return True
            elif 'instance' in data:
                instance_data = data.get('instance', {})
                status = instance_data.get('status', 'unknown')
                
                if status == 'open':
                    print("✅ WhatsApp já está conectado!")
                    print(f"📱 Status: {status}")
                    return True
                else:
                    print(f"⚠️ Status atual: {status}")
                    return False
            else:
                print(f"⚠️ Resposta inesperada, mas vou tentar gerar QR Code...")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_status():
    """Verifica o status da instância sistema_imo"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connectionState/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔍 Verificando status da instância '{INSTANCE_NAME}'...")
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📱 Status: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def deletar_instancia():
    """Deleta a instância se existir"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/delete/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🗑️ Deletando instância '{INSTANCE_NAME}' se existir...")
        response = requests.delete(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Instância deletada com sucesso!")
            return True
        else:
            print(f"⚠️ Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def criar_instancia():
    """Cria uma nova instância"""
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
        
        print(f"🆕 Criando instância '{INSTANCE_NAME}'...")
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 201 or response.status_code == 200:
            print("✅ Instância criada com sucesso!")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🚀 Conectar WhatsApp - Sistema Imobiliário")
    print("="*60)
    print(f"📋 Instância: {INSTANCE_NAME}")
    print(f"🔗 API URL: {EVOLUTION_API_URL}")
    print("="*60)
    
    # 1. Verifica status atual
    print("Passo 1: Verificando status...")
    status = verificar_status()
    
    print("\n" + "="*60)
    
    # 2. Se não conseguir verificar status, recria a instância
    if not status:
        print("Passo 2: Recriando instância...")
        deletar_instancia()
        if not criar_instancia():
            print("❌ Falha ao criar instância")
            return
        print("\n" + "="*60)
    
    # 3. Tenta conectar
    print("Passo 3: Conectando...")
    if conectar_sistema_imo():
        print(f"\n🎉 SUCESSO! Instância '{INSTANCE_NAME}' conectada!")
        
        # Salva confirmação
        with open('instancia_ativa.txt', 'w') as f:
            f.write(INSTANCE_NAME)
        print(f"💾 Instância ativa salva em 'instancia_ativa.txt'")
    else:
        print(f"\n❌ Falha ao conectar instância '{INSTANCE_NAME}'")
        print("💡 Tente acessar o manager: http://localhost:8081/manager")

if __name__ == "__main__":
    main()