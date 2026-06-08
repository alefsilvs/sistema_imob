#!/usr/bin/env python
"""
Script de teste para Evolution API
Testa o envio de mensagens WhatsApp via Evolution API no modo simulação
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.services import WhatsAppService, EvolutionAPIService
from django.conf import settings

def teste_configuracao():
    """Testa se as configurações estão corretas"""
    print("🔍 Testando configurações...")
    print(f"   Provedor: {getattr(settings, 'WHATSAPP_PROVIDER', 'não configurado')}")
    print(f"   Modo teste: {getattr(settings, 'WHATSAPP_TEST_MODE', False)}")
    print(f"   URL Evolution: {getattr(settings, 'EVOLUTION_API_URL', 'não configurado')}")
    print(f"   Instância: {getattr(settings, 'EVOLUTION_INSTANCE_NAME', 'não configurado')}")
    print()

def teste_evolution_api_direta():
    """Testa Evolution API diretamente"""
    print("🧪 Testando Evolution API diretamente...")
    
    try:
        evolution = EvolutionAPIService()
        
        # Verificar configuração
        if evolution.is_configured():
            print("✅ Evolution API configurada")
        else:
            print("⚠️  Evolution API em modo de teste")
        
        # Testar status da instância
        status = evolution.get_instance_status()
        print(f"   Status da instância: {status}")
        
        # Testar envio de mensagem em modo de teste
        numero_teste = "+5511999999999"
        mensagem_teste = "🤖 Teste Evolution API\n\nEste é um teste do sistema de notificações."
        
        print(f"📱 Testando envio de mensagem para {numero_teste}...")
        
        # Primeiro teste em modo simulação
        evolution.test_mode = True
        print("\n   🔄 Modo simulação:")
        resultado_teste = evolution.send_message(numero_teste, mensagem_teste)
        
        if resultado_teste.get('success'):
            print("   ✅ Simulação bem-sucedida!")
            print(f"      ID: {resultado_teste.get('message_id')}")
            print(f"      Status: {resultado_teste.get('status')}")
        
        # Depois teste real (que pode falhar com número inexistente)
        evolution.test_mode = False
        print("\n   🌐 Teste real (pode falhar com número inexistente):")
        resultado_real = evolution.send_message(numero_teste, mensagem_teste)
        
        if resultado_real.get('success'):
            print("   ✅ Mensagem real enviada com sucesso!")
            print(f"      ID: {resultado_real.get('message_id')}")
            print(f"      Status: {resultado_real.get('status')}")
        else:
            print(f"   ⚠️  Erro esperado (número inexistente): {resultado_real.get('error')}")
            print("   ℹ️  Isso é normal - o número de teste não existe no WhatsApp")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    print()

def teste_whatsapp_service():
    """Testa WhatsAppService (interface unificada)"""
    print("📞 Testando WhatsAppService...")
    
    try:
        service = WhatsAppService()
        
        # Verificar configuração
        if service.is_configured():
            print("✅ WhatsAppService configurado")
        else:
            print("❌ WhatsAppService não configurado")
            return
        
        print(f"   Provedor ativo: {service.get_active_provider()}")
        
        # Testar status do provedor
        status = service.get_provider_status()
        print(f"   Status do provedor: {status}")
        
        # Testar envio de mensagem
        numero_teste = "+5511999999999"
        mensagem_teste = "🤖 Teste WhatsAppService\n\nTeste via interface unificada."
        
        print(f"📱 Enviando mensagem via WhatsAppService...")
        resultado = service.send_message(numero_teste, mensagem_teste)
        
        if resultado.get('success'):
            print("✅ Mensagem enviada com sucesso!")
            print(f"   ID: {resultado.get('message_id')}")
            print(f"   Status: {resultado.get('status')}")
            print(f"   Provedor: {resultado.get('provider')}")
        else:
            print(f"❌ Erro no envio: {resultado.get('error')}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    print()

def main():
    print("🚀 Iniciando testes da Evolution API\n")
    
    # Executar testes
    teste_configuracao()
    teste_evolution_api_direta()
    teste_whatsapp_service()
    
    print("✅ Testes concluídos!")
    print("\n💡 Dicas:")
    print("   - Se estiver em modo teste, as mensagens são simuladas")
    print("   - Para usar em produção, configure WHATSAPP_TEST_MODE=false")
    print("   - Configure uma Evolution API real para envios reais")

if __name__ == '__main__':
    main()