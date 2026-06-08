#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas do WhatsApp
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.conf import settings
from notificacoes.services import WhatsAppService, EvolutionAPIService

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_status(message, status="INFO"):
    """Imprime status formatado"""
    icons = {
        "SUCCESS": "✅",
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }
    print(f"{icons.get(status, 'ℹ️')} {message}")

def check_evolution_api_connection():
    """Verifica conexão com Evolution API"""
    print_header("VERIFICANDO CONEXÃO COM EVOLUTION API")
    
    try:
        # Verificar configurações
        api_url = getattr(settings, 'EVOLUTION_API_URL', None)
        api_key = getattr(settings, 'EVOLUTION_API_KEY', None)
        instance_name = getattr(settings, 'EVOLUTION_INSTANCE_NAME', None)
        
        print_status(f"URL da API: {api_url}")
        print_status(f"Chave da API: {api_key[:10]}..." if api_key else "Não configurada")
        print_status(f"Nome da instância: {instance_name}")
        
        if not all([api_url, api_key, instance_name]):
            print_status("Configurações incompletas!", "ERROR")
            return False
        
        # Testar conexão básica
        try:
            response = requests.get(f"{api_url}/instance/fetchInstances", 
                                  headers={'apikey': api_key}, 
                                  timeout=10)
            
            if response.status_code == 200:
                print_status("Conexão com Evolution API: OK", "SUCCESS")
                
                # Verificar se a instância existe
                instances = response.json()
                instance_exists = any(inst.get('instance', {}).get('instanceName') == instance_name 
                                    for inst in instances)
                
                if instance_exists:
                    print_status(f"Instância '{instance_name}' encontrada", "SUCCESS")
                else:
                    print_status(f"Instância '{instance_name}' NÃO encontrada", "ERROR")
                    print_status("Instâncias disponíveis:")
                    for inst in instances:
                        name = inst.get('instance', {}).get('instanceName', 'N/A')
                        status = inst.get('instance', {}).get('status', 'N/A')
                        print(f"  - {name} (Status: {status})")
                
                return instance_exists
            else:
                print_status(f"Erro HTTP {response.status_code}: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.ConnectionError:
            print_status("Erro de conexão: Evolution API não está rodando", "ERROR")
            return False
        except requests.exceptions.Timeout:
            print_status("Timeout: Evolution API não responde", "ERROR")
            return False
        except Exception as e:
            print_status(f"Erro inesperado: {e}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Erro na verificação: {e}", "ERROR")
        return False

def check_whatsapp_service():
    """Verifica o serviço WhatsApp"""
    print_header("VERIFICANDO SERVIÇO WHATSAPP")
    
    try:
        service = WhatsAppService()
        
        # Verificar configuração
        if service.is_configured():
            print_status("WhatsAppService configurado", "SUCCESS")
        else:
            print_status("WhatsAppService NÃO configurado", "ERROR")
            return False
        
        # Verificar provedor ativo
        provider = service.get_active_provider()
        print_status(f"Provedor ativo: {provider}")
        
        # Verificar status do provedor
        status = service.get_provider_status()
        print_status(f"Status do provedor: {status}")
        
        return True
        
    except Exception as e:
        print_status(f"Erro no serviço WhatsApp: {e}", "ERROR")
        return False

def test_message_sending():
    """Testa envio de mensagem"""
    print_header("TESTANDO ENVIO DE MENSAGEM")
    
    try:
        service = WhatsAppService()
        
        # Número de teste
        numero_teste = "+5511999999999"
        mensagem_teste = f"🤖 Teste de diagnóstico\n\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\nSe você recebeu esta mensagem, o WhatsApp está funcionando!"
        
        print_status(f"Enviando mensagem para: {numero_teste}")
        print_status(f"Mensagem: {mensagem_teste[:50]}...")
        
        resultado = service.send_message(numero_teste, mensagem_teste)
        
        if resultado.get('success'):
            print_status("Mensagem enviada com sucesso!", "SUCCESS")
            print_status(f"ID da mensagem: {resultado.get('message_id')}")
            print_status(f"Status: {resultado.get('status')}")
            return True
        else:
            print_status(f"Erro no envio: {resultado.get('error')}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Erro no teste de envio: {e}", "ERROR")
        return False

def suggest_fixes():
    """Sugere correções para problemas encontrados"""
    print_header("SUGESTÕES DE CORREÇÃO")
    
    print_status("1. Verificar se Evolution API está rodando:")
    print("   cd evolution-api")
    print("   npm run dev:server")
    print()
    
    print_status("2. Verificar configurações no .env:")
    print("   EVOLUTION_API_URL=http://localhost:8080")
    print("   EVOLUTION_API_KEY=sua_chave_aqui")
    print("   EVOLUTION_INSTANCE_NAME=sistema_imo")
    print()
    
    print_status("3. Criar nova instância se necessário:")
    print("   Acesse: http://localhost:8080/manager")
    print("   Crie uma nova instância com nome: sistema_imo")
    print()
    
    print_status("4. Verificar logs detalhados:")
    print("   tail -f protection.log | grep WhatsApp")

def main():
    """Função principal"""
    print_header("DIAGNÓSTICO DO SISTEMA WHATSAPP")
    print_status(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Executar verificações
    api_ok = check_evolution_api_connection()
    service_ok = check_whatsapp_service()
    
    if api_ok and service_ok:
        test_ok = test_message_sending()
        
        if test_ok:
            print_header("RESULTADO FINAL")
            print_status("Sistema WhatsApp funcionando corretamente!", "SUCCESS")
        else:
            print_header("RESULTADO FINAL")
            print_status("Problema no envio de mensagens", "ERROR")
            suggest_fixes()
    else:
        print_header("RESULTADO FINAL")
        print_status("Problemas de configuração encontrados", "ERROR")
        suggest_fixes()

if __name__ == "__main__":
    main()