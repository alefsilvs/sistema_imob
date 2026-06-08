#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME', 'sistema_imo')

def verificar_instancia_existe():
    """Verifica se a instância do .env existe"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"🔍 Verificando se a instância '{INSTANCE_NAME}' existe...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            instancias = response.json()
            
            for instancia in instancias:
                nome = instancia.get('instance', {}).get('instanceName')
                if nome == INSTANCE_NAME:
                    status = instancia.get('instance', {}).get('status', 'N/A')
                    print(f"✅ Instância '{INSTANCE_NAME}' encontrada! Status: {status}")
                    return True
            
            print(f"❌ Instância '{INSTANCE_NAME}' não encontrada")
            return False
        else:
            print(f"❌ Erro ao listar instâncias: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def conectar_instancia():
    """Conecta a instância específica do .env"""
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
                    print("Resposta:", json.dumps(data, indent=2))
            else:
                print(f"⚠️ Resposta inesperada: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def limpar_outras_instancias():
    """Lista outras instâncias para possível limpeza"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print("🧹 Verificando outras instâncias...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            instancias = response.json()
            outras_instancias = []
            
            for instancia in instancias:
                nome = instancia.get('instance', {}).get('instanceName')
                if nome and nome != INSTANCE_NAME:
                    outras_instancias.append(nome)
            
            if outras_instancias:
                print(f"⚠️ Encontradas {len(outras_instancias)} instâncias extras:")
                for nome in outras_instancias:
                    print(f"   - {nome}")
                
                print(f"\n💡 Para manter apenas '{INSTANCE_NAME}', você pode deletar as outras no manager:")
                print(f"   http://localhost:8081/manager")
                
                return outras_instancias
            else:
                print(f"✅ Apenas a instância '{INSTANCE_NAME}' existe")
                return []
        else:
            print(f"❌ Erro: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def main():
    print("🚀 Conectar WhatsApp - Instância do .env")
    print("="*60)
    print(f"📋 Instância configurada: {INSTANCE_NAME}")
    print(f"🔗 API URL: {EVOLUTION_API_URL}")
    print("="*60)
    
    # 1. Verifica se a instância existe
    if not verificar_instancia_existe():
        print(f"\n❌ A instância '{INSTANCE_NAME}' não foi encontrada!")
        print("💡 Verifique se:")
        print("1. A Evolution API está rodando")
        print("2. A instância foi criada no manager")
        print("3. O nome no .env está correto")
        return
    
    print("\n" + "="*60)
    
    # 2. Tenta conectar
    if conectar_instancia():
        print(f"\n🎉 SUCESSO! Instância '{INSTANCE_NAME}' conectada!")
        print("📱 Agora escaneie o QR Code com seu WhatsApp")
    else:
        print(f"\n❌ Falha ao conectar instância '{INSTANCE_NAME}'")
    
    print("\n" + "="*60)
    
    # 3. Mostra outras instâncias
    limpar_outras_instancias()

if __name__ == "__main__":
    main()