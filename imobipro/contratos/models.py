from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models import Inquilino
from imoveis.models import Imovel
from saas.mixins import TenantMixin, TenantManager

class Contrato(TenantMixin):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('VENCIDO', 'Vencido'),
        ('RESCINDIDO', 'Rescindido'),
        ('RENOVADO', 'Renovado'),
    ]
    
    TIPO_REAJUSTE_CHOICES = [
        ('IGP-M', 'IGP-M'),
        ('IPCA', 'IPCA'),
        ('INPC', 'INPC'),
        ('FIXO', 'Percentual Fixo'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE)
    inquilino = models.ForeignKey(Inquilino, on_delete=models.CASCADE)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    valor_condominio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_iptu = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dia_vencimento = models.IntegerField(default=10)
    tipo_reajuste = models.CharField(max_length=10, choices=TIPO_REAJUSTE_CHOICES)
    percentual_reajuste = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    periodicidade_reajuste = models.IntegerField(default=12)  # meses
    percentual_honorario = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    caucao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager personalizado para filtrar por tenant
    objects = TenantManager()
    
    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contrato {self.numero} - {self.inquilino.nome}"
    
    @property
    def valor_total_mensal(self):
        return self.valor_aluguel + self.valor_condominio + self.valor_iptu
    
    @property
    def valor_honorario(self):
        return (self.valor_aluguel * self.percentual_honorario) / 100
    
    @property
    def valor_repasse(self):
        return self.valor_aluguel - self.valor_honorario
    
    def precisa_reajuste(self):
        from dateutil.relativedelta import relativedelta
        data_proximo_reajuste = self.data_inicio + relativedelta(months=self.periodicidade_reajuste)
        return timezone.now().date() >= data_proximo_reajuste

class ReajusteContrato(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='reajustes')
    data_reajuste = models.DateField()
    valor_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    valor_novo = models.DecimalField(max_digits=10, decimal_places=2)
    indice_aplicado = models.DecimalField(max_digits=8, decimal_places=4)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Reajuste de Contrato'
        verbose_name_plural = 'Reajustes de Contratos'
        ordering = ['-data_reajuste']
