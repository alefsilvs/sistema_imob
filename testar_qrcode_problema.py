#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao
from imoveis.models import ContratoBancaFeira
from pagamentos.models import ConfiguracaoPagamento
from django.template import Template, Context
import re

def testar_qrcode_problema():
    """Testa especificamente o problema do QR Code PIX"""
    
    print("🔍 TESTANDO PROBLEMA DO QR CODE PIX")
    print("=" * 50)
    
    try:
        # 1. Buscar template
        template = TemplateNotificacao.objects.get(nome='Cobrança Banca de Feira - Email')
        print(f"✅ Template encontrado: {template.nome}")
        
        # 2. Buscar contrato
        contrato = ContratoBancaFeira.objects.first()
        if not contrato:
            print("❌ Nenhum contrato de banca encontrado")
            return
        print(f"✅ Contrato encontrado: {contrato.numero}")
        
        # 3. Testar geração do QR Code
        from pagamentos.utils import gerar_codigo_pix_real, gerar_qr_code_pix
        
        config_pix = ConfiguracaoPagamento.get_configuracao()
        if not config_pix or not config_pix.pix_chave:
            print("❌ Configuração PIX não encontrada")
            return
        
        print(f"✅ Configuração PIX encontrada: {config_pix.pix_chave}")
        
        # 4. Gerar dados PIX
        dados_pix = {
            'chave': config_pix.pix_chave,
            'valor': float(contrato.valor_total_mensal),
            'nome_recebedor': config_pix.pix_nome_recebedor or 'GESTAO FEIRA MUNICIPAL',
            'cidade': 'SAO PAULO',
            'identificador': f'BANCA{contrato.id}'
        }
        
        codigo_pix = gerar_codigo_pix_real(dados_pix)
        print(f"✅ Código PIX gerado: {codigo_pix[:50]}...")
        
        qr_code_base64 = gerar_qr_code_pix(codigo_pix)
        if qr_code_base64:
            print(f"✅ QR Code gerado: {len(qr_code_base64)} caracteres")
            print(f"   Primeiros 50 chars: {qr_code_base64[:50]}...")
        else:
            print("❌ Falha ao gerar QR Code")
            return
        
        # 5. Criar contexto completo
        contexto = {
            'inquilino_nome': contrato.inquilino.nome,
            'banca_codigo': contrato.banca_feira.codigo,
            'banca_localizacao': contrato.banca_feira.localizacao_completa,
            'banca_tipo': contrato.banca_feira.get_tipo_display(),
            'contrato_numero': contrato.numero,
            'data_vencimento': contrato.data_fim.strftime('%d/%m/%Y'),
            'valor_total': f'R$ {contrato.valor_total_mensal:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            'pix': {
                'codigo_pix': codigo_pix,
                'qr_code_base64': qr_code_base64,
                'disponivel': True
            },
            'link_pagamento': 'https://exemplo.com/pagamento',
            'empresa_nome': 'Sistema Imobiliário',
            'empresa_telefone': '(11) 99999-9999',
            'empresa_email': 'contato@sistema.com'
        }
        
        print("✅ Contexto criado com sucesso")
        
        # 6. Renderizar template
        django_template = Template(template.corpo_template)
        django_context = Context(contexto)
        corpo_renderizado = django_template.render(django_context)
        
        print("✅ Template renderizado com sucesso")
        
        # 7. Verificar se o QR Code foi renderizado corretamente
        if '{{pix.qr_code_base64}}' in corpo_renderizado:
            print("❌ PROBLEMA ENCONTRADO: Variável não foi renderizada!")
            print("   A variável {{pix.qr_code_base64}} ainda está presente no HTML renderizado")
        elif 'data:image/png;base64,' + qr_code_base64 in corpo_renderizado:
            print("✅ QR Code renderizado corretamente no template")
        else:
            print("⚠️ QR Code pode ter sido renderizado, mas não foi possível confirmar")
        
        # 8. Procurar por problemas específicos
        problemas = []
        if 'data:image/png;base64,{{' in corpo_renderizado:
            problemas.append("Variável Django não renderizada")
        if 'net::ERR_INVALID_URL' in corpo_renderizado:
            problemas.append("Erro de URL inválida encontrado")
        
        if problemas:
            print("❌ PROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                print(f"   - {problema}")
        else:
            print("✅ Nenhum problema óbvio encontrado")
        
        # 9. Salvar HTML renderizado para análise
        with open('template_renderizado_teste.html', 'w', encoding='utf-8') as f:
            f.write(corpo_renderizado)
        print("📄 Template renderizado salvo em 'template_renderizado_teste.html'")
        
        # 10. Verificar se o QR Code é válido
        if qr_code_base64:
            try:
                import base64
                decoded = base64.b64decode(qr_code_base64)
                print(f"✅ QR Code base64 é válido: {len(decoded)} bytes")
            except Exception as e:
                print(f"❌ QR Code base64 inválido: {e}")
        
        print("\n" + "=" * 50)
        print("RESUMO DO TESTE:")
        print(f"- Template: ✅ OK")
        print(f"- Contrato: ✅ OK") 
        print(f"- Config PIX: ✅ OK")
        print(f"- Código PIX: ✅ OK")
        print(f"- QR Code: ✅ OK" if qr_code_base64 else "❌ FALHOU")
        print(f"- Renderização: ✅ OK" if '{{pix.qr_code_base64}}' not in corpo_renderizado else "❌ FALHOU")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_qrcode_problema()