#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.management.commands.verificar_vencimentos_bancas import Command
from imoveis.models import ContratoBancaFeira

def testar_notificacao():
    print("=== TESTE DE NOTIFICAÇÃO DE BANCA ===")
    
    # Buscar o contrato de banca
    contrato = ContratoBancaFeira.objects.first()
    if not contrato:
        print("❌ Nenhum contrato de banca encontrado")
        return
    
    print(f"✓ Contrato encontrado: {contrato.numero}")
    print(f"✓ Inquilino: {contrato.inquilino.nome}")
    print(f"✓ Email: {contrato.inquilino.email}")
    
    # Criar instância do comando
    cmd = Command()
    
    # Obter template
    template = cmd.obter_template()
    if not template:
        print("❌ Nenhum template encontrado")
        return
    
    print(f"✓ Template encontrado: {template.nome}")
    print(f"✓ Tipo: {template.tipo}")
    print(f"✓ Formato: {template.formato}")
    
    # Criar contexto
    try:
        contexto = cmd.criar_contexto_banca(contrato)
        print(f"✓ Contexto criado com {len(contexto)} variáveis")
        
        # Mostrar algumas variáveis importantes
        print(f"  - PIX disponível: {contexto.get('pix', {}).get('disponivel', False)}")
        print(f"  - Valor total: {contexto.get('valor_total', 'N/A')}")
        print(f"  - Dias para vencer: {contexto.get('dias_para_vencer', 'N/A')}")
        
    except Exception as e:
        print(f"❌ ERRO ao criar contexto: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Renderizar template
    try:
        assunto = template.renderizar_assunto(contexto)
        corpo = template.renderizar_corpo(contexto)
        print(f"✓ Template renderizado com sucesso")
        print(f"  - Assunto: {assunto[:50]}...")
        print(f"  - Corpo: {len(corpo)} caracteres")
        
    except Exception as e:
        print(f"❌ ERRO ao renderizar template: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Testar envio de email (simulado)
    try:
        from notificacoes.models import Notificacao
        
        # Criar notificação de teste
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
        
        print("✓ Notificação criada (não salva)")
        
        # Testar método de envio
        resultado = cmd.enviar_email(notificacao, assunto, corpo)
        print(f"✓ Resultado do envio: {'Sucesso' if resultado else 'Falha'}")
        
        if not resultado:
            print(f"  - Status: {notificacao.status}")
            if hasattr(notificacao, 'erro_envio') and notificacao.erro_envio:
                print(f"  - Erro: {notificacao.erro_envio}")
        
    except Exception as e:
        print(f"❌ ERRO ao testar envio: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_notificacao()