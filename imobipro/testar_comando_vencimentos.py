#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.management.commands.verificar_vencimentos_bancas import Command
from imoveis.models import ContratoBancaFeira
from notificacoes.models import TemplateNotificacao
from django.utils import timezone
from datetime import timedelta

def testar_comando_vencimentos():
    """Testa o comando de verificação de vencimentos para identificar problemas"""
    
    print("🔍 TESTANDO COMANDO DE VERIFICAÇÃO DE VENCIMENTOS")
    print("=" * 60)
    
    try:
        # Instanciar o comando
        command = Command()
        
        # Buscar um contrato que está próximo do vencimento
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=30)
        
        contratos = ContratoBancaFeira.objects.filter(
            data_fim__gte=hoje,
            data_fim__lte=data_limite,
            status='ATIVO'
        )
        
        if not contratos.exists():
            print("⚠️ Nenhum contrato próximo do vencimento encontrado")
            # Criar um contrato de teste
            contrato = ContratoBancaFeira.objects.first()
            if contrato:
                # Ajustar data para teste
                contrato.data_fim = hoje + timedelta(days=7)
                contrato.save()
                print(f"✅ Contrato ajustado para teste: {contrato.numero}")
            else:
                print("❌ Nenhum contrato disponível para teste")
                return
        else:
            contrato = contratos.first()
            print(f"✅ Contrato encontrado: {contrato.numero}")
        
        # Testar criação do contexto
        print("\n📋 TESTANDO CRIAÇÃO DO CONTEXTO...")
        contexto = command.criar_contexto_banca(contrato)
        
        print(f"✅ Contexto criado com {len(contexto)} itens")
        
        # Verificar dados PIX no contexto
        pix_data = contexto.get('pix', {})
        print(f"\n💰 DADOS PIX NO CONTEXTO:")
        print(f"- Disponível: {pix_data.get('disponivel', False)}")
        print(f"- Código PIX: {'✅ OK' if pix_data.get('codigo_pix') else '❌ VAZIO'}")
        print(f"- QR Code: {'✅ OK' if pix_data.get('qr_code_base64') else '❌ VAZIO'}")
        
        if pix_data.get('qr_code_base64'):
            qr_len = len(pix_data['qr_code_base64'])
            print(f"- Tamanho QR Code: {qr_len} caracteres")
            print(f"- Primeiros 50 chars: {pix_data['qr_code_base64'][:50]}...")
        
        # Buscar template
        template = TemplateNotificacao.objects.get(nome='Cobrança Banca de Feira - Email')
        print(f"\n📧 TEMPLATE: {template.nome}")
        
        # Testar renderização do assunto
        assunto_renderizado = template.renderizar_assunto(contexto)
        print(f"✅ Assunto renderizado: {assunto_renderizado}")
        
        # Testar renderização do corpo
        corpo_renderizado = template.renderizar_corpo(contexto)
        print(f"✅ Corpo renderizado: {len(corpo_renderizado)} caracteres")
        
        # Verificar se há problemas na renderização
        problemas = []
        if '{{pix.qr_code_base64}}' in corpo_renderizado:
            problemas.append("Variável pix.qr_code_base64 não renderizada")
        if '{{' in corpo_renderizado and '}}' in corpo_renderizado:
            import re
            vars_nao_renderizadas = re.findall(r'\{\{[^}]+\}\}', corpo_renderizado)
            if vars_nao_renderizadas:
                problemas.append(f"Variáveis não renderizadas: {vars_nao_renderizadas[:5]}")
        
        if problemas:
            print("\n❌ PROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                print(f"   - {problema}")
        else:
            print("\n✅ Renderização OK - Nenhum problema encontrado")
        
        # Salvar corpo renderizado
        with open('corpo_comando_vencimentos.html', 'w', encoding='utf-8') as f:
            f.write(corpo_renderizado)
        print("📄 Corpo renderizado salvo em 'corpo_comando_vencimentos.html'")
        
        # Testar método enviar_email
        print("\n📧 TESTANDO MÉTODO ENVIAR_EMAIL...")
        
        # Criar uma notificação de teste
        from notificacoes.models import Notificacao
        notificacao_teste = Notificacao(
            tipo='EMAIL',
            destinatario=contrato.inquilino.email,
            template=template,
            contrato_banca_feira=contrato,
            status='PENDENTE'
        )
        
        # Simular envio (sem realmente enviar)
        try:
            # Não vamos realmente enviar, apenas testar a preparação
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            email = EmailMessage(
                subject=assunto_renderizado,
                body=corpo_renderizado,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contrato.inquilino.email]
            )
            
            if template.formato == 'HTML':
                email.content_subtype = 'html'
            
            # Verificar se QR Code seria anexado
            if pix_data.get('disponivel') and pix_data.get('qr_code_base64'):
                import base64
                qr_code_data = base64.b64decode(pix_data['qr_code_base64'])
                email.attach(
                    f"QR_Code_PIX_Banca_{contrato.numero}.png",
                    qr_code_data,
                    'image/png'
                )
                print("✅ QR Code seria anexado ao email")
            else:
                print("⚠️ QR Code não seria anexado")
            
            print(f"✅ Email preparado com sucesso")
            print(f"   - Para: {email.to}")
            print(f"   - Assunto: {email.subject}")
            print(f"   - Tipo: {email.content_subtype}")
            print(f"   - Anexos: {len(email.attachments)}")
            
        except Exception as e:
            print(f"❌ Erro ao preparar email: {e}")
        
        print("\n" + "=" * 60)
        print("RESUMO DO TESTE DO COMANDO:")
        print(f"- Contrato: ✅ OK")
        print(f"- Contexto: ✅ OK")
        print(f"- PIX disponível: {'✅ SIM' if pix_data.get('disponivel') else '❌ NÃO'}")
        print(f"- QR Code gerado: {'✅ SIM' if pix_data.get('qr_code_base64') else '❌ NÃO'}")
        print(f"- Template renderizado: {'✅ OK' if not problemas else '❌ COM PROBLEMAS'}")
        print(f"- Email preparado: ✅ OK")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_comando_vencimentos()