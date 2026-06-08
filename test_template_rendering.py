#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao
from contratos.models import Contrato
from pagamentos.models import ConfiguracaoPagamento
from pagamentos.utils import gerar_link_pagamento, gerar_codigo_pix_real, gerar_qr_code_pix
from django.utils import timezone

# Buscar template de vencimento
template = TemplateNotificacao.objects.filter(tipo='VENCIMENTO').first()
if not template:
    print('❌ Template de vencimento não encontrado')
    exit()

print(f'=== TEMPLATE ENCONTRADO ===')
print(f'Nome: {template.nome}')
print(f'Tipo: {template.tipo}')
print(f'Corpo: {template.corpo_template[:200]}...')

# Buscar contrato para teste
contrato = Contrato.objects.filter(status='ATIVO').first()
if not contrato:
    print('❌ Nenhum contrato ativo encontrado')
    exit()

print(f'\n=== CONTRATO PARA TESTE ===')
print(f'Número: {contrato.numero}')
print(f'Inquilino: {contrato.inquilino.nome}')
print(f'Valor: R$ {contrato.valor_aluguel}')

# Buscar parcela pendente
parcela_pendente = contrato.parcelas.filter(status='PENDENTE').first()
if parcela_pendente:
    print(f'Parcela pendente encontrada: {parcela_pendente.id}')
    print(f'Valor total: R$ {parcela_pendente.valor_total}')
    print(f'Vencimento: {parcela_pendente.data_vencimento}')
else:
    print('❌ Nenhuma parcela pendente encontrada')

# Gerar dados PIX
link_pagamento = ''
codigo_pix = ''
qr_code_pix = ''

if parcela_pendente:
    try:
        # Gerar link de pagamento
        link_pagamento = gerar_link_pagamento(parcela_pendente.id) or ''
        print(f'\nLink de pagamento: {link_pagamento}')
        
        # Obter configuração PIX
        config_pix = ConfiguracaoPagamento.get_configuracao()
        print(f'Configuração PIX: {config_pix.pix_chave if config_pix else "Não configurado"}')
        
        # Gerar código PIX
        dados_pix = {
            'chave': config_pix.pix_chave or 'exemplo@email.com',
            'valor': float(parcela_pendente.valor_total),
            'nome_recebedor': config_pix.pix_nome_recebedor or 'SISTEMA IMOBILIARIO',
            'cidade': 'SAO PAULO',
            'identificador': f'PARC{parcela_pendente.id}'
        }
        
        codigo_pix = gerar_codigo_pix_real(dados_pix)
        qr_code_pix = gerar_qr_code_pix(codigo_pix) if codigo_pix else ''
        
        print(f'Código PIX gerado: {len(codigo_pix)} caracteres')
        print(f'QR Code gerado: {len(qr_code_pix)} caracteres')
        
    except Exception as e:
        print(f'❌ Erro ao gerar dados PIX: {e}')

# Criar contexto
dias_restantes = (contrato.data_fim - timezone.now().date()).days

contexto = {
    'inquilino_nome': contrato.inquilino.nome,
    'imovel_endereco': getattr(contrato.imovel, 'endereco_completo', 'N/A'),
    'valor_aluguel': contrato.valor_aluguel,
    'data_vencimento': parcela_pendente.data_vencimento.strftime('%d/%m/%Y') if parcela_pendente else contrato.data_fim.strftime('%d/%m/%Y'),
    'dias_restantes': dias_restantes,
    'link_pagamento': link_pagamento,
    'empresa_nome': 'Sistema Imobiliário',
    'pix': {
        'codigo_pix': codigo_pix,
        'qr_code_base64': qr_code_pix,
        'disponivel': bool(codigo_pix and qr_code_pix)
    }
}

print(f'\n=== CONTEXTO CRIADO ===')
print(f'PIX disponível: {contexto["pix"]["disponivel"]}')
print(f'Link pagamento: {contexto["link_pagamento"]}')
print(f'Código PIX: {len(contexto["pix"]["codigo_pix"])} caracteres')

# Renderizar template
try:
    assunto = template.renderizar_assunto(contexto)
    corpo = template.renderizar_corpo(contexto)
    
    print(f'\n=== TEMPLATE RENDERIZADO ===')
    print(f'Assunto: {assunto}')
    print(f'\nCorpo:')
    print(corpo)
    
except Exception as e:
    print(f'❌ Erro ao renderizar template: {e}')
    import traceback
    traceback.print_exc()