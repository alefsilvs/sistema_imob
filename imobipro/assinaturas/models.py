from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib

class PlanoAssinatura(models.Model):
    """
    Modelo para definir os planos de assinatura disponíveis
    """
    TIPO_CHOICES = [
        ('MENSAL', 'Mensal'),
        ('ANUAL', 'Anual'),
        ('VITALICIO', 'Vitalício'),
        ('TRIAL', 'Trial Gratuito'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name='Nome do Plano')
    descricao = models.TextField(verbose_name='Descrição')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    duracao_dias = models.IntegerField(verbose_name='Duração em Dias', help_text='0 para vitalício')
    max_imoveis = models.IntegerField(default=0, verbose_name='Máximo de Imóveis', help_text='0 para ilimitado')
    max_contratos = models.IntegerField(default=0, verbose_name='Máximo de Contratos', help_text='0 para ilimitado')
    max_usuarios = models.IntegerField(default=1, verbose_name='Máximo de Usuários')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['preco']
    
    def __str__(self):
        return f'{self.nome} - R$ {self.preco}'

class AssinaturaUsuario(models.Model):
    """
    Modelo para controlar as assinaturas dos usuários
    """
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('SUSPENSA', 'Suspensa'),
        ('TRIAL', 'Trial'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='assinatura')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, verbose_name='Plano')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVA', verbose_name='Status')
    data_inicio = models.DateTimeField(default=timezone.now, verbose_name='Data de Início')
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name='Data de Fim')
    data_cancelamento = models.DateTimeField(null=True, blank=True, verbose_name='Data de Cancelamento')
    renovacao_automatica = models.BooleanField(default=True, verbose_name='Renovação Automática')
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Pago')
    forma_pagamento = models.CharField(max_length=50, blank=True, verbose_name='Forma de Pagamento')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Assinatura do Usuário'
        verbose_name_plural = 'Assinaturas dos Usuários'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f'{self.usuario.username} - {self.plano.nome} ({self.status})'
    
    def save(self, *args, **kwargs):
        if not self.data_fim:
            if self.plano.duracao_dias > 0:
                self.data_fim = self.data_inicio + timedelta(days=self.plano.duracao_dias)
            else:
                # Vitalício - definir uma data muito distante
                self.data_fim = self.data_inicio + timedelta(days=36500)  # 100 anos
        super().save(*args, **kwargs)
    
    @property
    def esta_ativa(self):
        """Verifica se a assinatura está ativa"""
        if self.status in ['CANCELADA', 'SUSPENSA']:
            return False
        if not self.data_fim:
            return False
        return timezone.now() <= self.data_fim
    
    @property
    def dias_restantes(self):
        """Retorna quantos dias restam na assinatura"""
        if not self.esta_ativa or not self.data_fim:
            return 0
        delta = self.data_fim - timezone.now()
        return max(0, delta.days)
    
    @property
    def precisa_renovar(self):
        """Verifica se a assinatura precisa ser renovada em breve (7 dias)"""
        if not self.esta_ativa:
            return True
        return self.dias_restantes <= 7
    
    def renovar(self, novo_plano=None):
        """Renova a assinatura"""
        if novo_plano:
            self.plano = novo_plano
        
        self.data_inicio = timezone.now()
        if self.plano.duracao_dias > 0:
            self.data_fim = self.data_inicio + timedelta(days=self.plano.duracao_dias)
        else:
            self.data_fim = self.data_inicio + timedelta(days=36500)
        
        self.status = 'ATIVA'
        self.save()
    
    def cancelar(self, motivo=''):
        """Cancela a assinatura"""
        self.status = 'CANCELADA'
        self.data_cancelamento = timezone.now()
        self.observacoes += f'\nCancelada em {timezone.now().strftime("%d/%m/%Y %H:%M")}. Motivo: {motivo}'
        self.save()

class HistoricoPagamento(models.Model):
    """
    Histórico de pagamentos das assinaturas
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
        ('CANCELADO', 'Cancelado'),
        ('ESTORNADO', 'Estornado'),
    ]
    
    assinatura = models.ForeignKey(AssinaturaUsuario, on_delete=models.CASCADE, related_name='pagamentos')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    forma_pagamento = models.CharField(max_length=50, verbose_name='Forma de Pagamento')
    referencia_externa = models.CharField(max_length=100, blank=True, verbose_name='Referência Externa')
    data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name='Data do Pagamento')
    data_vencimento = models.DateTimeField(verbose_name='Data de Vencimento')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Histórico de Pagamento'
        verbose_name_plural = 'Histórico de Pagamentos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.assinatura.usuario.username} - R$ {self.valor} ({self.status})'

class PagamentoAssinatura(models.Model):
    """
    Modelo específico para pagamentos de assinaturas/planos
    Separado dos pagamentos de inquilinos (aluguel)
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROCESSANDO', 'Processando'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
        ('CANCELADO', 'Cancelado'),
        ('EXPIRADO', 'Expirado'),
        ('ESTORNADO', 'Estornado'),
    ]
    
    METODO_CHOICES = [
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('BOLETO', 'Boleto Bancário'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
    ]
    
    TIPO_CHOICES = [
        ('ASSINATURA_NOVA', 'Nova Assinatura'),
        ('RENOVACAO', 'Renovação'),
        ('UPGRADE', 'Upgrade de Plano'),
        ('DOWNGRADE', 'Downgrade de Plano'),
    ]
    
    # Identificação única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_pagamento = models.CharField(max_length=64, unique=True, editable=False)
    
    # Relacionamentos
    assinatura = models.ForeignKey(AssinaturaUsuario, on_delete=models.CASCADE, related_name='pagamentos_assinatura')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, verbose_name='Plano')
    
    # Dados do pagamento
    valor_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Original')
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor Pago')
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Desconto')
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_CHOICES, verbose_name='Método de Pagamento')
    tipo_pagamento = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ASSINATURA_NOVA', verbose_name='Tipo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    
    # Dados da transação
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID da Transação')
    gateway_response = models.JSONField(blank=True, null=True, verbose_name='Resposta do Gateway')
    
    # Controle de tempo
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_expiracao = models.DateTimeField(verbose_name='Data de Expiração')
    data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name='Data do Pagamento')
    data_confirmacao = models.DateTimeField(null=True, blank=True, verbose_name='Data de Confirmação')
    
    # Dados do pagador
    nome_pagador = models.CharField(max_length=200, blank=True, verbose_name='Nome do Pagador')
    email_pagador = models.EmailField(blank=True, verbose_name='Email do Pagador')
    telefone_pagador = models.CharField(max_length=20, blank=True, verbose_name='Telefone do Pagador')
    
    # Controle de tentativas
    tentativas_processamento = models.IntegerField(default=0, verbose_name='Tentativas')
    ultimo_erro = models.TextField(blank=True, verbose_name='Último Erro')
    
    # Metadados
    ip_origem = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP de Origem')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    # Período de cobertura
    periodo_inicio = models.DateTimeField(verbose_name='Início do Período')
    periodo_fim = models.DateTimeField(verbose_name='Fim do Período')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pagamento de Assinatura'
        verbose_name_plural = 'Pagamentos de Assinatura'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_pagamento']),
            models.Index(fields=['status']),
            models.Index(fields=['data_criacao']),
            models.Index(fields=['assinatura']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.token_pagamento:
            self.token_pagamento = self.gerar_token_pagamento()
        
        if not self.data_expiracao:
            # Expira em 24 horas por padrão
            self.data_expiracao = timezone.now() + timedelta(hours=24)
        
        super().save(*args, **kwargs)
    
    def gerar_token_pagamento(self):
        """Gera um token único para o pagamento de assinatura"""
        import uuid
        import hashlib
        base_string = f"assinatura-{self.assinatura.id}-{timezone.now().isoformat()}-{uuid.uuid4()}"
        return hashlib.sha256(base_string.encode()).hexdigest()
    
    def __str__(self):
        return f"Pagamento Assinatura {self.token_pagamento[:8]} - {self.assinatura.usuario.username}"
    
    @property
    def valor_final(self):
        """Valor final após desconto"""
        return self.valor_original - self.valor_desconto
    
    @property
    def esta_expirado(self):
        return timezone.now() > self.data_expiracao
    
    @property
    def pode_processar(self):
        return self.status == 'PENDENTE' and not self.esta_expirado
    
    def marcar_como_pago(self, valor_pago=None, transaction_id=None, gateway_response=None):
        """Marca o pagamento como aprovado e ativa/renova a assinatura"""
        self.status = 'APROVADO'
        self.data_pagamento = timezone.now()
        self.data_confirmacao = timezone.now()
        
        if valor_pago:
            self.valor_pago = valor_pago
        else:
            self.valor_pago = self.valor_final
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        if gateway_response:
            self.gateway_response = gateway_response
        
        self.save()
        
        # Ativar/renovar a assinatura
        if self.tipo_pagamento in ['ASSINATURA_NOVA', 'RENOVACAO']:
            self.assinatura.status = 'ATIVA'
            self.assinatura.data_inicio = self.periodo_inicio
            self.assinatura.data_fim = self.periodo_fim
            self.assinatura.valor_pago = self.valor_pago
            self.assinatura.forma_pagamento = self.get_metodo_pagamento_display()
            self.assinatura.save()
        
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

class ConfiguracaoSistema(models.Model):
    """
    Configurações gerais do sistema de assinaturas
    """
    trial_dias = models.IntegerField(default=7, verbose_name='Dias de Trial Gratuito')
    permitir_trial = models.BooleanField(default=True, verbose_name='Permitir Trial')
    bloquear_acesso_vencido = models.BooleanField(default=True, verbose_name='Bloquear Acesso Vencido')
    dias_graca = models.IntegerField(default=3, verbose_name='Dias de Graça após Vencimento')
    email_cobranca = models.EmailField(verbose_name='Email para Cobrança')
    mensagem_bloqueio = models.TextField(
        default='Sua assinatura expirou. Renove para continuar usando o sistema.',
        verbose_name='Mensagem de Bloqueio'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'
    
    def __str__(self):
        return 'Configurações do Sistema de Assinaturas'
    
    def save(self, *args, **kwargs):
        # Garantir que só existe uma configuração
        if not self.pk and ConfiguracaoSistema.objects.exists():
            raise ValueError('Só pode existir uma configuração do sistema')
        super().save(*args, **kwargs)
