from django.db import models
from core.models import Proprietario
from security.fields import EncryptedCharField
from saas.mixins import TenantMixin, TenantManager

class Imovel(TenantMixin):
    TIPO_CHOICES = [
        ('CASA', 'Casa'),
        ('APARTAMENTO', 'Apartamento'),
        ('COMERCIAL', 'Comercial'),
        ('TERRENO', 'Terreno'),
        ('CHACARA', 'Chácara'),
        ('KITNET', 'Kitnet'),
        ('SOBRADO', 'Sobrado'),
    ]
    
    FINALIDADE_CHOICES = [
        ('RESIDENCIAL', 'Residencial'),
        ('COMERCIAL', 'Comercial'),
        ('MISTO', 'Misto'),
    ]
    
    STATUS_CHOICES = [
        ('DISPONIVEL', 'Disponível'),
        ('OCUPADO', 'Ocupado'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('INDISPONIVEL', 'Indisponível'),
    ]
    
    # Identificação
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    proprietario = models.ForeignKey(Proprietario, on_delete=models.CASCADE, verbose_name='Proprietário')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    finalidade = models.CharField(max_length=20, choices=FINALIDADE_CHOICES, verbose_name='Finalidade')
    
    # Endereço
    endereco = models.CharField(max_length=200, verbose_name='Endereço')
    numero = models.CharField(max_length=10, verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=100, verbose_name='Bairro')
    cidade = models.CharField(max_length=100, verbose_name='Cidade')
    estado = models.CharField(max_length=2, verbose_name='Estado')
    cep = models.CharField(max_length=9, verbose_name='CEP')
    
    # Características
    area_total = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Área Total (m²)')
    area_construida = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Área Construída (m²)')
    quartos = models.IntegerField(default=0, verbose_name='Quartos')
    banheiros = models.IntegerField(default=0, verbose_name='Banheiros')
    vagas_garagem = models.IntegerField(default=0, verbose_name='Vagas de Garagem')
    
    # Valores
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor do Aluguel')
    valor_condominio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor do Condomínio')
    valor_iptu = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor do IPTU')
    valor_seguro = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor do Seguro')
    
    # Documentação
    inscricao_municipal = EncryptedCharField(max_length=50, blank=True, verbose_name='Inscrição Municipal')
    matricula = EncryptedCharField(max_length=50, blank=True, verbose_name='Matrícula')
    
    # Outros
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    mobiliado = models.BooleanField(default=False, verbose_name='Mobiliado')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISPONIVEL', verbose_name='Status')
    disponivel = models.BooleanField(default=True, verbose_name='Disponível para Locação')
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Manager personalizado para filtrar por tenant
    objects = TenantManager()
    
    class Meta:
        verbose_name = 'Imóvel'
        verbose_name_plural = 'Imóveis'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.endereco}"
    
    @property
    def valor_total_mensal(self):
        return self.valor_aluguel + self.valor_condominio + self.valor_iptu + self.valor_seguro
    
    @property
    def endereco_completo(self):
        endereco = f"{self.endereco}, {self.numero}"
        if self.complemento:
            endereco += f", {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade}/{self.estado}"
        return endereco

class FotoImovel(models.Model):
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='fotos')
    foto = models.ImageField(upload_to='imoveis/fotos/', verbose_name='Foto')
    descricao = models.CharField(max_length=200, blank=True, verbose_name='Descrição')
    principal = models.BooleanField(default=False, verbose_name='Foto Principal')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Foto do Imóvel'
        verbose_name_plural = 'Fotos dos Imóveis'
        ordering = ['-principal', '-created_at']
    
    def __str__(self):
        return f"Foto - {self.imovel.codigo}"
