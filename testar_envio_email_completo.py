#!/usr/bin/env python
"""
Script para testar o envio completo de email com QR Code PIX
Simula exatamente o processo do comando verificar_vencimentos_bancas
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.core.mail import EmailMessage
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from notificacoes.models import TemplateNotificacao
from contratos.models import Contrato
from pagamentos.models import ConfiguracaoPagamento
from pagamentos.utils import gerar_codigo_pix_real
import base64
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def testar_envio_email_completo():
    """Testa o envio completo de email com QR Code PIX"""
    
    print("🔍 TESTE COMPLETO: ENVIO DE EMAIL COM QR CODE PIX")
    print("=" * 60)
    
    try:
        # 1. Buscar template
        print("📋 1. Buscando template...")
        template = TemplateNotificacao.objects.filter(
            nome__icontains='Cobrança'
        ).filter(
            nome__icontains='Email'
        ).first()
        
        if not template:
            print("❌ Template não encontrado")
            return
            
        print(f"✅ Template: {template.nome}")
        
        # 2. Buscar contrato
        print("\n📋 2. Buscando contrato...")
        contrato = Contrato.objects.first()
        
        if not contrato:
            print("❌ Contrato não encontrado")
            return
            
        print(f"✅ Contrato: {contrato.numero}")
        
        # 3. Buscar configuração PIX
        print("\n📋 3. Verificando configuração PIX...")
        config_pix = ConfiguracaoPagamento.get_configuracao()
        
        if not config_pix or not config_pix.pix_habilitado:
            print("❌ PIX não configurado ou desabilitado")
            return
            
        print(f"✅ Config PIX: {config_pix.pix_chave}")
        
        # 4. Gerar dados PIX
        print("\n📋 4. Gerando código PIX...")
        dados_pix = {
            'chave': config_pix.pix_chave,
            'valor': 1050.00,
            'nome_recebedor': config_pix.pix_nome_recebedor or "SISTEMA IMOBILIARIO",
            'cidade': "SAO PAULO",
            'identificador': 'BANCA1'
        }
        
        codigo_pix = gerar_codigo_pix_real(dados_pix)
        print(f"✅ Código PIX: {len(codigo_pix)} chars")
        
        # 5. Gerar QR Code
        print("\n📋 5. Gerando QR Code...")
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(codigo_pix)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"✅ QR Code Base64: {len(qr_code_base64)} chars")
        
        # 6. Criar contexto
        print("\n📋 6. Criando contexto...")
        contexto = {
            'inquilino_nome': 'João Silva',
            'imovel_endereco': 'Rua das Flores, 123',
            'valor_aluguel': '1.050,00',
            'data_vencimento': '25/01/2025',
            'inquilino_cpf': '123.456.789-00',
            'inquilino_telefone': '(11) 99999-9999',
            'inquilino_email': 'joao@teste.com',
            'inquilino_endereco': 'Rua das Flores, 123',
            'link_pagamento': 'https://exemplo.com/pagamento',
            'telefone_contato': '(11) 3333-3333',
            'email_contato': 'contato@imobiliaria.com',
            'empresa_nome': 'Imobiliária Teste',
            'pix': {
                'disponivel': True,
                'codigo_pix': codigo_pix,
                'qr_code_base64': qr_code_base64
            }
        }
        
        print(f"✅ Contexto criado com PIX disponível")
        
        # 7. Renderizar template
        print("\n📋 7. Renderizando template...")
        template_django = Template(template.corpo_template)
        context = Context(contexto)
        corpo_renderizado = template_django.render(context)
        
        print(f"✅ Template renderizado: {len(corpo_renderizado)} chars")
        
        # 8. Verificar data URLs no HTML
        print("\n📋 8. Verificando data URLs...")
        import re
        data_url_pattern = r'data:image/png;base64,([A-Za-z0-9+/=]+)'
        matches = re.findall(data_url_pattern, corpo_renderizado)
        
        if matches:
            print(f"✅ {len(matches)} data URL(s) encontrada(s)")
            for i, match in enumerate(matches, 1):
                print(f"   Data URL {i}: {len(match)} chars")
        else:
            print("⚠️  Nenhuma data URL encontrada no HTML")
        
        # 9. Salvar HTML para debug
        print("\n📋 9. Salvando HTML de debug...")
        with open('email_completo_debug.html', 'w', encoding='utf-8') as f:
            f.write(corpo_renderizado)
        print("✅ HTML salvo em 'email_completo_debug.html'")
        
        # 10. Simular envio de email
        print("\n📋 10. Simulando envio de email...")
        
        # Verificar configurações de email
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("⚠️  Configurações de email não encontradas - simulando envio")
            
            # Criar email sem enviar
            email = EmailMessage(
                subject='Teste QR Code PIX - Cobrança Banca',
                body=corpo_renderizado,
                from_email=settings.DEFAULT_FROM_EMAIL or 'teste@sistema.com',
                to=['teste@exemplo.com']
            )
            
            email.content_subtype = 'html'
            
            # Anexar QR Code como arquivo PNG
            qr_code_data = base64.b64decode(qr_code_base64)
            email.attach(
                f"QR_Code_PIX_Banca_{contrato.numero}.png",
                qr_code_data,
                'image/png'
            )
            
            print("✅ Email criado com sucesso (não enviado)")
            print(f"   • Assunto: {email.subject}")
            print(f"   • Para: {email.to}")
            print(f"   • Tipo: {email.content_subtype}")
            print(f"   • Anexos: {len(email.attachments)}")
            print(f"   • Tamanho do corpo: {len(email.body)} chars")
            
        else:
            print("📧 Configurações de email encontradas - enviando email real...")
            
            # Criar e enviar email
            email = EmailMessage(
                subject='Teste QR Code PIX - Cobrança Banca',
                body=corpo_renderizado,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.EMAIL_HOST_USER]  # Enviar para si mesmo
            )
            
            email.content_subtype = 'html'
            
            # Anexar QR Code como arquivo PNG
            qr_code_data = base64.b64decode(qr_code_base64)
            email.attach(
                f"QR_Code_PIX_Banca_{contrato.numero}.png",
                qr_code_data,
                'image/png'
            )
            
            try:
                email.send()
                print("✅ Email enviado com sucesso!")
                print(f"   • Verifique a caixa de entrada: {settings.EMAIL_HOST_USER}")
            except Exception as e:
                print(f"❌ Erro ao enviar email: {e}")
        
        # 11. Resumo final
        print("\n📋 RESUMO DO TESTE:")
        print(f"   • Template: ✅ {template.nome}")
        print(f"   • Contrato: ✅ {contrato.numero}")
        print(f"   • PIX: ✅ {config_pix.pix_chave}")
        print(f"   • Código PIX: ✅ {len(codigo_pix)} chars")
        print(f"   • QR Code: ✅ {len(qr_code_base64)} chars")
        print(f"   • Data URLs: ✅ {len(matches)} encontrada(s)")
        print(f"   • HTML: ✅ {len(corpo_renderizado)} chars")
        print(f"   • Email: ✅ Criado")
        
        print("\n✅ TESTE CONCLUÍDO - Verifique o arquivo HTML e o email")
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_envio_email_completo()