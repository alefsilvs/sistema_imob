# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Sistema de Indicadores de Gestão - Inspirado no Gestor Fácil
Funcionalidades: Indicadores de inadimplência, imobiliário e financeiro
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from datetime import datetime, timedelta


class IndicadorGeral(models.Model):
    """
    Modelo base para indicadores gerais do sistema
    """
    TIPOS_INDICADOR = [
        ('inadimplencia', 'Inadimplência'),
        ('imobiliario', 'Imobiliário'),
        ('financeiro', 'Financeiro'),
        ('ocupacao', 'Ocupação'),
        ('manutencao', 'Manutenção'),
        ('vendas', 'Vendas'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name='Nome do Indicador')
    tipo = models.CharField(max_length=20, choices=TIPOS_INDICADOR, verbose_name='Tipo')
    descricao = models.TextField(verbose_name='Descrição')
    valor_atual = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor Atual')
    valor_meta = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Meta')
    unidade = models.CharField(max_length=20, default='%', verbose_name='Unidade')
    data_calculo = models.DateTimeField(auto_now=True, verbose_name='Data do Cálculo')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Indicador Geral'
        verbose_name_plural = 'Indicadores Gerais'
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.nome}: {self.valor_atual}{self.unidade}"
    
    @property
    def percentual_meta(self):
        """Calcula o percentual atingido da meta"""
        if self.valor_meta > 0:
            return (self.valor_atual / self.valor_meta) * 100
        return 0
    
    @property
    def status_meta(self):
        """Retorna o status em relação à meta"""
        percentual = self.percentual_meta
        if percentual >= 100:
            return 'atingida'
        elif percentual >= 80:
            return 'proxima'
        elif percentual >= 50:
            return 'media'
        else:
            return 'baixa'


class IndicadorInadimplencia(models.Model):
    """
    Indicadores específicos de inadimplência
    """
    data_referencia = models.DateField(verbose_name='Data de Referência')
    total_contratos = models.IntegerField(default=0, verbose_name='Total de Contratos')
    contratos_em_dia = models.IntegerField(default=0, verbose_name='Contratos em Dia')
    contratos_inadimplentes = models.IntegerField(default=0, verbose_name='Contratos Inadimplentes')
    valor_total_devido = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor Total Devido')
    valor_inadimplente = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Valor Inadimplente')
    percentual_inadimplencia = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='% Inadimplência')
    ticket_medio_inadimplencia = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Ticket Médio Inadimplência')
    
    class Meta:
        verbose_name = 'Indicador de Inadimplência'
        verbose_name_plural = 'Indicadores de Inadimplência'
        ordering = ['-data_referencia']
        unique_together = ['data_referencia']
    
    def __str__(self):
        return f"Inadimplência {self.data_referencia.strftime('%m/%Y')}: {self.percentual_inadimplencia}%"
    
    def calcular_indicadores(self):
        """Calcula automaticamente os indicadores de inadimplência"""
        from contratos.models import Contrato
        from financeiro.models import Parcela
        
        # Buscar contratos ativos
        contratos_ativos = Contrato.objects.filter(
            status='ativo',
            data_inicio__lte=self.data_referencia
        )
        
        self.total_contratos = contratos_ativos.count()
        
        # Buscar parcelas vencidas até a data de referência
        parcelas_vencidas = Parcela.objects.filter(
            contrato__in=contratos_ativos,
            data_vencimento__lte=self.data_referencia,
            status='pendente'
        )
        
        # Contratos com parcelas vencidas
        contratos_inadimplentes_ids = parcelas_vencidas.values_list('contrato_id', flat=True).distinct()
        self.contratos_inadimplentes = len(set(contratos_inadimplentes_ids))
        self.contratos_em_dia = self.total_contratos - self.contratos_inadimplentes
        
        # Valores
        # Calcular valor inadimplente somando todos os componentes das parcelas vencidas
        valor_inadimplente_data = parcelas_vencidas.aggregate(
            aluguel=Sum('valor_aluguel'),
            condominio=Sum('valor_condominio'),
            iptu=Sum('valor_iptu'),
            seguro=Sum('valor_seguro'),
            outros=Sum('valor_outros'),
            multa=Sum('valor_multa'),
            juros=Sum('valor_juros'),
            desconto=Sum('valor_desconto')
        )
        
        self.valor_inadimplente = (
            (valor_inadimplente_data['aluguel'] or Decimal('0')) +
            (valor_inadimplente_data['condominio'] or Decimal('0')) +
            (valor_inadimplente_data['iptu'] or Decimal('0')) +
            (valor_inadimplente_data['seguro'] or Decimal('0')) +
            (valor_inadimplente_data['outros'] or Decimal('0')) +
            (valor_inadimplente_data['multa'] or Decimal('0')) +
            (valor_inadimplente_data['juros'] or Decimal('0')) -
            (valor_inadimplente_data['desconto'] or Decimal('0'))
        )
        
        # Calcular valor total devido somando todos os componentes das parcelas
        valor_total_data = Parcela.objects.filter(
            contrato__in=contratos_ativos,
            data_vencimento__lte=self.data_referencia
        ).aggregate(
            aluguel=Sum('valor_aluguel'),
            condominio=Sum('valor_condominio'),
            iptu=Sum('valor_iptu'),
            seguro=Sum('valor_seguro'),
            outros=Sum('valor_outros'),
            multa=Sum('valor_multa'),
            juros=Sum('valor_juros'),
            desconto=Sum('valor_desconto')
        )
        
        self.valor_total_devido = (
            (valor_total_data['aluguel'] or Decimal('0')) +
            (valor_total_data['condominio'] or Decimal('0')) +
            (valor_total_data['iptu'] or Decimal('0')) +
            (valor_total_data['seguro'] or Decimal('0')) +
            (valor_total_data['outros'] or Decimal('0')) +
            (valor_total_data['multa'] or Decimal('0')) +
            (valor_total_data['juros'] or Decimal('0')) -
            (valor_total_data['desconto'] or Decimal('0'))
        )
        
        # Percentuais
        if self.total_contratos > 0:
            self.percentual_inadimplencia = (self.contratos_inadimplentes / self.total_contratos) * 100
        
        if self.contratos_inadimplentes > 0:
            self.ticket_medio_inadimplencia = self.valor_inadimplente / self.contratos_inadimplentes
        
        self.save()


class IndicadorImobiliario(models.Model):
    """
    Indicadores específicos do setor imobiliário
    """
    data_referencia = models.DateField(verbose_name='Data de Referência')
    total_imoveis = models.IntegerField(default=0, verbose_name='Total de Imóveis')
    imoveis_ocupados = models.IntegerField(default=0, verbose_name='Imóveis Ocupados')
    imoveis_vagos = models.IntegerField(default=0, verbose_name='Imóveis Vagos')
    imoveis_manutencao = models.IntegerField(default=0, verbose_name='Imóveis em Manutenção')
    taxa_ocupacao = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Taxa de Ocupação (%)')
    valor_medio_aluguel = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Médio Aluguel')
    tempo_medio_locacao = models.IntegerField(default=0, verbose_name='Tempo Médio Locação (dias)')
    novos_contratos_mes = models.IntegerField(default=0, verbose_name='Novos Contratos no Mês')
    contratos_encerrados_mes = models.IntegerField(default=0, verbose_name='Contratos Encerrados no Mês')
    
    class Meta:
        verbose_name = 'Indicador Imobiliário'
        verbose_name_plural = 'Indicadores Imobiliários'
        ordering = ['-data_referencia']
        unique_together = ['data_referencia']
    
    def __str__(self):
        return f"Imobiliário {self.data_referencia.strftime('%m/%Y')}: {self.taxa_ocupacao}% ocupação"
    
    def calcular_indicadores(self):
        """Calcula automaticamente os indicadores imobiliários"""
        from imoveis.models import Imovel
        from contratos.models import Contrato
        
        # Total de imóveis
        self.total_imoveis = Imovel.objects.filter(disponivel=True).count()
        
        # Imóveis por status
        self.imoveis_ocupados = Imovel.objects.filter(
            status='OCUPADO',
            disponivel=True
        ).count()
        
        self.imoveis_vagos = Imovel.objects.filter(
            status='DISPONIVEL',
            disponivel=True
        ).count()
        
        self.imoveis_manutencao = Imovel.objects.filter(
            status='MANUTENCAO',
            disponivel=True
        ).count()
        
        # Taxa de ocupação
        if self.total_imoveis > 0:
            self.taxa_ocupacao = (self.imoveis_ocupados / self.total_imoveis) * 100
        
        # Valor médio do aluguel
        contratos_ativos = Contrato.objects.filter(
            status='ativo',
            data_inicio__lte=self.data_referencia
        )
        
        if contratos_ativos.exists():
            self.valor_medio_aluguel = contratos_ativos.aggregate(
                media=Avg('valor_aluguel')
            )['media'] or Decimal('0')
        
        # Novos contratos no mês
        inicio_mes = self.data_referencia.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        self.novos_contratos_mes = Contrato.objects.filter(
            data_inicio__range=[inicio_mes, fim_mes]
        ).count()
        
        self.contratos_encerrados_mes = Contrato.objects.filter(
            data_fim__range=[inicio_mes, fim_mes],
            status='encerrado'
        ).count()
        
        self.save()


class IndicadorFinanceiro(models.Model):
    """
    Indicadores específicos financeiros
    """
    data_referencia = models.DateField(verbose_name='Data de Referência')
    receita_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Receita Total')
    receita_alugueis = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Receita Aluguéis')
    receita_taxas = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Receita Taxas')
    despesa_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Despesa Total')
    despesa_manutencao = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Despesa Manutenção')
    despesa_administrativa = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Despesa Administrativa')
    lucro_liquido = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Lucro Líquido')
    margem_lucro = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Margem de Lucro (%)')
    ticket_medio_receita = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Ticket Médio Receita')
    
    class Meta:
        verbose_name = 'Indicador Financeiro'
        verbose_name_plural = 'Indicadores Financeiros'
        ordering = ['-data_referencia']
        unique_together = ['data_referencia']
    
    def __str__(self):
        return f"Financeiro {self.data_referencia.strftime('%m/%Y')}: R$ {self.receita_total}"
    
    def calcular_indicadores(self):
        """Calcula automaticamente os indicadores financeiros"""
        from financeiro.models import Parcela, Repasse
        from manutencao.models import OrdemServico
        
        # Período do mês
        inicio_mes = self.data_referencia.replace(day=1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Receitas
        parcelas_pagas = Parcela.objects.filter(
            data_pagamento__range=[inicio_mes, fim_mes],
            status='pago'
        )
        
        # Calcular receitas baseado nos valores das parcelas pagas
        receita_alugueis = Decimal('0')
        receita_taxas = Decimal('0')
        
        for parcela in parcelas_pagas:
            receita_alugueis += parcela.valor_aluguel
            receita_taxas += (parcela.valor_condominio + parcela.valor_iptu + 
                            parcela.valor_seguro + parcela.valor_outros)
        
        self.receita_alugueis = receita_alugueis
        self.receita_taxas = receita_taxas
        
        self.receita_total = self.receita_alugueis + self.receita_taxas
        
        # Despesas
        self.despesa_manutencao = OrdemServico.objects.filter(
            data_conclusao__range=[inicio_mes, fim_mes],
            status='concluida'
        ).aggregate(total=Sum('valor_final'))['total'] or Decimal('0')
        
        # Repasses (despesas administrativas)
        self.despesa_administrativa = Repasse.objects.filter(
            data_repasse__range=[inicio_mes, fim_mes]
        ).aggregate(total=Sum('valor_repasse'))['total'] or Decimal('0')
        
        self.despesa_total = self.despesa_manutencao + self.despesa_administrativa
        
        # Lucro
        self.lucro_liquido = self.receita_total - self.despesa_total
        
        if self.receita_total > 0:
            self.margem_lucro = (self.lucro_liquido / self.receita_total) * 100
        
        # Ticket médio
        if parcelas_pagas.count() > 0:
            self.ticket_medio_receita = self.receita_total / parcelas_pagas.count()
        
        self.save()


class DashboardIndicadores(models.Model):
    """
    Dashboard consolidado de indicadores
    """
    data_referencia = models.DateField(verbose_name='Data de Referência')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    configuracao = models.JSONField(default=dict, verbose_name='Configuração do Dashboard')
    ultima_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    
    class Meta:
        verbose_name = 'Dashboard de Indicadores'
        verbose_name_plural = 'Dashboards de Indicadores'
        unique_together = ['data_referencia', 'usuario']
    
    def __str__(self):
        return f"Dashboard {self.usuario.username} - {self.data_referencia.strftime('%m/%Y')}"
    
    def atualizar_todos_indicadores(self):
        """Atualiza todos os indicadores para a data de referência"""
        # Inadimplência
        inadimplencia, created = IndicadorInadimplencia.objects.get_or_create(
            data_referencia=self.data_referencia
        )
        inadimplencia.calcular_indicadores()
        
        # Imobiliário
        imobiliario, created = IndicadorImobiliario.objects.get_or_create(
            data_referencia=self.data_referencia
        )
        imobiliario.calcular_indicadores()
        
        # Financeiro
        financeiro, created = IndicadorFinanceiro.objects.get_or_create(
            data_referencia=self.data_referencia
        )
        financeiro.calcular_indicadores()
        
        return {
            'inadimplencia': inadimplencia,
            'imobiliario': imobiliario,
            'financeiro': financeiro
        }