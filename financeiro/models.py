from django.db import models
from django.utils import timezone
from contratos.models import Contrato
from core.models import Proprietario
from security.fields import EncryptedCharField, CPFCNPJField

class Parcela(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    TIPO_CHOICES = [
        ('ALUGUEL', 'Aluguel'),
        ('CONDOMINIO', 'Condomínio'),
        ('IPTU', 'IPTU'),
        ('SEGURO', 'Seguro'),
        ('OUTROS', 'Outros'),
    ]
    
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='parcelas')
    numero_parcela = models.IntegerField()
    data_vencimento = models.DateField()
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    valor_condominio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_iptu = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_seguro = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_outros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_juros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_pagamento = models.DateField(null=True, blank=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField(max_length=50, blank=True)
    observacoes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ALUGUEL')
    boleto_gerado = models.BooleanField(default=False)
    codigo_barras = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Parcela'
        verbose_name_plural = 'Parcelas'
        ordering = ['data_vencimento']
        unique_together = ['contrato', 'numero_parcela']
    
    def __str__(self):
        return f"Parcela {self.numero_parcela} - {self.contrato.numero}"
    
    @property
    def valor_total(self):
        return (self.valor_aluguel + self.valor_condominio + self.valor_iptu + 
                self.valor_seguro + self.valor_outros + self.valor_multa + 
                self.valor_juros - self.valor_desconto)
    
    @property
    def esta_vencida(self):
        return self.data_vencimento < timezone.now().date() and self.status == 'PENDENTE'

class Repasse(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PROCESSADO', 'Processado'),
        ('ERRO', 'Erro'),
    ]
    
    proprietario = models.ForeignKey(Proprietario, on_delete=models.CASCADE)
    parcela = models.ForeignKey(Parcela, on_delete=models.CASCADE)
    valor_repasse = models.DecimalField(max_digits=10, decimal_places=2)
    valor_honorario = models.DecimalField(max_digits=10, decimal_places=2)
    data_repasse = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    comprovante = models.CharField(max_length=100, blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Repasse'
        verbose_name_plural = 'Repasses'
        ordering = ['-data_repasse']

class NotaFiscal(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('processando', 'Processando'),
        ('emitida', 'Emitida'),
        ('cancelada', 'Cancelada'),
        ('erro', 'Erro'),
    ]
    
    # Campos básicos
    numero = models.PositiveIntegerField('Número')
    serie = models.PositiveIntegerField('Série', default=1)
    chave_acesso = EncryptedCharField('Chave de Acesso', max_length=44, blank=True, null=True)
    protocolo = models.CharField('Protocolo', max_length=50, blank=True, null=True)
    data_emissao = models.DateTimeField('Data de Emissão', auto_now_add=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='rascunho')
    
    # Dados do cliente
    cliente_nome = models.CharField('Nome/Razão Social', max_length=200)
    cliente_documento = CPFCNPJField('CPF/CNPJ')
    cliente_email = models.EmailField('E-mail', blank=True, null=True)
    cliente_endereco = models.TextField('Endereço', blank=True, null=True)
    cliente_cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    cliente_uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cliente_cep = models.CharField('CEP', max_length=10, blank=True, null=True)
    
    # Dados fiscais
    descricao_servico = models.TextField('Descrição do Serviço')
    valor_servicos = models.DecimalField('Valor dos Serviços', max_digits=10, decimal_places=2)
    base_calculo_iss = models.DecimalField('Base de Cálculo ISS', max_digits=10, decimal_places=2)
    aliquota_iss = models.DecimalField('Alíquota ISS (%)', max_digits=5, decimal_places=2, default=5.0)
    valor_iss = models.DecimalField('Valor ISS', max_digits=10, decimal_places=2)
    valor_total = models.DecimalField('Valor Total', max_digits=10, decimal_places=2)
    
    # Campos para integração com API
    provider_id = models.CharField('ID no Provedor', max_length=100, blank=True, null=True)
    provider_response = models.JSONField('Resposta do Provedor', blank=True, null=True)
    xml_content = models.TextField('Conteúdo XML', blank=True, null=True)
    arquivo_xml = models.FileField('Arquivo XML', upload_to='nfe/xml/', blank=True, null=True)
    arquivo_pdf = models.FileField('Arquivo PDF', upload_to='nfe/pdf/', blank=True, null=True)
    
    # Campos de controle
    tentativas_envio = models.PositiveIntegerField('Tentativas de Envio', default=0)
    ultimo_erro = models.TextField('Último Erro', blank=True, null=True)
    data_cancelamento = models.DateTimeField('Data de Cancelamento', blank=True, null=True)
    motivo_cancelamento = models.TextField('Motivo do Cancelamento', blank=True, null=True)
    
    # Relacionamentos
    parcelas = models.ManyToManyField('Parcela', verbose_name='Parcelas', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Nota Fiscal Eletrônica'
        verbose_name_plural = 'Notas Fiscais Eletrônicas'
        ordering = ['-data_emissao']
        unique_together = ['numero', 'serie']
    
    def __str__(self):
        return f'NFe {self.numero}/{self.serie} - {self.cliente_nome}'
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar próximo número sequencial
            ultimo_numero = NotaFiscal.objects.filter(serie=self.serie).aggregate(
                models.Max('numero')
            )['numero__max'] or 0
            self.numero = ultimo_numero + 1
        
        # Calcular valores
        if self.valor_servicos:
            self.base_calculo_iss = self.valor_servicos
            self.valor_iss = (self.valor_servicos * self.aliquota_iss) / 100
            self.valor_total = self.valor_servicos
        
        super().save(*args, **kwargs)
    
    @property
    def pode_cancelar(self):
        return self.status == 'emitida' and not self.data_cancelamento
    
    @property
    def numero_formatado(self):
        return f"{self.numero:09d}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar próximo número sequencial
            ultimo_numero = NotaFiscal.objects.filter(serie=self.serie).aggregate(
                models.Max('numero')
            )['numero__max'] or 0
            self.numero = ultimo_numero + 1
        
        # Calcular valores
        if self.valor_servicos:
            self.base_calculo_iss = self.valor_servicos
            self.valor_iss = (self.valor_servicos * self.aliquota_iss) / 100
            self.valor_total = self.valor_servicos
        
        super().save(*args, **kwargs)
    
    @property
    def pode_cancelar(self):
        return self.status == 'emitida' and not self.data_cancelamento
    
    @property
    def numero_formatado(self):
        return f"{self.numero:09d}"

class IPTU(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('VENCIDO', 'Vencido'),
        ('PARCELADO', 'Parcelado'),
        ('ISENTO', 'Isento'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('VISTA', 'À Vista'),
        ('PARCELADO', 'Parcelado'),
    ]
    
    imovel = models.ForeignKey('imoveis.Imovel', on_delete=models.CASCADE, related_name='iptus')
    ano_exercicio = models.IntegerField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_desconto_vista = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_vencimento_vista = models.DateField()
    numero_parcelas = models.IntegerField(default=1)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='VISTA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'IPTU'
        verbose_name_plural = 'IPTUs'
        unique_together = ['imovel', 'ano_exercicio']
        ordering = ['-ano_exercicio']
    
    def __str__(self):
        return f"IPTU {self.ano_exercicio} - {self.imovel.codigo}"
    
    @property
    def valor_com_desconto(self):
        if self.forma_pagamento == 'VISTA':
            return self.valor_total - self.valor_desconto_vista
        return self.valor_total
    
    @property
    def valor_parcela(self):
        if self.numero_parcelas > 1:
            return self.valor_total / self.numero_parcelas
        return self.valor_total

class ParcelaIPTU(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('VENCIDO', 'Vencido'),
    ]
    
    iptu = models.ForeignKey(IPTU, on_delete=models.CASCADE, related_name='parcelas_iptu')
    numero_parcela = models.IntegerField()
    data_vencimento = models.DateField()
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_pagamento = models.DateField(null=True, blank=True)
    codigo_barras = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Parcela IPTU'
        verbose_name_plural = 'Parcelas IPTU'
        unique_together = ['iptu', 'numero_parcela']
        ordering = ['numero_parcela']
    
    def __str__(self):
        return f"Parcela {self.numero_parcela}/{self.iptu.numero_parcelas} - IPTU {self.iptu.ano_exercicio}"

class Seguro(models.Model):
    TIPO_CHOICES = [
        ('INCENDIO', 'Seguro Incêndio'),
        ('RESIDENCIAL', 'Seguro Residencial'),
        ('COMERCIAL', 'Seguro Comercial'),
        ('VIDA', 'Seguro de Vida'),
        ('FIANCA', 'Seguro Fiança'),
    ]
    
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
        ('PENDENTE', 'Pendente Renovação'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('MENSAL', 'Mensal'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
    ]
    
    imovel = models.ForeignKey('imoveis.Imovel', on_delete=models.CASCADE, related_name='seguros')
    contrato = models.ForeignKey('contratos.Contrato', on_delete=models.CASCADE, null=True, blank=True, related_name='seguros')
    seguradora = models.CharField(max_length=100)
    tipo_seguro = models.CharField(max_length=20, choices=TIPO_CHOICES)
    numero_apolice = EncryptedCharField(max_length=50, unique=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='MENSAL')
    cobertura = models.TextField()
    franquia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Seguro'
        verbose_name_plural = 'Seguros'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.get_tipo_seguro_display()} - {self.numero_apolice}"
    
    @property
    def dias_para_vencimento(self):
        from datetime import date
        return (self.data_fim - date.today()).days
    
    @property
    def precisa_renovacao(self):
        return self.dias_para_vencimento <= 30

class ParcelaSeguro(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('VENCIDO', 'Vencido'),
    ]
    
    seguro = models.ForeignKey(Seguro, on_delete=models.CASCADE, related_name='parcelas_seguro')
    numero_parcela = models.IntegerField()
    data_vencimento = models.DateField()
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Parcela Seguro'
        verbose_name_plural = 'Parcelas Seguro'
        unique_together = ['seguro', 'numero_parcela']
        ordering = ['data_vencimento']
    
    def __str__(self):
        return f"Parcela {self.numero_parcela} - {self.seguro.numero_apolice}"

class Sangria(models.Model):
    """Modelo para registrar todas as saídas/despesas do sistema"""
    
    CATEGORIA_CHOICES = [
        ('MANUTENCAO', 'Manutenção'),
        ('LIMPEZA', 'Limpeza'),
        ('SEGURANCA', 'Segurança'),
        ('ADMINISTRACAO', 'Administração'),
        ('MARKETING', 'Marketing'),
        ('JURIDICO', 'Jurídico'),
        ('CONTABILIDADE', 'Contabilidade'),
        ('IMPOSTOS', 'Impostos'),
        ('COMBUSTIVEL', 'Combustível'),
        ('ALIMENTACAO', 'Alimentação'),
        ('TRANSPORTE', 'Transporte'),
        ('MATERIAL_ESCRITORIO', 'Material de Escritório'),
        ('TELEFONE_INTERNET', 'Telefone/Internet'),
        ('ENERGIA_ELETRICA', 'Energia Elétrica'),
        ('AGUA_ESGOTO', 'Água/Esgoto'),
        ('SEGUROS', 'Seguros'),
        ('TAXAS_BANCARIAS', 'Taxas Bancárias'),
        ('OUTROS', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
        ('BOLETO', 'Boleto'),
        ('CHEQUE', 'Cheque'),
    ]
    
    # Campos básicos
    descricao = models.CharField('Descrição', max_length=200)
    categoria = models.CharField('Categoria', max_length=30, choices=CATEGORIA_CHOICES)
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Relacionamentos opcionais
    imovel = models.ForeignKey('imoveis.Imovel', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='Imóvel', help_text='Imóvel relacionado à despesa (opcional)')
    contrato = models.ForeignKey('contratos.Contrato', on_delete=models.CASCADE, null=True, blank=True,
                                verbose_name='Contrato', help_text='Contrato relacionado à despesa (opcional)')
    
    # Campos adicionais
    fornecedor = models.CharField('Fornecedor/Beneficiário', max_length=200, blank=True)
    numero_documento = models.CharField('Número do Documento', max_length=50, blank=True,
                                       help_text='Número da nota fiscal, recibo, etc.')
    observacoes = models.TextField('Observações', blank=True)
    
    # Campos de controle
    usuario_criacao = models.ForeignKey('auth.User', on_delete=models.PROTECT, 
                                       verbose_name='Usuário que Criou')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    # Tenant para multi-tenancy
    tenant = models.ForeignKey('saas.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Sangria'
        verbose_name_plural = 'Sangrias'
        ordering = ['-data_vencimento', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'data_vencimento']),
            models.Index(fields=['tenant', 'categoria']),
            models.Index(fields=['tenant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor} ({self.get_categoria_display()})"
    
    @property
    def esta_vencida(self):
        """Verifica se a sangria está vencida"""
        from django.utils import timezone
        return self.data_vencimento < timezone.now().date() and self.status == 'PENDENTE'
    
    @property
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para o vencimento"""
        from django.utils import timezone
        if self.status != 'PENDENTE':
            return None
        delta = self.data_vencimento - timezone.now().date()
        return delta.days
    
    def marcar_como_pago(self, data_pagamento=None, forma_pagamento=None):
        """Marca a sangria como paga"""
        from django.utils import timezone
        self.status = 'PAGO'
        self.data_pagamento = data_pagamento or timezone.now().date()
        if forma_pagamento:
            self.forma_pagamento = forma_pagamento
        self.save()
    
    def cancelar(self):
        """Cancela a sangria"""
        self.status = 'CANCELADO'
        self.save()

