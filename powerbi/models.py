# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from security.fields import EncryptedTextField


class PowerBIConfig(models.Model):
    """
    Configurações de conexão com Power BI
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Configuração")
    tenant_id = EncryptedTextField(verbose_name="Tenant ID")
    client_id = EncryptedTextField(verbose_name="Client ID")
    client_secret = EncryptedTextField(verbose_name="Client Secret")
    workspace_id = EncryptedTextField(verbose_name="Workspace ID", blank=True, null=True)
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Criado por")
    
    class Meta:
        verbose_name = "Configuração Power BI"
        verbose_name_plural = "Configurações Power BI"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.nome} ({'Ativo' if self.ativo else 'Inativo'})"


class PowerBIDataset(models.Model):
    """
    Datasets disponíveis para Power BI
    """
    TIPO_CHOICES = [
        ('financeiro', 'Dados Financeiros'),
        ('imoveis', 'Dados de Imóveis'),
        ('contratos', 'Dados de Contratos'),
        ('manutencao', 'Dados de Manutenção'),
        ('inquilinos', 'Dados de Inquilinos'),
        ('proprietarios', 'Dados de Proprietários'),
        ('bancas', 'Dados de Bancas de Feira'),
        ('dashboard', 'Dashboard Geral'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name="Nome do Dataset")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    descricao = models.TextField(verbose_name="Descrição")
    endpoint = models.CharField(max_length=200, verbose_name="Endpoint da API")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    requer_autenticacao = models.BooleanField(default=True, verbose_name="Requer Autenticação")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Dataset Power BI"
        verbose_name_plural = "Datasets Power BI"
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class PowerBIAccessLog(models.Model):
    """
    Log de acessos às APIs do Power BI
    """
    dataset = models.ForeignKey(PowerBIDataset, on_delete=models.CASCADE, verbose_name="Dataset")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuário")
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP")
    user_agent = models.TextField(verbose_name="User Agent")
    metodo = models.CharField(max_length=10, verbose_name="Método HTTP")
    status_code = models.IntegerField(verbose_name="Código de Status")
    tempo_resposta = models.FloatField(verbose_name="Tempo de Resposta (ms)")
    registros_retornados = models.IntegerField(default=0, verbose_name="Registros Retornados")
    data_acesso = models.DateTimeField(auto_now_add=True, verbose_name="Data do Acesso")
    
    class Meta:
        verbose_name = "Log de Acesso Power BI"
        verbose_name_plural = "Logs de Acesso Power BI"
        ordering = ['-data_acesso']
    
    def __str__(self):
        return f"{self.dataset.nome} - {self.data_acesso.strftime('%d/%m/%Y %H:%M')}"


class PowerBIToken(models.Model):
    """
    Tokens de acesso para APIs do Power BI
    """
    config = models.ForeignKey(PowerBIConfig, on_delete=models.CASCADE, verbose_name="Configuração")
    token = EncryptedTextField(verbose_name="Token de Acesso")
    refresh_token = EncryptedTextField(verbose_name="Refresh Token", blank=True, null=True)
    expira_em = models.DateTimeField(verbose_name="Expira em")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Token Power BI"
        verbose_name_plural = "Tokens Power BI"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Token {self.config.nome} - {self.expira_em.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expira_em
    
    @property
    def expires_soon(self):
        """Verifica se o token expira em menos de 10 minutos"""
        return (self.expira_em - timezone.now()).total_seconds() < 600
