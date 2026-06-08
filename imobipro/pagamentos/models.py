from django.db import models
from django.utils import timezone
from financeiro.models import Parcela
import uuid
import hashlib

class PagamentoOnline(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROCESSANDO', 'Processando'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
        ('CANCELADO', 'Cancelado'),
        ('EXPIRADO', 'Expirado'),
    ]
    
    METODO_CHOICES = [
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('BOLETO', 'Boleto Bancário'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
    ]
    
    CATEGORIA_CHOICES = [
        ('INQUILINO', 'Pagamento de Inquilino (Aluguel)'),
        ('ASSINATURA', 'Pagamento de Assinatura (Plano)'),
        ('OUTROS', 'Outros'),
    ]
    
    # Identificação única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_pagamento = models.CharField(max_length=64, unique=True, editable=False)
    
    # Relacionamentos
    parcela = models.ForeignKey(Parcela, on_delete=models.CASCADE, related_name='pagamentos_online')
    
    # Dados do pagamento
    valor_original = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_CHOICES)
    categoria_pagamento = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='INQUILINO', verbose_name='Categoria do Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Dados da transação
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Controle de tempo
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    
    # Dados do pagador
    nome_pagador = models.CharField(max_length=200, blank=True)
    email_pagador = models.EmailField(blank=True)
    telefone_pagador = models.CharField(max_length=20, blank=True)
    
    # Controle de tentativas
    tentativas_processamento = models.IntegerField(default=0)
    ultimo_erro = models.TextField(blank=True)
    
    # Metadados
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pagamento Online'
        verbose_name_plural = 'Pagamentos Online'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_pagamento']),
            models.Index(fields=['status']),
            models.Index(fields=['data_criacao']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.token_pagamento:
            self.token_pagamento = self.gerar_token_pagamento()
        
        if not self.data_expiracao:
            # Expira em 24 horas por padrão
            self.data_expiracao = timezone.now() + timezone.timedelta(hours=24)
        
        super().save(*args, **kwargs)
    
    def gerar_token_pagamento(self):
        """Gera um token único para o pagamento"""
        base_string = f"{self.parcela.id}-{timezone.now().isoformat()}-{uuid.uuid4()}"
        return hashlib.sha256(base_string.encode()).hexdigest()
    
    def __str__(self):
        return f"Pagamento {self.token_pagamento[:8]} - {self.parcela}"
    
    @property
    def esta_expirado(self):
        return timezone.now() > self.data_expiracao
    
    @property
    def pode_processar(self):
        return self.status == 'PENDENTE' and not self.esta_expirado
    
    @property
    def url_pagamento(self):
        from django.urls import reverse
        return reverse('pagamentos:processar_pagamento', kwargs={'token': self.token_pagamento})
    
    def marcar_como_pago(self, valor_pago=None, transaction_id=None, gateway_response=None):
        """Marca o pagamento como aprovado e atualiza a parcela"""
        self.status = 'APROVADO'
        self.data_pagamento = timezone.now()
        self.data_confirmacao = timezone.now()
        
        if valor_pago:
            self.valor_pago = valor_pago
        else:
            self.valor_pago = self.valor_original
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        if gateway_response:
            self.gateway_response = gateway_response
        
        self.save()
        
        # Atualizar a parcela
        self.parcela.status = 'PAGO'
        self.parcela.data_pagamento = self.data_pagamento.date()
        self.parcela.valor_pago = self.valor_pago
        self.parcela.forma_pagamento = self.get_metodo_pagamento_display()
        self.parcela.observacoes = f"Pago via sistema online - Token: {self.token_pagamento}"
        self.parcela.save()
        
        return True
    
    def cancelar(self, motivo=""):
        """Cancela o pagamento"""
        self.status = 'CANCELADO'
        if motivo:
            self.ultimo_erro = motivo
        self.save()
    
    def expirar(self):
        """Marca o pagamento como expirado"""
        if self.status == 'PENDENTE':
            self.status = 'EXPIRADO'
            self.save()

class LogPagamento(models.Model):
    """Log de eventos do pagamento para auditoria"""
    TIPO_CHOICES = [
        ('CRIACAO', 'Criação'),
        ('TENTATIVA', 'Tentativa de Pagamento'),
        ('APROVACAO', 'Aprovação'),
        ('REJEICAO', 'Rejeição'),
        ('CANCELAMENTO', 'Cancelamento'),
        ('EXPIRACAO', 'Expiração'),
        ('ERRO', 'Erro'),
    ]
    
    pagamento = models.ForeignKey(PagamentoOnline, on_delete=models.CASCADE, related_name='logs')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField()
    dados_extras = models.JSONField(blank=True, null=True)
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Pagamento'
        verbose_name_plural = 'Logs de Pagamento'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.tipo} - {self.pagamento.token_pagamento[:8]} - {self.timestamp}"

class ConfiguracaoPagamento(models.Model):
    """Configurações do sistema de pagamento"""
    # PIX
    pix_habilitado = models.BooleanField(default=True)
    pix_chave = models.CharField(max_length=200, blank=True)
    pix_nome_recebedor = models.CharField(max_length=200, blank=True)
    
    # Cartão
    cartao_habilitado = models.BooleanField(default=False)
    gateway_api_key = models.CharField(max_length=500, blank=True)
    gateway_secret_key = models.CharField(max_length=500, blank=True)
    gateway_endpoint = models.URLField(blank=True)
    
    # Boleto
    boleto_habilitado = models.BooleanField(default=False)
    banco_codigo = models.CharField(max_length=10, blank=True)
    agencia = models.CharField(max_length=10, blank=True)
    conta = models.CharField(max_length=20, blank=True)
    
    # Configurações gerais
    tempo_expiracao_horas = models.IntegerField(default=24)
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    taxa_processamento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # URLs de retorno
    url_sucesso = models.URLField(blank=True)
    url_erro = models.URLField(blank=True)
    url_cancelamento = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Pagamento'
        verbose_name_plural = 'Configurações de Pagamento'
    
    def __str__(self):
        return f"Configuração de Pagamento - {self.updated_at.strftime('%d/%m/%Y')}"
    
    @classmethod
    def get_configuracao(cls):
        """Retorna a configuração ativa (singleton)"""
        config, created = cls.objects.get_or_create(pk=1)
        return config


