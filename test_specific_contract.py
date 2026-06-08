#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from contratos.models import Contrato
from financeiro.models import Parcela
from notificacoes.models import TemplateNotificacao, Notificacao
from notificacoes.services import WhatsAppService
from pagamentos.models import ConfiguracaoPagamento
from pagamentos.utils import gerar_link_pagamento, gerar_codigo_pix_real, gerar_qr_code_pix
from django.utils import timezone
from datetime import timedelta

print('=== VERIFICANDO CONTRATOS E PARCELAS ===')

# Buscar todos os contratos ativos
contratos = Contrato.objects.filter(status='ATIVO')
for contrato in contratos:
    parcelas_pendentes = contrato.parcelas.filter(status='PENDENTE').count()
    print(f'Contrato {contrato.numero} ({contrato.inquilino.nome}): {parcelas_pendentes} parcelas pendentes')
    
    if parcelas_pendentes > 0:
        parcela = contrato.parcelas.filter(status='PENDENTE').first()
        print(f'  - Parcela {parcela.id}: R$ {parcela.valor_total} - Vence em {parcela.data_vencimento}')

# Buscar contrato com parcela pendente
contrato_com_parcela = None
for contrato in contratos:
    if contrato.parcelas.filter(status='PENDENTE').exists():
        contrato_com_parcela = contrato
        break

if not contrato_com_parcela:
    print('\n❌ Nenhum contrato com parcela pendente encontrado')
    # Criar uma parcela pendente para o contrato TESTE001
    contrato_teste = Contrato.objects.filter(numero='TESTE001').first()
    if contrato_teste:
        print(f'Criando parcela pendente para contrato {contrato_teste.numero}')
        parcela = Parcela.objects.create(
            contrato=contrato_teste,
            numero_parcela=1,
            data_vencimento=timezone.now().date() + timedelta(days=5),
            valor_aluguel=contrato_teste.valor_aluguel,
            status='PENDENTE',
            tipo='ALUGUEL'
        )
        print(f'Parcela criada: {parcela.id}')
        contrato_com_parcela = contrato_teste
    else:
        print('Contrato TESTE001 não encontrado')
        exit()

print(f'\n=== TESTANDO NOTIFICAÇÃO PARA {contrato_com_parcela.numero} ===')

# Buscar template
template = TemplateNotificacao.objects.filter(tipo='VENCIMENTO').first()
if not template:
    print('❌ Template não encontrado')
    exit()

# Buscar parcela pendente
parcela_pendente = contrato_com_parcela.parcelas.filter(status='PENDENTE').first()
print(f'Parcela pendente: {parcela_pendente.id} - R$ {parcela_pendente.valor_total}')

# Gerar dados PIX
link_pagamento = ''
codigo_pix = ''
qr_code_pix = ''

try:
    # Gerar link de pagamento
    link_pagamento = gerar_link_pagamento(parcela_pendente.id) or ''
    print(f'Link de pagamento: {link_pagamento}')
    
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
    
    print(f'Código PIX: {len(codigo_pix)} caracteres')
    print(f'QR Code: {len(qr_code_pix)} caracteres')
    
except Exception as e:
    print(f'❌ Erro ao gerar dados PIX: {e}')

# Criar contexto
dias_restantes = (contrato_com_parcela.data_fim - timezone.now().date()).days

contexto = {
    'inquilino_nome': contrato_com_parcela.inquilino.nome,
    'imovel_endereco': getattr(contrato_com_parcela.imovel, 'endereco_completo', 'N/A'),
    'valor_aluguel': contrato_com_parcela.valor_aluguel,
    'data_vencimento': parcela_pendente.data_vencimento.strftime('%d/%m/%Y'),
    'dias_restantes': dias_restantes,
    'link_pagamento': link_pagamento,
    'empresa_nome': 'Sistema Imobiliário',
    'pix': {
        'codigo_pix': codigo_pix,
        'qr_code_base64': qr_code_pix,
        'disponivel': bool(codigo_pix and qr_code_pix)
    }
}

print(f'\nPIX disponível: {contexto["pix"]["disponivel"]}')

# Renderizar template
assunto = template.renderizar_assunto(contexto)
corpo = template.renderizar_corpo(contexto)

print(f'\n=== MENSAGEM RENDERIZADA ===')
print(f'Assunto: {assunto}')
print(f'\nCorpo (primeiros 500 caracteres):')
print(corpo[:500])
print('...')

# Verificar se tem telefone
if contrato_com_parcela.inquilino.telefone:
    print(f'\n=== ENVIANDO WHATSAPP PARA {contrato_com_parcela.inquilino.telefone} ===')
    
    # Criar notificação
    notificacao = Notificacao.objects.create(
        template=template,
        inquilino=contrato_com_parcela.inquilino,
        contrato=contrato_com_parcela,
        canal='WHATSAPP',
        destinatario=contrato_com_parcela.inquilino.telefone,
        assunto=assunto,
        corpo=corpo,
        prioridade='ALTA',
        usuario_id=1
    )
    
    # Enviar via WhatsApp
    whatsapp_service = WhatsAppService()
    resultado = whatsapp_service.send_message(
        to_number=contrato_com_parcela.inquilino.telefone,
        message=corpo,
        media_base64=qr_code_pix if qr_code_pix else None,
        media_type='image'
    )
    
    if resultado.get('success', False):
        notificacao.status = 'ENVIADA'
        notificacao.data_envio = timezone.now()
        notificacao.tracking_id = resultado.get('message_id')
        print('✅ Notificação enviada com sucesso!')
    else:
        notificacao.status = 'ERRO'
        notificacao.erro_envio = resultado.get('error', 'Erro desconhecido')
        print(f'❌ Erro ao enviar: {resultado.get("error", "Erro desconhecido")}')
    
    notificacao.save()
    print(f'Notificação salva com ID: {notificacao.id}')
else:
    print('❌ Inquilino não tem telefone cadastrado')