# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

from rest_framework import serializers
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from imoveis.models import Imovel
from contratos.models import Contrato
from financeiro.models import Parcela, Repasse, NotaFiscal, IPTU, Seguro
from manutencao.models import OrdemServico
from core.models import Inquilino, Proprietario


class DashboardGeralSerializer(serializers.Serializer):
    """
    Serializer para dados gerais do dashboard
    """
    total_imoveis = serializers.IntegerField()
    imoveis_ocupados = serializers.IntegerField()
    imoveis_vagos = serializers.IntegerField()
    taxa_ocupacao = serializers.FloatField()
    receita_mensal = serializers.DecimalField(max_digits=15, decimal_places=2)
    despesas_mensais = serializers.DecimalField(max_digits=15, decimal_places=2)
    lucro_mensal = serializers.DecimalField(max_digits=15, decimal_places=2)
    contratos_ativos = serializers.IntegerField()
    contratos_vencendo = serializers.IntegerField()
    manutencoes_pendentes = serializers.IntegerField()
    data_atualizacao = serializers.DateTimeField()


class ImovelPowerBISerializer(serializers.ModelSerializer):
    """
    Serializer para dados de imóveis no Power BI
    """
    tipo_imovel = serializers.CharField(source='tipo')
    proprietario_nome = serializers.CharField(source='proprietario.nome')
    status_ocupacao = serializers.SerializerMethodField()
    
    class Meta:
        model = Imovel
        fields = [
            'id', 'codigo', 'endereco', 'bairro', 'cidade', 'estado',
            'tipo_imovel', 'proprietario_nome', 'status_ocupacao',
            'area_total', 'quartos', 'banheiros', 'vagas_garagem'
        ]
    
    def get_status_ocupacao(self, obj):
        contrato_ativo = Contrato.objects.filter(
            imovel=obj,
            data_inicio__lte=timezone.now().date(),
            data_fim__gte=timezone.now().date()
        ).first()
        return 'Ocupado' if contrato_ativo else 'Vago'


class FinanceiroPowerBISerializer(serializers.ModelSerializer):
    """Serializer para dados financeiros do Power BI"""
    contrato_numero = serializers.CharField(source='contrato.numero')
    imovel_codigo = serializers.CharField(source='contrato.imovel.codigo')
    inquilino_nome = serializers.CharField(source='contrato.inquilino.nome')
    
    class Meta:
        model = Parcela
        fields = [
            'id', 'numero_parcela', 'data_vencimento', 'valor_total',
            'valor_aluguel', 'valor_condominio', 'valor_iptu', 'valor_seguro',
            'data_pagamento', 'valor_pago', 'status', 'contrato_numero',
            'imovel_codigo', 'inquilino_nome', 'created_at'
        ]


class ContratoPowerBISerializer(serializers.ModelSerializer):
    """
    Serializer para dados de contratos no Power BI
    """
    imovel_codigo = serializers.CharField(source='imovel.codigo')
    imovel_endereco = serializers.CharField(source='imovel.endereco')
    inquilino_nome = serializers.CharField(source='inquilino.nome')
    inquilino_cpf = serializers.CharField(source='inquilino.cpf')
    proprietario_nome = serializers.CharField(source='imovel.proprietario.nome')
    status_contrato = serializers.SerializerMethodField()
    dias_para_vencimento = serializers.SerializerMethodField()
    
    class Meta:
        model = Contrato
        fields = [
            'id', 'numero_contrato', 'imovel_codigo', 'imovel_endereco',
            'inquilino_nome', 'inquilino_cpf', 'proprietario_nome',
            'data_inicio', 'data_fim', 'valor_aluguel', 'valor_deposito',
            'status_contrato', 'dias_para_vencimento', 'criado_em'
        ]
    
    def get_status_contrato(self, obj):
        hoje = timezone.now().date()
        if obj.data_fim < hoje:
            return 'Vencido'
        elif obj.data_inicio <= hoje <= obj.data_fim:
            return 'Ativo'
        else:
            return 'Futuro'
    
    def get_dias_para_vencimento(self, obj):
        hoje = timezone.now().date()
        if obj.data_fim >= hoje:
            return (obj.data_fim - hoje).days
        return 0


class ManutencaoPowerBISerializer(serializers.ModelSerializer):
    """
    Serializer para dados de manutenção no Power BI
    """
    imovel_codigo = serializers.CharField(source='imovel.codigo')
    imovel_endereco = serializers.CharField(source='imovel.endereco')
    proprietario_nome = serializers.CharField(source='imovel.proprietario.nome')
    tempo_resolucao = serializers.SerializerMethodField()
    
    class Meta:
        model = OrdemServico
        fields = [
            'id', 'numero_os', 'imovel_codigo', 'imovel_endereco',
            'proprietario_nome', 'descricao', 'tipo_servico', 'prioridade',
            'status', 'data_abertura', 'data_conclusao', 'tempo_resolucao',
            'observacoes'
        ]
    
    def get_tempo_resolucao(self, obj):
        if obj.data_conclusao and obj.data_abertura:
            return (obj.data_conclusao - obj.data_abertura).days
        return None


class InquilinoPowerBISerializer(serializers.ModelSerializer):
    """
    Serializer para dados de inquilinos no Power BI
    """
    contratos_ativos = serializers.SerializerMethodField()
    valor_total_contratos = serializers.SerializerMethodField()
    
    class Meta:
        model = Inquilino
        fields = [
            'id', 'nome', 'cpf', 'email', 'telefone', 'data_nascimento',
            'profissao', 'renda_mensal', 'contratos_ativos',
            'valor_total_contratos', 'criado_em'
        ]
    
    def get_contratos_ativos(self, obj):
        return obj.contratos.filter(
            data_inicio__lte=timezone.now().date(),
            data_fim__gte=timezone.now().date()
        ).count()
    
    def get_valor_total_contratos(self, obj):
        return obj.contratos.filter(
            data_inicio__lte=timezone.now().date(),
            data_fim__gte=timezone.now().date()
        ).aggregate(total=Sum('valor_aluguel'))['total'] or 0


class ProprietarioPowerBISerializer(serializers.ModelSerializer):
    """
    Serializer para dados de proprietários no Power BI
    """
    total_imoveis = serializers.SerializerMethodField()
    imoveis_ocupados = serializers.SerializerMethodField()
    
    class Meta:
        model = Proprietario
        fields = [
            'id', 'nome', 'cpf', 'email', 'telefone',
            'total_imoveis', 'imoveis_ocupados', 'criado_em'
        ]
    
    def get_total_imoveis(self, obj):
        return obj.imoveis.count()
    
    def get_imoveis_ocupados(self, obj):
        hoje = timezone.now().date()
        return obj.imoveis.filter(
            contratos__data_inicio__lte=hoje,
            contratos__data_fim__gte=hoje
        ).distinct().count()
