from django.urls import reverse
from django.utils import timezone
from .models import PagamentoOnline, ConfiguracaoPagamento
from financeiro.models import Parcela
import logging
import qrcode
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

def criar_pagamento_online(parcela_id, metodo_preferido='PIX'):
    """
    Cria um pagamento online para uma parcela específica
    
    Args:
        parcela_id: ID da parcela
        metodo_preferido: Método de pagamento preferido
    
    Returns:
        PagamentoOnline: Objeto do pagamento criado
    """
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        
        # Verificar se já existe um pagamento pendente para esta parcela
        pagamento_existente = PagamentoOnline.objects.filter(
            parcela=parcela,
            status__in=['PENDENTE', 'PROCESSANDO']
        ).first()
        
        if pagamento_existente and not pagamento_existente.esta_expirado:
            return pagamento_existente
        
        # Criar novo pagamento
        config = ConfiguracaoPagamento.get_configuracao()
        
        pagamento = PagamentoOnline.objects.create(
            parcela=parcela,
            valor_original=parcela.valor_total,
            metodo_pagamento=metodo_preferido,
            data_expiracao=timezone.now() + timezone.timedelta(hours=config.tempo_expiracao_horas)
        )
        
        logger.info(f"Pagamento online criado: {pagamento.token_pagamento} para parcela {parcela.id}")
        return pagamento
        
    except Parcela.DoesNotExist:
        logger.error(f"Parcela {parcela_id} não encontrada")
        return None

def gerar_qr_code_base64(data, size=10, border=4):
    """
    Gera um QR code em formato base64
    
    Args:
        data: Dados para o QR code (string)
        size: Tamanho do QR code (default: 10)
        border: Borda do QR code (default: 4)
    
    Returns:
        str: QR code em formato base64
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        return qr_code_base64
        
    except Exception as e:
        logger.error(f"Erro ao gerar QR code: {str(e)}")
        return None

def gerar_qr_code_pix(codigo_pix):
    """
    Gera QR code para código PIX
    
    Args:
        codigo_pix: Código PIX para gerar o QR code
    
    Returns:
        str: QR code em formato base64
    """
    return gerar_qr_code_base64(codigo_pix, size=8, border=2)

def gerar_qr_code_link_pagamento(link_pagamento):
    """
    Gera QR code para link de pagamento
    
    Args:
        link_pagamento: URL do link de pagamento
    
    Returns:
        str: QR code em formato base64
    """
    return gerar_qr_code_base64(link_pagamento, size=6, border=2)

def gerar_codigo_pix_real(dados_pix):
    """
    Gera código PIX real seguindo o padrão EMV
    
    Args:
        dados_pix: Dicionário com dados do PIX
    
    Returns:
        str: Código PIX formatado
    """
    try:
        # Implementação básica do padrão EMV para PIX
        # Em produção, usar biblioteca específica como python-pix
        
        payload = ""
        
        # Payload Format Indicator
        payload += "0014BR.GOV.BCB.PIX"
        
        # Merchant Account Information
        chave = dados_pix.get('chave', '')
        if chave:
            merchant_info = f"0014BR.GOV.BCB.PIX01{len(chave):02d}{chave}"
            payload += f"26{len(merchant_info):02d}{merchant_info}"
        
        # Merchant Category Code
        payload += "52040000"
        
        # Transaction Currency
        payload += "5303986"
        
        # Transaction Amount
        valor = f"{float(dados_pix.get('valor', 0)):.2f}"
        payload += f"54{len(valor):02d}{valor}"
        
        # Country Code
        payload += "5802BR"
        
        # Merchant Name
        nome = dados_pix.get('nome_recebedor', 'PAGAMENTO')[:25]
        payload += f"59{len(nome):02d}{nome}"
        
        # Merchant City
        cidade = dados_pix.get('cidade', 'SAO PAULO')[:15]
        payload += f"60{len(cidade):02d}{cidade}"
        
        # Additional Data Field Template
        identificador = dados_pix.get('identificador', '')[:25]
        if identificador:
            additional_data = f"05{len(identificador):02d}{identificador}"
            payload += f"62{len(additional_data):02d}{additional_data}"
        
        # CRC16 (simplificado)
        payload += "6304"
        crc = calcular_crc16(payload)
        payload += f"{crc:04X}"
        
        return payload
        
    except Exception as e:
        logger.error(f"Erro ao gerar código PIX real: {str(e)}")
        # Fallback para código simulado
        pix_string = f"{dados_pix['chave']}|{dados_pix['valor']}|{dados_pix['identificador']}"
        return base64.b64encode(pix_string.encode()).decode()[:50]

def calcular_crc16(payload):
    """
    Calcula CRC16 para código PIX (implementação simplificada)
    """
    try:
        # Implementação básica do CRC16
        # Em produção, usar biblioteca específica
        crc = 0xFFFF
        for byte in payload.encode('utf-8'):
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc
    except Exception as e:
        logger.error(f"Erro ao calcular CRC16: {str(e)}")
        return 0x0000

def gerar_link_pagamento(parcela_id, metodo_preferido='PIX'):
    """
    Gera um link de pagamento para uma parcela
    
    Args:
        parcela_id: ID da parcela
        metodo_preferido: Método de pagamento preferido
    
    Returns:
        str: URL completa do pagamento ou None se houver erro
    """
    pagamento = criar_pagamento_online(parcela_id, metodo_preferido)
    
    if pagamento:
        # Gerar URL completa
        from django.contrib.sites.models import Site
        from django.conf import settings
        
        try:
            # Tentar obter o domínio do site
            if hasattr(settings, 'SITE_URL'):
                base_url = settings.SITE_URL
            else:
                site = Site.objects.get_current()
                protocol = 'https' if getattr(settings, 'USE_HTTPS', False) else 'http'
                base_url = f"{protocol}://{site.domain}"
        except:
            # Fallback para localhost em desenvolvimento
            base_url = "http://localhost:8000"
        
        relative_url = reverse('pagamentos:pagamento', kwargs={'token': pagamento.token_pagamento})
        return f"{base_url}{relative_url}"
    
    return None


def processar_confirmacao_automatica(token_pagamento, dados_confirmacao):
    """
    Processa confirmação automática de pagamento
    
    Args:
        token_pagamento: Token do pagamento
        dados_confirmacao: Dados da confirmação (dict)
    
    Returns:
        bool: True se processado com sucesso
    """
    try:
        pagamento = PagamentoOnline.objects.get(token_pagamento=token_pagamento)
        
        if pagamento.status != 'PROCESSANDO':
            logger.warning(f"Tentativa de confirmar pagamento {token_pagamento} com status {pagamento.status}")
            return False
        
        # Marcar como pago
        pagamento.marcar_como_pago(
            valor_pago=dados_confirmacao.get('valor_pago'),
            transaction_id=dados_confirmacao.get('transaction_id'),
            gateway_response=dados_confirmacao
        )
        
        logger.info(f"Pagamento {token_pagamento} confirmado automaticamente")
        return True
        
    except PagamentoOnline.DoesNotExist:
        logger.error(f"Pagamento {token_pagamento} não encontrado")
        return False
    except Exception as e:
        logger.error(f"Erro ao processar confirmação automática: {str(e)}")
        return False

def verificar_pagamentos_expirados():
    """
    Verifica e marca pagamentos expirados
    
    Returns:
        int: Número de pagamentos expirados
    """
    try:
        pagamentos_pendentes = PagamentoOnline.objects.filter(
            status='PENDENTE',
            data_expiracao__lt=timezone.now()
        )
        
        count = 0
        for pagamento in pagamentos_pendentes:
            pagamento.expirar()
            count += 1
        
        if count > 0:
            logger.info(f"{count} pagamentos marcados como expirados")
        
        return count
        
    except Exception as e:
        logger.error(f"Erro ao verificar pagamentos expirados: {str(e)}")
        return 0

def obter_estatisticas_pagamentos():
    """
    Obtém estatísticas dos pagamentos online
    
    Returns:
        dict: Estatísticas dos pagamentos
    """
    try:
        from django.db.models import Count, Sum, Q
        
        stats = {
            'total_pagamentos': PagamentoOnline.objects.count(),
            'pagamentos_aprovados': PagamentoOnline.objects.filter(status='APROVADO').count(),
            'pagamentos_pendentes': PagamentoOnline.objects.filter(status='PENDENTE').count(),
            'pagamentos_rejeitados': PagamentoOnline.objects.filter(status='REJEITADO').count(),
            'valor_total_aprovado': PagamentoOnline.objects.filter(
                status='APROVADO'
            ).aggregate(total=Sum('valor_pago'))['total'] or 0,
            'metodos_mais_usados': PagamentoOnline.objects.filter(
                status='APROVADO'
            ).values('metodo_pagamento').annotate(
                count=Count('metodo_pagamento')
            ).order_by('-count')[:5]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return {}

def simular_pagamento_aprovado(token_pagamento):
    """
    Simula aprovação de pagamento (para testes)
    
    Args:
        token_pagamento: Token do pagamento
    
    Returns:
        bool: True se simulado com sucesso
    """
    try:
        pagamento = PagamentoOnline.objects.get(token_pagamento=token_pagamento)
        
        if pagamento.status not in ['PENDENTE', 'PROCESSANDO']:
            return False
        
        # Simular dados de aprovação
        dados_simulacao = {
            'tipo': 'SIMULACAO',
            'transaction_id': f'SIM_{pagamento.token_pagamento[:10]}',
            'simulado_em': timezone.now().isoformat()
        }
        
        pagamento.marcar_como_pago(
            transaction_id=dados_simulacao['transaction_id'],
            gateway_response=dados_simulacao
        )
        
        logger.info(f"Pagamento {token_pagamento} simulado como aprovado")
        return True
        
    except PagamentoOnline.DoesNotExist:
        logger.error(f"Pagamento {token_pagamento} não encontrado para simulação")
        return False
    except Exception as e:
        logger.error(f"Erro ao simular pagamento: {str(e)}")
        return False

def validar_configuracao_pagamento():
    """
    Valida se as configurações de pagamento estão corretas
    
    Returns:
        dict: Resultado da validação
    """
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        
        validacao = {
            'valido': True,
            'erros': [],
            'avisos': []
        }
        
        # Verificar PIX
        if config.pix_habilitado:
            if not config.pix_chave:
                validacao['erros'].append('PIX habilitado mas chave PIX não configurada')
                validacao['valido'] = False
            if not config.pix_nome_recebedor:
                validacao['avisos'].append('Nome do recebedor PIX não configurado')
        
        # Verificar Cartão
        if config.cartao_habilitado:
            if not config.gateway_api_key:
                validacao['erros'].append('Cartão habilitado mas API key do gateway não configurada')
                validacao['valido'] = False
            if not config.gateway_endpoint:
                validacao['erros'].append('Cartão habilitado mas endpoint do gateway não configurado')
                validacao['valido'] = False
        
        # Verificar Boleto
        if config.boleto_habilitado:
            if not all([config.banco_codigo, config.agencia, config.conta]):
                validacao['erros'].append('Boleto habilitado mas dados bancários incompletos')
                validacao['valido'] = False
        
        # Verificar se pelo menos um método está habilitado
        if not any([config.pix_habilitado, config.cartao_habilitado, config.boleto_habilitado]):
            validacao['erros'].append('Nenhum método de pagamento está habilitado')
            validacao['valido'] = False
        
        return validacao
        
    except Exception as e:
        logger.error(f"Erro ao validar configuração: {str(e)}")
        return {
            'valido': False,
            'erros': [f'Erro interno: {str(e)}'],
            'avisos': []
        }