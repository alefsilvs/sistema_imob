import uuid
import qrcode
from io import BytesIO
import base64
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from .models import HistoricoPagamento, AssinaturaUsuario

class PagamentoService:
    """
    Serviço para gerenciar pagamentos e verificações
    """
    
    @staticmethod
    def gerar_pix_qrcode(valor, descricao="Pagamento ImobilPro"):
        """
        Gera um QR Code PIX para pagamento
        """
        # Dados básicos do PIX (em produção, usar dados reais)
        chave_pix = "admin@imobilpro.com"  # Substitua pela chave PIX real
        
        # Formato simplificado do PIX (em produção, usar formato completo)
        pix_data = f"PIX|{chave_pix}|{valor}|{descricao}"
        
        # Gerar QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(pix_data)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': img_str,
            'pix_data': pix_data,
            'chave_pix': chave_pix,
            'valor': valor
        }
    
    @staticmethod
    def criar_pagamento(assinatura, valor, forma_pagamento='PIX'):
        """
        Cria um registro de pagamento
        """
        pagamento = HistoricoPagamento.objects.create(
            assinatura=assinatura,
            valor=valor,
            forma_pagamento=forma_pagamento,
            referencia_externa=str(uuid.uuid4()),
            data_vencimento=timezone.now() + timedelta(days=1),
            status='PENDENTE'
        )
        return pagamento
    
    @staticmethod
    def verificar_pagamento(referencia_externa):
        """
        Verifica o status de um pagamento
        Em produção, integrar com gateway de pagamento real
        """
        try:
            pagamento = HistoricoPagamento.objects.get(
                referencia_externa=referencia_externa
            )
            
            # Simulação: pagamentos criados há mais de 5 minutos são "aprovados"
            # Em produção, consultar API do gateway
            if pagamento.status == 'PENDENTE':
                tempo_criacao = timezone.now() - pagamento.created_at
                if tempo_criacao.total_seconds() > 300:  # 5 minutos
                    pagamento.status = 'APROVADO'
                    pagamento.data_pagamento = timezone.now()
                    pagamento.save()
                    
                    # Ativar assinatura
                    PagamentoService.ativar_assinatura(pagamento.assinatura)
            
            return pagamento
        except HistoricoPagamento.DoesNotExist:
            return None
    
    @staticmethod
    def ativar_assinatura(assinatura):
        """
        Ativa uma assinatura após pagamento confirmado
        """
        assinatura.status = 'ATIVA'
        assinatura.data_inicio = timezone.now()
        assinatura.data_fim = timezone.now() + timedelta(days=assinatura.plano.duracao_dias)
        assinatura.save()
        
        return assinatura
    
    @staticmethod
    def processar_webhook_pagamento(dados_webhook):
        """
        Processa webhook de confirmação de pagamento
        """
        try:
            referencia = dados_webhook.get('referencia_externa')
            status = dados_webhook.get('status', 'PENDENTE')
            
            pagamento = HistoricoPagamento.objects.get(
                referencia_externa=referencia
            )
            
            pagamento.status = status.upper()
            if status.upper() == 'APROVADO':
                pagamento.data_pagamento = timezone.now()
                PagamentoService.ativar_assinatura(pagamento.assinatura)
            
            pagamento.save()
            return pagamento
            
        except HistoricoPagamento.DoesNotExist:
            return None
    
    @staticmethod
    def cancelar_pagamento(referencia_externa, motivo=""):
        """
        Cancela um pagamento pendente
        """
        try:
            pagamento = HistoricoPagamento.objects.get(
                referencia_externa=referencia_externa,
                status='PENDENTE'
            )
            
            pagamento.status = 'CANCELADO'
            pagamento.observacoes = f"Cancelado: {motivo}"
            pagamento.save()
            
            return pagamento
        except HistoricoPagamento.DoesNotExist:
            return None
    
    @staticmethod
    def verificar_assinaturas_vencidas():
        """
        Verifica e atualiza assinaturas vencidas
        Deve ser executado periodicamente (cron job)
        """
        agora = timezone.now()
        
        # Buscar assinaturas ativas vencidas
        assinaturas_vencidas = AssinaturaUsuario.objects.filter(
            status='ATIVA',
            data_fim__lt=agora
        )
        
        for assinatura in assinaturas_vencidas:
            assinatura.status = 'VENCIDA'
            assinatura.save()
        
        return assinaturas_vencidas.count()
    
    @staticmethod
    def gerar_cobranca_renovacao(assinatura):
        """
        Gera uma nova cobrança para renovação de assinatura
        """
        if assinatura.renovacao_automatica:
            novo_pagamento = PagamentoService.criar_pagamento(
                assinatura=assinatura,
                valor=assinatura.plano.preco,
                forma_pagamento=assinatura.forma_pagamento
            )
            return novo_pagamento
        return None