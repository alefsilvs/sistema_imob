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
INSTANCE_NAME = "sistema_imo"

def conectar_via_manager():
    """Conecta usando os mesmos endpoints que o manager web usa"""
    try:
        # Primeiro, vamos tentar o endpoint que o manager usa
        url = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        print(f"📱 Conectando instância '{INSTANCE_NAME}' via manager...")
        print(f"🔗 URL: {url}")
        
        # Tenta POST primeiro (como o manager faz)
        response = requests.post(url, headers=headers, json={})
        
        print(f"Status HTTP: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Dados recebidos: {json.dumps(data, indent=2)}")
                
                # Verifica se há QR code na resposta
                if 'qrcode' in data and data['qrcode']:
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
                
                # Se não tem QR code, verifica se já está conectado
                if 'instance' in data:
                    instance_info = data['instance']
                    if instance_info.get('status') == 'open':
                        print("✅ WhatsApp já está conectado!")
                        return True
                
                return False
                
            except json.JSONDecodeError:
                print("⚠️ Resposta não é JSON válido")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def obter_qr_code_direto():
    """Tenta obter QR code usando endpoint direto"""
    try:
        # Endpoint alternativo para QR code
        url = f"{EVOLUTION_API_URL}/instance/{INSTANCE_NAME}/qrcode"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔄 Obtendo QR Code diretamente...")
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Resposta QR: {json.dumps(data, indent=2)}")
            
            if 'base64' in data:
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
                print("⚠️ QR Code não encontrado na resposta")
                return False
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def restart_instancia():
    """Reinicia a instância"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/restart/{INSTANCE_NAME}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔄 Reiniciando instância '{INSTANCE_NAME}'...")
        response = requests.put(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Instância reiniciada com sucesso!")
            time.sleep(3)  # Aguarda um pouco
            return True
        else:
            print(f"⚠️ Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verificar_status_detalhado():
    """Verifica status detalhado da instância"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔍 Verificando status detalhado...")
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Procura nossa instância
            for instance in data:
                if instance.get('name') == INSTANCE_NAME:
                    print(f"📱 Instância encontrada:")
                    print(f"   Nome: {instance.get('name')}")
                    print(f"   Status: {instance.get('connectionStatus')}")
                    print(f"   ID: {instance.get('id')}")
                    return instance
            
            print(f"⚠️ Instância '{INSTANCE_NAME}' não encontrada")
            return None
        else:
            print(f"❌ Erro: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def main():
    print("🚀 Conectar WhatsApp - Via Manager")
    print("="*60)
    print(f"📋 Instância: {INSTANCE_NAME}")
    print(f"🔗 API URL: {EVOLUTION_API_URL}")
    print("="*60)
    
    # 1. Verifica status detalhado
    print("Passo 1: Verificando status detalhado...")
    instance_info = verificar_status_detalhado()
    
    if instance_info:
        status = instance_info.get('connectionStatus', 'unknown')
        print(f"📱 Status atual: {status}")
        
        if status == 'close':
            print("\n" + "="*60)
            print("Passo 2: Reiniciando instância...")
            restart_instancia()
            
            print("\n" + "="*60)
            print("Passo 3: Conectando via manager...")
            if conectar_via_manager():
                print(f"\n🎉 SUCESSO! Instância '{INSTANCE_NAME}' conectada!")
            else:
                print("\nPasso 4: Tentando obter QR Code diretamente...")
                if obter_qr_code_direto():
                    print(f"\n🎉 SUCESSO! QR Code gerado para '{INSTANCE_NAME}'!")
                else:
                    print(f"\n❌ Falha ao conectar '{INSTANCE_NAME}'")
                    print("💡 Tente usar o manager web: http://localhost:8081/manager")
        elif status == 'open':
            print("✅ WhatsApp já está conectado!")
        else:
            print(f"⚠️ Status desconhecido: {status}")
    else:
        print("❌ Não foi possível verificar o status da instância")
    
    # Salva confirmação
    with open('instancia_ativa.txt', 'w') as f:
        f.write(INSTANCE_NAME)
    print(f"💾 Instância ativa salva em 'instancia_ativa.txt'")

if __name__ == "__main__":
    main()