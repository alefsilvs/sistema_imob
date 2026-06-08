# -*- coding: utf-8 -*-
"""
Comando para configuração inicial do Power BI

Uso: python manage.py setup_powerbi
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from powerbi.models import PowerBIConfig, PowerBIDataset, PowerBIToken
from rest_framework.authtoken.models import Token as DRFToken


class Command(BaseCommand):
    help = 'Configura a integração inicial com o Power BI'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-token',
            action='store_true',
            help='Cria um token de acesso para o usuário admin'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove todas as configurações existentes e recria'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Configuração do Power BI ===')
        )
        
        if options['reset']:
            self.reset_config()
        
        config = self.create_config()
        if not config:
            return
        
        self.create_datasets()
        
        if options['create_token']:
            self.create_token()
        
        self.show_summary()
    
    def reset_config(self):
        """Remove todas as configurações existentes"""
        self.stdout.write('Removendo configurações existentes...')
        
        PowerBIToken.objects.all().delete()
        PowerBIDataset.objects.all().delete()
        PowerBIConfig.objects.all().delete()
        
        self.stdout.write(
            self.style.WARNING('Configurações removidas!')
        )
    
    def create_config(self):
        """Cria a configuração principal"""
        # Obter usuário admin para o campo criado_por
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Usuário admin não encontrado. Crie um usuário admin primeiro.')
            )
            return None
        
        config, created = PowerBIConfig.objects.get_or_create(
            nome='Configuração Principal',
            defaults={
                'tenant_id': 'CONFIGURE_NO_ADMIN',
                'client_id': 'CONFIGURE_NO_ADMIN',
                'client_secret': 'CONFIGURE_NO_ADMIN',
                'workspace_id': 'CONFIGURE_NO_ADMIN',
                'ativo': True,
                'criado_por': admin_user
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Configuração principal criada')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Configuração principal já existe')
            )
        
        return config
    
    def create_datasets(self):
        """Cria os datasets padrão"""
        config = PowerBIConfig.objects.get(nome='Configuração Principal')
        
        datasets = [
            {
                'nome': 'Dashboard Geral',
                'tipo': 'dashboard',
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
                'tipo': 'imoveis',
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
                'tipo': 'financeiro',
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
                'tipo': 'contratos',
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
                'tipo': 'manutencao',
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
                'tipo': 'inquilinos',
                'endpoint': '/powerbi/inquilinos/',
                'descricao': 'Dados dos inquilinos e histórico',
                'campos_disponiveis': [
                    'nome', 'cpf', 'email', 'telefone', 'data_nascimento',
                    'profissao', 'renda', 'score_credito', 'contratos_ativos'
                ]
            },
            {
                'nome': 'Proprietários',
                'tipo': 'proprietarios',
                'endpoint': '/powerbi/proprietarios/',
                'descricao': 'Informações dos proprietários',
                'campos_disponiveis': [
                    'nome', 'cpf_cnpj', 'email', 'telefone',
                    'total_imoveis', 'receita_mensal', 'banco_conta'
                ]
            }
        ]
        
        created_count = 0
        for dataset_data in datasets:
            dataset, created = PowerBIDataset.objects.get_or_create(
                nome=dataset_data['nome'],
                defaults={
                    'tipo': dataset_data['tipo'],
                    'endpoint': dataset_data['endpoint'],
                    'descricao': dataset_data['descricao'],
                    'ativo': True
                }
            )
            
            if created:
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ {created_count} datasets criados')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Todos os datasets já existem')
            )
    
    def create_token(self):
        """Cria um token de acesso para o usuário admin"""
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Usuário admin não encontrado')
            )
            return
        
        # Criar ou obter token do Django REST Framework
        token, created = DRFToken.objects.get_or_create(user=admin_user)
        
        # Obter configuração do Power BI
        try:
            config = PowerBIConfig.objects.get(nome='Configuração Principal')
        except PowerBIConfig.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('✗ Configuração do Power BI não encontrada')
            )
            return
        
        # Criar registro no PowerBIToken
        from django.utils import timezone
        from datetime import timedelta
        
        powerbi_token, created = PowerBIToken.objects.get_or_create(
            config=config,
            defaults={
                'token': token.key,
                'expira_em': timezone.now() + timedelta(days=365)
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Token de acesso criado')
            )
            self.stdout.write(
                f'Token: {token.key}'
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Token já existe')
            )
            self.stdout.write(
                f'Token: {powerbi_token.token}'
            )
    
    def show_summary(self):
        """Mostra um resumo da configuração"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS('CONFIGURAÇÃO CONCLUÍDA!')
        )
        self.stdout.write('='*50)
        
        # Estatísticas
        configs = PowerBIConfig.objects.count()
        datasets = PowerBIDataset.objects.count()
        tokens = PowerBIToken.objects.count()
        
        self.stdout.write(f'📊 Configurações: {configs}')
        self.stdout.write(f'📈 Datasets: {datasets}')
        self.stdout.write(f'🔑 Tokens: {tokens}')
        
        self.stdout.write('\n📋 PRÓXIMOS PASSOS:')
        self.stdout.write('1. Acesse o Django Admin (/admin/)')
        self.stdout.write('2. Configure os dados reais do Power BI:')
        self.stdout.write('   - Tenant ID')
        self.stdout.write('   - Client ID')
        self.stdout.write('   - Client Secret')
        self.stdout.write('   - Workspace ID')
        self.stdout.write('3. Teste as APIs:')
        self.stdout.write('   - /powerbi/health/ (verificar saúde)')
        self.stdout.write('   - /powerbi/datasets/ (listar datasets)')
        self.stdout.write('   - /powerbi/dashboard/ (dados do dashboard)')
        
        if PowerBIToken.objects.exists():
            token = PowerBIToken.objects.first()
            self.stdout.write('\n🔑 EXEMPLO DE USO:')
            self.stdout.write('curl -H "Authorization: Token ' + token.token + '" \\')
            self.stdout.write('     http://localhost:8000/powerbi/health/')
        
        self.stdout.write('\n📚 DOCUMENTAÇÃO:')
        self.stdout.write('- README: powerbi/README.md')
        self.stdout.write('- Exemplos: powerbi/config_example.py')
        
        self.stdout.write('\n' + '='*50)