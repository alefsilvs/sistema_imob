#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar envio de notificação WhatsApp
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.services import WhatsAppService

def testar_notificacao():
    """Testa o envio de notificação WhatsApp"""
    
    print("=" * 60)
    print(" TESTE DE NOTIFICAÇÃO WHATSAPP")
    print("=" * 60)
    print(f"ℹ️ Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Inicializar serviço
    whatsapp_service = WhatsAppService()
    
    # Verificar se está conectado
    print("🔍 Verificando status da conexão...")
    status = whatsapp_service.get_provider_status()
    print(f"Status: {status}")
    print()
    
    # Número de teste (substitua pelo seu número)
    numero_teste = "5511999999999"  # Formato: 55 + DDD + número
    
    print(f"📱 Testando envio para: {numero_teste}")
    print()
    
    # Teste 1: Mensagem simples
    print("📤 Teste 1: Mensagem simples")
    try:
        resultado = whatsapp_service.send_message(
            to_number=numero_teste,
            message="🧪 Teste de notificação - Sistema IMO\n\nEste é um teste para verificar se as notificações WhatsApp estão funcionando corretamente."
        )
        
        if resultado.get('success'):
            print("✅ Mensagem enviada com sucesso!")
            print(f"ID da mensagem: {resultado.get('message_id', 'N/A')}")
        else:
            print("❌ Falha no envio:")
            print(f"Erro: {resultado.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
    
    print()
    
    # Teste 2: Mensagem com formatação
    print("📤 Teste 2: Mensagem com formatação")
    try:
        mensagem_formatada = """
🏠 *Sistema IMO - Notificação*

📋 *Detalhes:*
• Data: {data}
• Hora: {hora}
• Status: ✅ Ativo

💡 _Esta é uma mensagem de teste com formatação._

---
Sistema IMO © 2024
        """.format(
            data=datetime.now().strftime('%d/%m/%Y'),
            hora=datetime.now().strftime('%H:%M:%S')
        )
        
        resultado = whatsapp_service.send_message(
            to_number=numero_teste,
            message=mensagem_formatada
        )
        
        if resultado.get('success'):
            print("✅ Mensagem formatada enviada com sucesso!")
            print(f"ID da mensagem: {resultado.get('message_id', 'N/A')}")
        else:
            print("❌ Falha no envio da mensagem formatada:")
            print(f"Erro: {resultado.get('error', 'Erro desconhecido')}")
            
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
    
    print()
    print("=" * 60)
    print(" TESTE CONCLUÍDO")
    print("=" * 60)
    
    # Instruções finais
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Verifique se recebeu as mensagens no WhatsApp")
    print("2. Se não recebeu, acesse: http://localhost:8080/manager")
    print("3. Escaneie o QR Code para conectar o WhatsApp")
    print("4. Execute este teste novamente após conectar")
    print()

if __name__ == "__main__":
    testar_notificacao()