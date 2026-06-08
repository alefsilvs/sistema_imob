#!/usr/bin/env python
"""
Teste específico para o número 61983036586
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

from notificacoes.services import WhatsAppService
from django.conf import settings

def teste_meu_numero():
    print("🔍 Testando WhatsApp para o número 61983036586")
    print("="*50)
    
    # Verificar configurações
    print(f"Provedor: {getattr(settings, 'WHATSAPP_PROVIDER', 'não configurado')}")
    print(f"Modo teste: {getattr(settings, 'WHATSAPP_TEST_MODE', False)}")
    print(f"URL Evolution: {getattr(settings, 'EVOLUTION_API_URL', 'não configurado')}")
    print()
    
    try:
        service = WhatsAppService()
        
        # Seu número formatado corretamente
        meu_numero = "+5561983036586"  # Formato internacional
        mensagem = "🤖 Teste do Sistema Imobiliário\n\nOlá! Este é um teste das notificações WhatsApp do seu sistema.\n\nSe você recebeu esta mensagem, tudo está funcionando perfeitamente! ✅"
        
        print(f"📱 Enviando mensagem de teste para: {meu_numero}")
        print(f"📝 Mensagem: {mensagem[:50]}...")
        print()
        
        resultado = service.send_message(meu_numero, mensagem)
        
        if resultado.get('success'):
            print("✅ SUCESSO! Mensagem enviada")
            print(f"   ID da mensagem: {resultado.get('message_id')}")
            print(f"   Status: {resultado.get('status')}")
            print(f"   Provedor usado: {resultado.get('provider')}")
            
            if settings.WHATSAPP_TEST_MODE:
                print("\n⚠️  ATENÇÃO: Sistema em modo TESTE")
                print("   A mensagem foi simulada, não foi enviada de verdade")
                print("   Para envios reais, configure uma Evolution API real")
        else:
            print(f"❌ ERRO no envio: {resultado.get('error')}")
            print(f"   Detalhes: {resultado.get('details', 'Nenhum detalhe disponível')}")
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("💡 PRÓXIMOS PASSOS:")
    print("1. Se quiser envios REAIS, precisa configurar Evolution API real")
    print("2. Ou manter em teste para desenvolvimento")
    print("3. Posso ajudar a configurar qualquer uma das opções!")

if __name__ == '__main__':
    teste_meu_numero()