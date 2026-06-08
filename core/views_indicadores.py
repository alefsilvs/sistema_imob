# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Views para Indicadores de Gestão - Inspirado no Gestor Fácil
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from .models_indicadores import (
    IndicadorGeral, IndicadorInadimplencia, 
    IndicadorImobiliario, IndicadorFinanceiro, 
    DashboardIndicadores
)
from .models_perfil import UsuarioPerfil


@login_required
def dashboard_indicadores(request):
    """
    Dashboard principal de indicadores - Similar ao Gestor Fácil
    """
    # Verificar permissão
    if not request.user.perfil_usuario.tem_permissao('relatorios', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar os indicadores.')
        return redirect('core:dashboard')
    
    # Data de referência (mês atual por padrão)
    data_referencia = request.GET.get('data_referencia')
    if data_referencia:
        try:
            data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
        except ValueError:
            data_referencia = timezone.now().date()
    else:
        data_referencia = timezone.now().date()
    
    # Buscar ou criar dashboard do usuário
    dashboard, created = DashboardIndicadores.objects.get_or_create(
        data_referencia=data_referencia,
        usuario=request.user
    )
    
    # Atualizar indicadores se necessário
    if created or request.GET.get('atualizar') == '1':
        indicadores = dashboard.atualizar_todos_indicadores()
    else:
        # Buscar indicadores existentes
        try:
            inadimplencia = IndicadorInadimplencia.objects.get(data_referencia=data_referencia)
        except IndicadorInadimplencia.DoesNotExist:
            inadimplencia = None
        
        try:
            imobiliario = IndicadorImobiliario.objects.get(data_referencia=data_referencia)
        except IndicadorImobiliario.DoesNotExist:
            imobiliario = None
        
        try:
            financeiro = IndicadorFinanceiro.objects.get(data_referencia=data_referencia)
        except IndicadorFinanceiro.DoesNotExist:
            financeiro = None
        
        indicadores = {
            'inadimplencia': inadimplencia,
            'imobiliario': imobiliario,
            'financeiro': financeiro
        }
    
    # Indicadores gerais
    indicadores_gerais = IndicadorGeral.objects.filter(ativo=True).order_by('tipo', 'nome')
    
    # Dados para gráficos (últimos 6 meses)
    data_inicio = data_referencia.replace(day=1) - timedelta(days=180)
    historico_inadimplencia = IndicadorInadimplencia.objects.filter(
        data_referencia__gte=data_inicio,
        data_referencia__lte=data_referencia
    ).order_by('data_referencia')
    
    historico_financeiro = IndicadorFinanceiro.objects.filter(
        data_referencia__gte=data_inicio,
        data_referencia__lte=data_referencia
    ).order_by('data_referencia')
    
    historico_ocupacao = IndicadorImobiliario.objects.filter(
        data_referencia__gte=data_inicio,
        data_referencia__lte=data_referencia
    ).order_by('data_referencia')
    
    context = {
        'dashboard': dashboard,
        'indicadores': indicadores,
        'indicadores_gerais': indicadores_gerais,
        'data_referencia': data_referencia,
        'historico_inadimplencia': historico_inadimplencia,
        'historico_financeiro': historico_financeiro,
        'historico_ocupacao': historico_ocupacao,
        'pode_editar': request.user.perfil_usuario.tem_permissao('relatorios', 'editar'),
    }
    
    return render(request, 'core/dashboard_indicadores.html', context)


@login_required
def indicador_inadimplencia_detalhes(request, data_referencia):
    """
    Detalhes do indicador de inadimplência
    """
    if not request.user.perfil_usuario.tem_permissao('financeiro', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar estes dados.')
        return redirect('indicadores:dashboard')
    
    try:
        data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data inválida.')
        return redirect('indicadores:dashboard')
    
    indicador = get_object_or_404(IndicadorInadimplencia, data_referencia=data_ref)
    
    # Buscar contratos inadimplentes para detalhamento
    from contratos.models import Contrato
    from financeiro.models import Parcela
    
    contratos_ativos = Contrato.objects.filter(
        status='ativo',
        data_inicio__lte=data_ref
    )
    
    parcelas_vencidas = Parcela.objects.filter(
        contrato__in=contratos_ativos,
        data_vencimento__lte=data_ref,
        status='pendente'
    ).select_related('contrato', 'contrato__imovel', 'contrato__inquilino')
    
    context = {
        'indicador': indicador,
        'parcelas_vencidas': parcelas_vencidas,
        'data_referencia': data_ref,
    }
    
    return render(request, 'core/indicador_inadimplencia_detalhes.html', context)


@login_required
def indicador_imobiliario_detalhes(request, data_referencia):
    """
    Detalhes do indicador imobiliário
    """
    if not request.user.perfil_usuario.tem_permissao('imoveis', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar estes dados.')
        return redirect('indicadores:dashboard')
    
    try:
        data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data inválida.')
        return redirect('indicadores:dashboard')
    
    indicador = get_object_or_404(IndicadorImobiliario, data_referencia=data_ref)
    
    # Buscar imóveis por status
    from imoveis.models import Imovel
    
    imoveis_ocupados = Imovel.objects.filter(status='OCUPADO', disponivel=True)
    imoveis_vagos = Imovel.objects.filter(status='DISPONIVEL', disponivel=True)
    imoveis_manutencao = Imovel.objects.filter(status='MANUTENCAO', disponivel=True)
    
    context = {
        'indicador': indicador,
        'imoveis_ocupados': imoveis_ocupados,
        'imoveis_vagos': imoveis_vagos,
        'imoveis_manutencao': imoveis_manutencao,
        'data_referencia': data_ref,
    }
    
    return render(request, 'core/indicador_imobiliario_detalhes.html', context)


@login_required
def indicador_financeiro_detalhes(request, data_referencia):
    """
    Detalhes do indicador financeiro
    """
    if not request.user.perfil_usuario.tem_permissao('financeiro', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar estes dados.')
        return redirect('indicadores:dashboard')
    
    try:
        data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Data inválida.')
        return redirect('indicadores:dashboard')
    
    indicador = get_object_or_404(IndicadorFinanceiro, data_referencia=data_ref)
    
    # Período do mês
    inicio_mes = data_ref.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Buscar detalhes das receitas e despesas
    from financeiro.models import Parcela, Repasse
    from manutencao.models import OrdemServico
    
    parcelas_pagas = Parcela.objects.filter(
        data_pagamento__range=[inicio_mes, fim_mes],
        status='pago'
    ).select_related('contrato', 'contrato__imovel')
    
    ordens_servico = OrdemServico.objects.filter(
        data_conclusao__range=[inicio_mes, fim_mes],
        status='concluida'
    ).select_related('imovel')
    
    repasses = Repasse.objects.filter(
        data_repasse__range=[inicio_mes, fim_mes]
    ).select_related('contrato', 'proprietario')
    
    context = {
        'indicador': indicador,
        'parcelas_pagas': parcelas_pagas,
        'ordens_servico': ordens_servico,
        'repasses': repasses,
        'data_referencia': data_ref,
        'inicio_mes': inicio_mes,
        'fim_mes': fim_mes,
    }
    
    return render(request, 'core/indicador_financeiro_detalhes.html', context)


@login_required
def api_indicadores_resumo(request):
    """
    API para retornar resumo dos indicadores (para gráficos)
    """
    if not request.user.perfil_usuario.tem_permissao('relatorios', 'visualizar'):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    data_referencia = request.GET.get('data_referencia')
    if data_referencia:
        try:
            data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
        except ValueError:
            data_ref = timezone.now().date()
    else:
        data_ref = timezone.now().date()
    
    # Buscar indicadores
    try:
        inadimplencia = IndicadorInadimplencia.objects.get(data_referencia=data_ref)
        dados_inadimplencia = {
            'percentual': float(inadimplencia.percentual_inadimplencia),
            'valor': float(inadimplencia.valor_inadimplente),
            'contratos': inadimplencia.contratos_inadimplentes
        }
    except IndicadorInadimplencia.DoesNotExist:
        dados_inadimplencia = None
    
    try:
        imobiliario = IndicadorImobiliario.objects.get(data_referencia=data_ref)
        dados_imobiliario = {
            'taxa_ocupacao': float(imobiliario.taxa_ocupacao),
            'total_imoveis': imobiliario.total_imoveis,
            'ocupados': imobiliario.imoveis_ocupados,
            'vagos': imobiliario.imoveis_vagos
        }
    except IndicadorImobiliario.DoesNotExist:
        dados_imobiliario = None
    
    try:
        financeiro = IndicadorFinanceiro.objects.get(data_referencia=data_ref)
        dados_financeiro = {
            'receita_total': float(financeiro.receita_total),
            'despesa_total': float(financeiro.despesa_total),
            'lucro_liquido': float(financeiro.lucro_liquido),
            'margem_lucro': float(financeiro.margem_lucro)
        }
    except IndicadorFinanceiro.DoesNotExist:
        dados_financeiro = None
    
    return JsonResponse({
        'inadimplencia': dados_inadimplencia,
        'imobiliario': dados_imobiliario,
        'financeiro': dados_financeiro,
        'data_referencia': data_ref.strftime('%Y-%m-%d')
    })


@login_required
def atualizar_indicadores(request):
    """
    Força a atualização de todos os indicadores
    """
    if not request.user.perfil_usuario.tem_permissao('relatorios', 'editar'):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    if request.method == 'POST':
        data_referencia = request.POST.get('data_referencia')
        if data_referencia:
            try:
                data_ref = datetime.strptime(data_referencia, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Data inválida'}, status=400)
        else:
            data_ref = timezone.now().date()
        
        try:
            # Buscar ou criar dashboard
            dashboard, created = DashboardIndicadores.objects.get_or_create(
                data_referencia=data_ref,
                usuario=request.user
            )
            
            # Atualizar indicadores
            indicadores = dashboard.atualizar_todos_indicadores()
            
            return JsonResponse({
                'success': True,
                'message': 'Indicadores atualizados com sucesso!',
                'data_referencia': data_ref.strftime('%Y-%m-%d')
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Erro ao atualizar indicadores: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)


@login_required
def configurar_dashboard(request):
    """
    Configuração personalizada do dashboard
    """
    if not request.user.perfil_usuario.tem_permissao('relatorios', 'editar'):
        messages.error(request, 'Você não tem permissão para configurar o dashboard.')
        return redirect('indicadores:dashboard')
    
    data_referencia = timezone.now().date()
    dashboard, created = DashboardIndicadores.objects.get_or_create(
        data_referencia=data_referencia,
        usuario=request.user
    )
    
    if request.method == 'POST':
        configuracao = {
            'mostrar_inadimplencia': request.POST.get('mostrar_inadimplencia') == 'on',
            'mostrar_imobiliario': request.POST.get('mostrar_imobiliario') == 'on',
            'mostrar_financeiro': request.POST.get('mostrar_financeiro') == 'on',
            'periodo_historico': int(request.POST.get('periodo_historico', 6)),
            'atualizar_automatico': request.POST.get('atualizar_automatico') == 'on',
        }
        
        dashboard.configuracao = configuracao
        dashboard.save()
        
        messages.success(request, 'Configuração do dashboard salva com sucesso!')
        return redirect('indicadores:dashboard')
    
    context = {
        'dashboard': dashboard,
    }
    
    return render(request, 'core/configurar_dashboard.html', context)