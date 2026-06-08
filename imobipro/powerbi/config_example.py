# -*- coding: utf-8 -*-
"""
Exemplo de configuração para integração com Power BI

Este arquivo contém exemplos de como configurar a integração
com o Microsoft Power BI através do Django Admin.
"""

from django.core.management.base import BaseCommand
from powerbi.models import PowerBIConfig, PowerBIDataset


class Command(BaseCommand):
    help = 'Cria configurações iniciais para o Power BI'
    
    def handle(self, *args, **options):
        # Configuração principal do Power BI
        config, created = PowerBIConfig.objects.get_or_create(
            nome='Configuração Principal',
            defaults={
                'tenant_id': 'seu-tenant-id-aqui',
                'client_id': 'seu-client-id-aqui',
                'client_secret': 'seu-client-secret-aqui',
                'workspace_id': 'seu-workspace-id-aqui',
                'ativo': True,
                'descricao': 'Configuração principal para integração com Power BI'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Configuração principal criada com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Configuração principal já existe.')
            )
        
        # Datasets padrão
        datasets = [
            {
                'nome': 'Dashboard Geral',
                'endpoint': '/powerbi/dashboard/',
                'descricao': 'Dados consolidados para visão geral do negócio',
                'campos_disponiveis': [
                    'total_imoveis', 'imoveis_ocupados', 'imoveis_disponiveis',
                    'total_contratos', 'contratos_ativos', 'receita_mensal',
                    'inadimplencia_percentual', 'manutencoes_pendentes'
                ]
            },
            {
                'nome': 'Imóveis',
                'endpoint': '/powerbi/imoveis/',
                'descricao': 'Lista completa de imóveis com detalhes',
                'campos_disponiveis': [
                    'codigo', 'tipo', 'endereco', 'bairro', 'cidade',
                    'area_total', 'quartos', 'banheiros', 'valor_aluguel',
                    'status', 'proprietario_nome'
                ]
            },
            {
                'nome': 'Financeiro',
                'endpoint': '/powerbi/financeiro/',
                'descricao': 'Dados de parcelas, pagamentos e inadimplência',
                'campos_disponiveis': [
                    'numero_parcela', 'data_vencimento', 'valor_total',
                    'valor_aluguel', 'data_pagamento', 'status',
                    'contrato_numero', 'imovel_codigo', 'inquilino_nome'
                ]
            },
            {
                'nome': 'Contratos',
                'endpoint': '/powerbi/contratos/',
                'descricao': 'Informações detalhadas dos contratos',
                'campos_disponiveis': [
                    'numero', 'data_inicio', 'data_fim', 'valor_aluguel',
                    'valor_deposito', 'status', 'imovel_codigo',
                    'inquilino_nome', 'proprietario_nome'
                ]
            },
            {
                'nome': 'Manutenção',
                'endpoint': '/powerbi/manutencao/',
                'descricao': 'Ordens de serviço e custos de manutenção',
                'campos_disponiveis': [
                    'numero', 'tipo_servico', 'descricao', 'valor_total',
                    'data_abertura', 'data_conclusao', 'status',
                    'imovel_codigo', 'fornecedor'
                ]
            },
            {
                'nome': 'Inquilinos',
                'endpoint': '/powerbi/inquilinos/',
                'descricao': 'Dados dos inquilinos e histórico',
                'campos_disponiveis': [
                    'nome', 'cpf', 'email', 'telefone', 'data_nascimento',
                    'profissao', 'renda', 'score_credito', 'contratos_ativos'
                ]
            },
            {
                'nome': 'Proprietários',
                'endpoint': '/powerbi/proprietarios/',
                'descricao': 'Informações dos proprietários',
                'campos_disponiveis': [
                    'nome', 'cpf_cnpj', 'email', 'telefone',
                    'total_imoveis', 'receita_mensal', 'banco_conta'
                ]
            }
        ]
        
        for dataset_data in datasets:
            dataset, created = PowerBIDataset.objects.get_or_create(
                nome=dataset_data['nome'],
                defaults={
                    'endpoint': dataset_data['endpoint'],
                    'descricao': dataset_data['descricao'],
                    'campos_disponiveis': dataset_data['campos_disponiveis'],
                    'ativo': True,
                    'config': config
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Dataset "{dataset_data["nome"]}" criado!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Dataset "{dataset_data["nome"]}" já existe.')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\nConfiguração inicial concluída!')
        )
        self.stdout.write(
            'Próximos passos:'
        )
        self.stdout.write(
            '1. Acesse o Django Admin'
        )
        self.stdout.write(
            '2. Configure os dados reais do Power BI na seção "Power BI Config"'
        )
        self.stdout.write(
            '3. Gere tokens de acesso na seção "Power BI Token"'
        )
        self.stdout.write(
            '4. Teste as APIs usando o endpoint /powerbi/health/'
        )


# Exemplo de uso das APIs
EXEMPLO_REQUESTS = """
# Exemplo de como usar as APIs do Power BI

import requests
import json

# Configuração
BASE_URL = 'http://localhost:8000'
TOKEN = 'seu_token_aqui'

headers = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

# 1. Verificar saúde da API
response = requests.get(f'{BASE_URL}/powerbi/health/', headers=headers)
print('Health Check:', response.json())

# 2. Listar datasets disponíveis
response = requests.get(f'{BASE_URL}/powerbi/datasets/', headers=headers)
print('Datasets:', response.json())

# 3. Obter dados do dashboard
response = requests.get(f'{BASE_URL}/powerbi/dashboard/', headers=headers)
print('Dashboard:', response.json())

# 4. Obter dados de imóveis
response = requests.get(f'{BASE_URL}/powerbi/imoveis/', headers=headers)
print('Imóveis:', response.json())

# 5. Obter dados financeiros com filtro de data
params = {
    'data_inicio': '2024-01-01',
    'data_fim': '2024-12-31'
}
response = requests.get(
    f'{BASE_URL}/powerbi/financeiro/', 
    headers=headers, 
    params=params
)
print('Financeiro:', response.json())

# 6. Obter dados de contratos ativos
params = {'status': 'ativo'}
response = requests.get(
    f'{BASE_URL}/powerbi/contratos/', 
    headers=headers, 
    params=params
)
print('Contratos Ativos:', response.json())
"""

# Configurações recomendadas para Power BI
POWER_BI_SETTINGS = {
    'REFRESH_INTERVAL': '1 hour',  # Intervalo de atualização recomendado
    'MAX_ROWS_PER_REQUEST': 10000,  # Limite de linhas por requisição
    'TIMEOUT': 30,  # Timeout em segundos
    'RETRY_ATTEMPTS': 3,  # Tentativas de retry
    'CACHE_DURATION': 300,  # Cache em segundos (5 minutos)
}

# Campos recomendados para cada dataset
RECOMMENDED_FIELDS = {
    'dashboard': [
        'data_referencia', 'total_imoveis', 'imoveis_ocupados',
        'receita_mensal', 'inadimplencia_percentual'
    ],
    'imoveis': [
        'codigo', 'tipo', 'endereco', 'bairro', 'cidade',
        'valor_aluguel', 'status', 'area_total'
    ],
    'financeiro': [
        'data_vencimento', 'valor_total', 'status',
        'contrato_numero', 'imovel_codigo'
    ],
    'contratos': [
        'numero', 'data_inicio', 'data_fim', 'valor_aluguel',
        'status', 'imovel_codigo', 'inquilino_nome'
    ]
}