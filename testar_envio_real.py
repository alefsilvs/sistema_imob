#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.core.mail import EmailMessage
from django.conf import settings
from notificacoes.models import TemplateNotificacao, Notificacao
from imoveis.models import ContratoBancaFeira
from django.utils import timezone
import base64

def simular_envio_real():
    print("=== SIMULAÇÃO DO ENVIO REAL ===")
    
    # Buscar template e contrato
    template = TemplateNotificacao.objects.filter(nome__icontains='banca').first()
    contrato = ContratoBancaFeira.objects.first()
    
    if not template or not contrato:
        print("❌ Template ou contrato não encontrado")
        return
    
    print(f"✓ Template: {template.nome} (Formato: {template.formato})")
    print(f"✓ Contrato: {contrato.numero}")
    
    # Criar contexto exatamente como no comando
    from notificacoes.management.commands.verificar_vencimentos_bancas import Command
    cmd = Command()
    contexto = cmd.criar_contexto_banca(contrato)
    
    # Renderizar template
    assunto = template.renderizar_assunto(contexto)
    corpo = template.renderizar_corpo(contexto)
    
    print(f"✓ Assunto: {assunto}")
    print(f"✓ Corpo renderizado: {len(corpo)} caracteres")
    
    # Criar notificação como no comando
    notificacao = Notificacao(
        template=template,
        inquilino=contrato.inquilino,
        contrato_banca_feira=contrato,
        banca_feira=contrato.banca_feira,
        canal='EMAIL',
        destinatario=contrato.inquilino.email,
        assunto=assunto,
        corpo=corpo,
        prioridade='ALTA',
        usuario_id=1
    )
    
    # Simular o método enviar_email exatamente como no comando
    print("\n=== SIMULANDO MÉTODO ENVIAR_EMAIL ===")
    
    # Criar email com suporte a HTML e anexos
    email = EmailMessage(
        subject=assunto,
        body=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notificacao.destinatario]
    )
    
    # Se o template é HTML, definir como tal
    if notificacao.template and notificacao.template.formato == 'HTML':
        email.content_subtype = 'html'
        print("✓ Email configurado como HTML")
    
    # Adicionar QR Code PIX como anexo se disponível
    if contexto.get('pix', {}).get('disponivel') and contexto.get('pix', {}).get('qr_code_base64'):
        try:
            # Decodificar base64 do QR Code
            qr_code_data = base64.b64decode(contexto['pix']['qr_code_base64'])
            
            # Anexar QR Code como imagem
            email.attach(
                f"QR_Code_PIX_Banca_{notificacao.contrato_banca_feira.numero}.png",
                qr_code_data,
                'image/png'
            )
            
            print(f'✓ QR Code PIX anexado ao email')
        except Exception as qr_error:
            print(f'⚠️  Erro ao anexar QR Code PIX: {qr_error}')
    
    # Verificar configurações finais do email
    print(f"\n=== CONFIGURAÇÕES FINAIS DO EMAIL ===")
    print(f"Para: {email.to}")
    print(f"Assunto: {email.subject}")
    print(f"Content subtype: {email.content_subtype}")
    print(f"Tipo do corpo: {type(email.body)}")
    print(f"Tamanho do corpo: {len(email.body)} caracteres")
    print(f"Número de anexos: {len(email.attachments)}")
    
    if email.attachments:
        for i, attachment in enumerate(email.attachments):
            print(f"  Anexo {i+1}: {attachment[0]} ({attachment[2]})")
    
    # Salvar corpo em arquivo
    with open('email_simulacao_real.html', 'w', encoding='utf-8') as f:
        f.write(corpo)
    print("✓ Corpo salvo em 'email_simulacao_real.html'")
    
    # Verificar se seria enviado como HTML
    print(f"\n=== RESULTADO FINAL ===")
    if email.content_subtype == 'html':
        print("✅ O email SERIA enviado como HTML no corpo")
        print("✅ NÃO seria enviado como arquivo anexo")
    else:
        print("❌ O email seria enviado como texto simples")
    
    # Mostrar início do corpo para verificação
    print(f"\n=== INÍCIO DO CORPO DO EMAIL ===")
    print(corpo[:200] + "...")

if __name__ == '__main__':
    simular_envio_real()