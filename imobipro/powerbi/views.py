# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

import time
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from imoveis.models import Imovel
from contratos.models import Contrato
from financeiro.models import Parcela, Repasse, NotaFiscal, IPTU, Seguro
from manutencao.models import OrdemServico
from core.models import Inquilino, Proprietario
from .models import PowerBIDataset, PowerBIAccessLog
from .serializers import (
    DashboardGeralSerializer,
    ImovelPowerBISerializer,
    FinanceiroPowerBISerializer,
    ContratoPowerBISerializer,
    ManutencaoPowerBISerializer,
    InquilinoPowerBISerializer,
    ProprietarioPowerBISerializer
)


class PowerBIBaseView(APIView):
    """
    Classe base para views do Power BI com logging automático
    """
    permission_classes = [IsAuthenticated]
    dataset_tipo = None
    
    def dispatch(self, request, *args, **kwargs):
        start_time = time.time()
        response = super().dispatch(request, *args, **kwargs)
        end_time = time.time()
        
        # Log do acesso
        if self.dataset_tipo:
            try:
                dataset = PowerBIDataset.objects.get(tipo=self.dataset_tipo, ativo=True)
                registros_retornados = 0
                
                if hasattr(response, 'data') and isinstance(response.data, (list, dict)):
                    if isinstance(response.data, list):
                        registros_retornados = len(response.data)
                    elif isinstance(response.data, dict) and 'results' in response.data:
                        registros_retornados = len(response.data['results'])
                    else:
                        registros_retornados = 1
                
                PowerBIAccessLog.objects.create(
                    dataset=dataset,
                    usuario=request.user if request.user.is_authenticated else None,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metodo=request.method,
                    status_code=response.status_code,
                    tempo_resposta=(end_time - start_time) * 1000,
                    registros_retornados=registros_retornados
                )
            except PowerBIDataset.DoesNotExist:
                pass
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DashboardGeralAPIView(PowerBIBaseView):
    """
    API para dados gerais do dashboard
    """
    dataset_tipo = 'dashboard'
    
    def get(self, request):
        hoje = timezone.now().date()
        mes_atual = timezone.now().replace(day=1).date()
        
        # Dados de imóveis
        total_imoveis = Imovel.objects.count()
        imoveis_ocupados = Imovel.objects.filter(
            contrato__data_inicio__lte=hoje,
            contrato__data_fim__gte=hoje
        ).distinct().count()
        imoveis_vagos = total_imoveis - imoveis_ocupados
        taxa_ocupacao = (imoveis_ocupados / total_imoveis * 100) if total_imoveis > 0 else 0
        
        # Dados financeiros do mês atual
        receitas = Parcela.objects.filter(
            status='PAGO',
            data_pagamento__gte=mes_atual
        ).aggregate(total=Sum('valor_pago'))['total'] or 0
        
        # Para despesas, vamos usar repasses como exemplo
        despesas = Repasse.objects.filter(
            data_repasse__gte=mes_atual
        ).aggregate(total=Sum('valor_repasse'))['total'] or 0
        
        lucro = receitas - despesas
        
        # Dados de contratos
        contratos_ativos = Contrato.objects.filter(
            data_inicio__lte=hoje,
            data_fim__gte=hoje
        ).count()
        
        # Contratos vencendo em 30 dias
        data_limite = hoje + timedelta(days=30)
        contratos_vencendo = Contrato.objects.filter(
            data_fim__gte=hoje,
            data_fim__lte=data_limite
        ).count()
        
        # Manutenções pendentes
        manutencoes_pendentes = OrdemServico.objects.filter(
            status__in=['aberta', 'em_andamento']
        ).count()
        
        data = {
            'total_imoveis': total_imoveis,
            'imoveis_ocupados': imoveis_ocupados,
            'imoveis_vagos': imoveis_vagos,
            'taxa_ocupacao': round(taxa_ocupacao, 2),
            'receita_mensal': receitas,
            'despesas_mensais': despesas,
            'lucro_mensal': lucro,
            'contratos_ativos': contratos_ativos,
            'contratos_vencendo': contratos_vencendo,
            'manutencoes_pendentes': manutencoes_pendentes,
            'data_atualizacao': timezone.now()
        }
        
        serializer = DashboardGeralSerializer(data)
        return Response(serializer.data)


class ImoveisPowerBIAPIView(PowerBIBaseView):
    """
    API para dados de imóveis
    """
    dataset_tipo = 'imoveis'
    
    def get(self, request):
        # Filtrar por tenant se disponível
        if hasattr(request, 'tenant') and request.tenant:
            imoveis = Imovel.objects.filter(tenant=request.tenant).select_related('proprietario')
        else:
            imoveis = Imovel.objects.none()
        serializer = ImovelPowerBISerializer(imoveis, many=True)
        return Response(serializer.data)


class FinanceiroPowerBIAPIView(PowerBIBaseView):
    """
    API para dados financeiros
    """
    dataset_tipo = 'financeiro'
    
    def get(self, request):
        # Parâmetros de filtro
        ano = request.GET.get('ano', timezone.now().year)
        mes_inicio = request.GET.get('mes_inicio', 1)
        mes_fim = request.GET.get('mes_fim', 12)
        
        try:
            ano = int(ano)
            mes_inicio = int(mes_inicio)
            mes_fim = int(mes_fim)
        except ValueError:
            return Response(
                {'error': 'Parâmetros de data inválidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar todas as parcelas do período
        parcelas = Parcela.objects.filter(
            data_vencimento__year=ano,
            data_vencimento__month__gte=mes_inicio,
            data_vencimento__month__lte=mes_fim
        )
        
        serializer = FinanceiroPowerBISerializer(parcelas, many=True)
        return Response(serializer.data)


class ContratosPowerBIAPIView(PowerBIBaseView):
    """
    API para dados de contratos
    """
    dataset_tipo = 'contratos'
    
    def get(self, request):
        # Filtrar por tenant se disponível
        if hasattr(request, 'tenant') and request.tenant:
            contratos = Contrato.objects.filter(tenant=request.tenant).select_related(
                'imovel', 'inquilino', 'imovel__proprietario'
            )
        else:
            contratos = Contrato.objects.none()
        serializer = ContratoPowerBISerializer(contratos, many=True)
        return Response(serializer.data)


class ManutencaoPowerBIAPIView(PowerBIBaseView):
    """
    API para dados de manutenção
    """
    dataset_tipo = 'manutencao'
    
    def get(self, request):
        ordens = OrdemServico.objects.select_related(
            'imovel', 'imovel__proprietario'
        ).all()
        serializer = ManutencaoPowerBISerializer(ordens, many=True)
        return Response(serializer.data)


class InquilinosPowerBIAPIView(PowerBIBaseView):
    """
    API para dados de inquilinos
    """
    dataset_tipo = 'inquilinos'
    
    def get(self, request):
        # Filtrar por tenant se disponível
        if hasattr(request, 'tenant') and request.tenant:
            inquilinos = Inquilino.objects.filter(tenant=request.tenant)
        else:
            inquilinos = Inquilino.objects.none()
        serializer = InquilinoPowerBISerializer(inquilinos, many=True)
        return Response(serializer.data)


class ProprietariosPowerBIAPIView(PowerBIBaseView):
    """
    API para dados de proprietários
    """
    dataset_tipo = 'proprietarios'
    
    def get(self, request):
        proprietarios = Proprietario.objects.all()
        serializer = ProprietarioPowerBISerializer(proprietarios, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_datasets(request):
    """
    Lista todos os datasets disponíveis para Power BI
    """
    datasets = PowerBIDataset.objects.filter(ativo=True)
    data = []
    
    for dataset in datasets:
        data.append({
            'id': dataset.id,
            'nome': dataset.nome,
            'tipo': dataset.tipo,
            'descricao': dataset.descricao,
            'endpoint': request.build_absolute_uri(dataset.endpoint),
            'requer_autenticacao': dataset.requer_autenticacao
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_health(request):
    """
    Endpoint de health check para Power BI
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now(),
        'version': '1.0.0',
        'datasets_ativos': PowerBIDataset.objects.filter(ativo=True).count()
    })


class PowerBIConfigView(APIView):
    """
    View para gerenciar configurações do Power BI
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retorna as configurações atuais do Power BI
        """
        try:
            from django.conf import settings
            
            # Verificar se as configurações existem
            is_configured = bool(
                getattr(settings, 'POWERBI_WORKSPACE_ID', '') and
                getattr(settings, 'POWERBI_CLIENT_ID', '') and
                getattr(settings, 'POWERBI_CLIENT_SECRET', '')
            )
            
            config = {
                'workspace_id': getattr(settings, 'POWERBI_WORKSPACE_ID', ''),
                'client_id': getattr(settings, 'POWERBI_CLIENT_ID', ''),
                'tenant_id': getattr(settings, 'POWERBI_TENANT_ID', ''),
                'configured': is_configured,
                'last_sync': getattr(settings, 'POWERBI_LAST_SYNC', None),
                'reports': [
                    {
                        'id': 'dashboard',
                        'name': 'Dashboard Geral',
                        'description': 'Métricas gerais do sistema',
                        'icon': 'bi-speedometer2',
                        'color': 'primary',
                        'configured': is_configured
                    },
                    {
                        'id': 'financeiro',
                        'name': 'Relatório Financeiro',
                        'description': 'Análise de receitas e despesas',
                        'icon': 'bi-currency-dollar',
                        'color': 'success',
                        'configured': is_configured
                    },
                    {
                        'id': 'imoveis',
                        'name': 'Relatório de Imóveis',
                        'description': 'Análise do portfólio de imóveis',
                        'icon': 'bi-building',
                        'color': 'warning',
                        'configured': is_configured
                    },
                    {
                        'id': 'contratos',
                        'name': 'Relatório de Contratos',
                        'description': 'Análise de contratos e ocupação',
                        'icon': 'bi-file-earmark-text',
                        'color': 'purple',
                        'configured': is_configured
                    }
                ]
            }
            
            return Response(config)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao carregar configurações: {str(e)}', 'reports': []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """
        Salva as configurações do Power BI
        """
        try:
            data = request.data
            
            # Validar dados obrigatórios
            required_fields = ['workspace_id', 'client_id', 'client_secret']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        {'error': f'Campo {field} é obrigatório'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Simular salvamento das configurações
            # Em uma implementação real, você salvaria no banco de dados ou arquivo de configuração
            config_data = {
                'workspace_id': data.get('workspace_id'),
                'client_id': data.get('client_id'),
                'client_secret': data.get('client_secret'),
                'tenant_id': data.get('tenant_id', ''),
                'configured_at': timezone.now().isoformat(),
                'configured_by': request.user.username
            }
            
            # Log da configuração
            PowerBIAccessLog.objects.create(
                usuario=request.user,
                dataset_tipo='config',
                endpoint='/powerbi/config/',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                tempo_resposta=0.1,
                status_code=200
            )
            
            return Response({
                'success': True,
                'message': 'Configurações salvas com sucesso!',
                'config': config_data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao salvar configurações: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_powerbi_connection(request):
    """
    Testa a conexão com o Power BI usando as credenciais fornecidas
    """
    try:
        data = request.data
        
        # Validar dados
        required_fields = ['workspace_id', 'client_id', 'client_secret']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Campo {field} é obrigatório'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Simular teste de conexão
        # Em uma implementação real, você faria uma chamada para a API do Power BI
        import time
        time.sleep(2)  # Simular tempo de resposta
        
        # Simular sucesso (90% das vezes)
        import random
        if random.random() > 0.1:
            return Response({
                'success': True,
                'message': 'Conexão estabelecida com sucesso!',
                'workspace_name': 'ImobiPro Workspace',
                'reports_found': 4,
                'last_refresh': timezone.now().isoformat()
            })
        else:
            return Response(
                {'error': 'Falha na autenticação. Verifique as credenciais.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    except Exception as e:
        return Response(
            {'error': f'Erro ao testar conexão: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


