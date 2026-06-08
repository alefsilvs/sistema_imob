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

def testar_formato_email():
    print("=== TESTE DE FORMATO DE EMAIL ===")
    
    # Buscar template
    template = TemplateNotificacao.objects.filter(nome__icontains='banca').first()
    if not template:
        print("❌ Template não encontrado")
        return
    
    print(f"✓ Template encontrado: {template.nome}")
    print(f"✓ Formato do template: {template.formato}")
    
    # Buscar contrato de teste
    contrato = ContratoBancaFeira.objects.first()
    if not contrato:
        print("❌ Contrato não encontrado")
        return
    
    print(f"✓ Contrato encontrado: {contrato.numero}")
    
    # Criar contexto
    valor_total = contrato.valor_aluguel + contrato.valor_taxa_feira + contrato.valor_limpeza + contrato.valor_seguranca
    contexto = {
        'banca_codigo': contrato.banca_feira.codigo,
        'banca_localizacao': contrato.banca_feira.localizacao,
        'contrato_numero': contrato.numero,
        'data_vencimento': contrato.data_fim.strftime('%d/%m/%Y'),
        'valor_total': f"R$ {valor_total:,.2f}".replace(',', '.'),
        'empresa_nome': 'IMOBILPRO',
        'empresa_telefone': '(11) 99999-9999'
    }
    
    # Renderizar template
    assunto = template.renderizar_assunto(contexto)
    corpo = template.renderizar_corpo(contexto)
    
    print(f"✓ Assunto renderizado: {assunto}")
    print(f"✓ Corpo renderizado (primeiros 100 chars): {corpo[:100]}...")
    
    # Criar email como no comando
    email = EmailMessage(
        subject=assunto,
        body=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contrato.inquilino.email]
    )
    
    # Verificar se está configurando como HTML
    if template.formato == 'HTML':
        email.content_subtype = 'html'
        print("✓ Email configurado como HTML")
    else:
        print("⚠️  Email configurado como texto")
    
    # Verificar propriedades do email
    print(f"✓ Content subtype: {email.content_subtype}")
    print(f"✓ Body type: {type(email.body)}")
    print(f"✓ Body length: {len(email.body)}")
    
    # Simular envio (sem realmente enviar)
    print("\n=== SIMULAÇÃO DE ENVIO ===")
    print(f"Para: {email.to}")
    print(f"Assunto: {email.subject}")
    print(f"Tipo de conteúdo: {email.content_subtype}")
    print(f"Corpo é HTML: {'Sim' if email.content_subtype == 'html' else 'Não'}")
    
    # Salvar corpo em arquivo para verificação
    with open('corpo_email_teste.html', 'w', encoding='utf-8') as f:
        f.write(corpo)
    print("✓ Corpo do email salvo em 'corpo_email_teste.html'")
    
    # Verificar se há anexos
    print(f"✓ Número de anexos: {len(email.attachments)}")
    
    print("\n=== RESULTADO ===")
    if email.content_subtype == 'html':
        print("✅ Email está configurado corretamente como HTML")
    else:
        print("❌ Email NÃO está configurado como HTML")

if __name__ == '__main__':
    testar_formato_email()