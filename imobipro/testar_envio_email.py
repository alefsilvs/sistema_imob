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
from django.utils import timezone
from datetime import timedelta
from imoveis.models import ContratoBancaFeira
from notificacoes.management.commands.verificar_vencimentos_bancas import Command
from notificacoes.models import Notificacao

def testar_envio_email():
    print("=== TESTANDO ENVIO REAL DE EMAIL ===\n")
    
    # Criar instância do comando
    cmd = Command()
    
    # Obter template
    template = cmd.obter_template()
    print(f"Template obtido: {template.nome}")
    print(f"Formato: {template.formato}")
    
    # Buscar um contrato de teste
    data_limite = timezone.now().date() + timedelta(days=30)
    contrato = ContratoBancaFeira.objects.filter(
        status='ATIVO',
        data_fim__lte=data_limite,
        data_fim__gte=timezone.now().date()
    ).select_related('inquilino', 'banca_feira').first()
    
    if not contrato:
        print("Nenhum contrato encontrado para teste")
        return
    
    print(f"\nContrato de teste: {contrato.numero}")
    print(f"Inquilino: {contrato.inquilino.nome}")
    print(f"Email: {contrato.inquilino.email}")
    
    # Criar contexto
    contexto = cmd.criar_contexto_banca(contrato)
    
    # Renderizar template
    assunto = template.renderizar_assunto(contexto)
    corpo = template.renderizar_corpo(contexto)
    
    print(f"\nAssunto: {assunto}")
    print(f"Tamanho do corpo: {len(corpo)} caracteres")
    print(f"É HTML: {template.formato == 'HTML'}")
    
    # Salvar o HTML renderizado em arquivo para verificação
    with open('email_renderizado.html', 'w', encoding='utf-8') as f:
        f.write(corpo)
    print(f"HTML salvo em: email_renderizado.html")
    
    # Criar notificação de teste
    notificacao = Notificacao(
        template=template,
        contrato_banca_feira=contrato,
        inquilino=contrato.inquilino,
        canal='EMAIL',
        destinatario=contrato.inquilino.email or 'teste@exemplo.com',
        assunto=assunto,
        corpo=corpo,
        prioridade='ALTA',
        usuario_id=1
    )
    notificacao.save()
    
    print(f"\nNotificação criada: ID {notificacao.id}")
    
    # Testar envio usando o método do comando
    print("\n=== TESTANDO ENVIO VIA MÉTODO DO COMANDO ===")
    try:
        sucesso = cmd.enviar_email(notificacao, assunto, corpo)
        print(f"Resultado do envio: {'SUCESSO' if sucesso else 'ERRO'}")
        print(f"Status da notificação: {notificacao.status}")
        if notificacao.erro_envio:
            print(f"Erro: {notificacao.erro_envio}")
    except Exception as e:
        print(f"Exceção durante envio: {e}")
    
    # Testar envio direto com EmailMessage
    print("\n=== TESTANDO ENVIO DIRETO COM EmailMessage ===")
    try:
        email = EmailMessage(
            subject=f"[TESTE] {assunto}",
            body=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['teste@exemplo.com']  # Email de teste
        )
        
        if template.formato == 'HTML':
            email.content_subtype = 'html'
        
        # Simular envio (não enviar realmente)
        print("Email configurado com sucesso:")
        print(f"  Subject: {email.subject}")
        print(f"  From: {email.from_email}")
        print(f"  To: {email.to}")
        print(f"  Content Type: {'text/html' if email.content_subtype == 'html' else 'text/plain'}")
        print(f"  Body size: {len(email.body)} chars")
        
        # Verificar se há variáveis não substituídas no corpo final
        import re
        variaveis_nao_substituidas = re.findall(r'\{\{[^}]+\}\}', email.body)
        if variaveis_nao_substituidas:
            print(f"\n❌ VARIÁVEIS NÃO SUBSTITUÍDAS:")
            for var in set(variaveis_nao_substituidas):
                print(f"  - {var}")
        else:
            print(f"\n✅ Todas as variáveis foram substituídas no email final")
        
        # Para teste real, descomente a linha abaixo:
        # email.send()
        print("\n📧 Email preparado (não enviado - descomente para envio real)")
        
    except Exception as e:
        print(f"Erro no envio direto: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_envio_email()