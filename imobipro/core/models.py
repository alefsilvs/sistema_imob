from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from security.fields import CPFCNPJField, EncryptedCharField
from saas.mixins import TenantMixin, TenantManager

class Pessoa(models.Model):
    TIPO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES)
    cpf_cnpj = CPFCNPJField(unique=True)
    rg_ie = EncryptedCharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()
    endereco = models.TextField()
    cep = models.CharField(max_length=9)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    data_nascimento = models.DateField(null=True, blank=True)
    profissao = models.CharField(max_length=100, blank=True)
    renda = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    banco = EncryptedCharField(max_length=100, blank=True, verbose_name='Banco')
    agencia = EncryptedCharField(max_length=20, blank=True, verbose_name='Agência')
    conta = EncryptedCharField(max_length=30, blank=True, verbose_name='Conta')
    pix = EncryptedCharField(max_length=100, blank=True, verbose_name='Chave PIX')
    observacoes = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class Proprietario(Pessoa, TenantMixin):
    # Manager personalizado para filtrar por tenant
    objects = TenantManager()
    
    class Meta:
        verbose_name = 'Proprietário'
        verbose_name_plural = 'Proprietários'

class Inquilino(Pessoa, TenantMixin):
    fiador = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    renda_comprovada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Manager personalizado para filtrar por tenant
    objects = TenantManager()
    
    class Meta:
        verbose_name = 'Inquilino'
        verbose_name_plural = 'Inquilinos'


# Importar modelos de perfil
from .models_perfil import PerfilUsuario, AbrangenciaPerfil, UsuarioPerfil, LogAlteracaoPerfil
