from django.db import models
from imoveis.models import Imovel
from contratos.models import Contrato

class Fornecedor(models.Model):
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=15)
    email = models.EmailField()
    endereco = models.TextField()
    especialidade = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
    
    def __str__(self):
        return self.nome

class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    RESPONSAVEL_CHOICES = [
        ('INQUILINO', 'Inquilino'),
        ('PROPRIETARIO', 'Proprietário'),
        ('IMOBILIARIA', 'Imobiliária'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.TextField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_agendamento = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    valor_orcamento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    responsavel_pagamento = models.CharField(max_length=20, choices=RESPONSAVEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ordem de Serviço'
        verbose_name_plural = 'Ordens de Serviço'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OS {self.numero} - {self.imovel.codigo}"
