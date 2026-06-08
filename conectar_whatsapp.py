#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')

def listar_instancias():
    """Lista todas as instâncias disponíveis"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print("🔍 Buscando instâncias disponíveis...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            instancias = response.json()
            print(f"📱 Encontradas {len(instancias)} instância(s):")
            
            for i, instancia in enumerate(instancias, 1):
                nome = instancia.get('instance', {}).get('instanceName', 'N/A')
                status = instancia.get('instance', {}).get('status', 'N/A')
                print(f"   {i}. Nome: {nome} | Status: {status}")
            
            return instancias
        else:
            print(f"❌ Erro: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []

def conectar_instancia(nome):
    """Conecta uma instância específica"""
    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{nome}"
        headers = {"apikey": EVOLUTION_API_KEY}
        
        print(f"📱 Conectando instância '{nome}'...")
        response = requests.get(url, headers=headers)
        
        print(f"Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'base64' in data:
                print("✅ QR Code gerado com sucesso!")
                
                # Salva o QR Code
                filename = f'qrcode_{nome}.txt'
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

def main():
    print("🚀 Conectar WhatsApp - Sistema Imobiliário")
    print("="*60)
    
    # Lista instâncias disponíveis
    instancias = listar_instancias()
    
    if not instancias:
        print("\n❌ Nenhuma instância encontrada!")
        print("💡 Passos para resolver:")
        print("1. Acesse: http://localhost:8081/manager")
        print("2. Crie uma nova instância")
        print("3. Execute este script novamente")
        print(f"4. Use a API Key: {EVOLUTION_API_KEY}")
        return
    
    print("\n" + "="*60)
    
    # Tenta conectar cada instância
    for instancia in instancias:
        nome = instancia.get('instance', {}).get('instanceName')
        if nome:
            print(f"\n🔄 Tentando conectar: {nome}")
            if conectar_instancia(nome):
                print(f"\n🎉 SUCESSO! Instância '{nome}' conectada!")
                print("📱 Agora escaneie o QR Code com seu WhatsApp")
                
                # Salva o nome da instância ativa
                with open('instancia_ativa.txt', 'w') as f:
                    f.write(nome)
                print(f"💾 Nome da instância salvo em 'instancia_ativa.txt'")
                return
    
    print("\n❌ Não foi possível conectar nenhuma instância")

if __name__ == "__main__":
    main()