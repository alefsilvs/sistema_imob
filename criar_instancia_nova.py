#!/usr/bin/env python3
"""
Script para criar uma nova instância com nome único e obter QR Code
"""

import requests
import json
import os
from dotenv import load_dotenv
import time
import base64
import random
import string

# Carregar variáveis do .env
load_dotenv()

# Configurações da API
API_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8081')
API_KEY = os.getenv('EVOLUTION_API_KEY', 'F8A3B2C9D4E5F6A7B8C9D0E1F2A3B4C5')

# Gerar nome único para a instância
timestamp = str(int(time.time()))
random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
INSTANCE_NAME = f"sistema_imo_{timestamp}_{random_suffix}"

# Headers para as requisições
headers = {
    'Content-Type': 'application/json',
    'apikey': API_KEY
}

def criar_instancia():
    """Cria uma nova instância"""
    try:
        url = f"{API_URL}/instance/create"
        print(f"🆕 Criando instância '{INSTANCE_NAME}' em: {url}")
        
        data = {
            "instanceName": INSTANCE_NAME,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Instância criada com sucesso")
            print(f"Dados: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Erro ao criar: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao criar: {e}")
        return None

def conectar_instancia():
    """Conecta a instância"""
    try:
        url = f"{API_URL}/instance/connect/{INSTANCE_NAME}"
        print(f"🔗 Conectando instância em: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resposta da conexão: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Erro ao conectar: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None

def aguardar_e_obter_qr():
    """Aguarda e tenta obter QR Code"""
    print("⏳ Aguardando QR Code ser gerado...")
    
    for tentativa in range(15):  # 15 tentativas
        print(f"🔄 Tentativa {tentativa + 1}/15...")
        
        try:
            # Tentar conectar novamente
            url = f"{API_URL}/instance/connect/{INSTANCE_NAME}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Resposta: {json.dumps(data, indent=2)}")
                
                # Verificar se há QR Code
                qr_code = None
                if isinstance(data, dict):
                    qr_code = (data.get('base64') or 
                              data.get('code') or 
                              data.get('qrcode') or 
                              data.get('qr'))
                    
                    # Verificar se não há erro e há QR Code
                    if not data.get('error') and qr_code:
                        print(f"✅ QR Code encontrado!")
                        
                        # Salvar QR Code
                        with open(f'qrcode_{INSTANCE_NAME}.txt', 'w') as f:
                            f.write(qr_code)
                        print(f"💾 QR Code salvo em: qrcode_{INSTANCE_NAME}.txt")
                        
                        # Salvar nome da instância ativa
                        with open('instancia_ativa.txt', 'w') as f:
                            f.write(INSTANCE_NAME)
                        print(f"📝 Nome da instância salvo em: instancia_ativa.txt")
                        
                        # Tentar salvar como imagem se for base64
                        if qr_code.startswith('data:image'):
                            try:
                                base64_data = qr_code.split(',')[1]
                                image_data = base64.b64decode(base64_data)
                                
                                with open(f'qrcode_{INSTANCE_NAME}.png', 'wb') as f:
                                    f.write(image_data)
                                print(f"🖼️ QR Code salvo como imagem: qrcode_{INSTANCE_NAME}.png")
                            except Exception as e:
                                print(f"⚠️ Não foi possível salvar como imagem: {e}")
                        
                        return True
                    elif data.get('error'):
                        print(f"⚠️ Erro na resposta: {data.get('message', 'Erro desconhecido')}")
                    else:
                        print(f"⚠️ QR Code ainda não disponível")
                        
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa + 1}: {e}")
        
        # Aguardar antes da próxima tentativa
        time.sleep(2)
    
    print("❌ Não foi possível obter QR Code após 15 tentativas")
    return False

def main():
    print("=" * 60)
    print("🆕 CRIAR NOVA INSTÂNCIA E OBTER QR CODE")
    print("=" * 60)
    print(f"📋 Nova instância: {INSTANCE_NAME}")
    print(f"🌐 URL da API: {API_URL}")
    print()
    
    # 1. Criar nova instância
    print("1️⃣ Criando nova instância...")
    instancia = criar_instancia()
    
    if not instancia:
        print("❌ Falha ao criar instância")
        return
    
    time.sleep(3)
    print()
    
    # 2. Conectar instância
    print("2️⃣ Conectando instância...")
    conexao = conectar_instancia()
    
    if not conexao:
        print("❌ Falha ao conectar instância")
        return
    
    print()
    
    # 3. Aguardar e obter QR Code
    print("3️⃣ Aguardando QR Code...")
    if aguardar_e_obter_qr():
        print("✅ QR Code obtido com sucesso!")
        print()
        print("📱 Para conectar o WhatsApp:")
        print("   1. Abra o WhatsApp no seu celular")
        print("   2. Vá em Configurações > Aparelhos conectados")
        print("   3. Toque em 'Conectar um aparelho'")
        print(f"   4. Escaneie o QR Code salvo em: qrcode_{INSTANCE_NAME}.txt")
    else:
        print("❌ Não foi possível obter QR Code")
        print()
        print("💡 Sugestões:")
        print("   - Acesse o manager web em: http://localhost:8081/manager")
        print(f"   - Procure pela instância: {INSTANCE_NAME}")
        print("   - Clique no botão 'Connect' da instância")
        print("   - O QR Code deve aparecer na interface web")
    
    print()
    print("=" * 60)
    print("🏁 PROCESSO FINALIZADO")
    print("=" * 60)

if __name__ == "__main__":
    main()