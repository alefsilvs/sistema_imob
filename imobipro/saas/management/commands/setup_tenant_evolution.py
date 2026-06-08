"""
Comando Django para configurar Evolution API para tenants existentes
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import logging

from saas.models import Tenant
from saas.evolution_services import tenant_evolution_service
from saas.database_isolation import TenantDatabaseManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Configura Evolution API e isolamento de banco para tenants existentes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='ID específico do tenant para configurar'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Configurar todos os tenants'
        )
        
        parser.add_argument(
            '--create-schemas',
            action='store_true',
            help='Criar schemas de banco de dados separados'
        )
        
        parser.add_argument(
            '--create-evolution',
            action='store_true',
            help='Criar instâncias Evolution API'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular execução sem fazer alterações'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuração de tenants...')
        )
        
        # Determinar quais tenants configurar
        if options['tenant_id']:
            try:
                tenants = [Tenant.objects.get(id=options['tenant_id'])]
            except Tenant.DoesNotExist:
                raise CommandError(f'Tenant com ID {options["tenant_id"]} não encontrado')
        elif options['all']:
            tenants = Tenant.objects.all()
        else:
            raise CommandError('Especifique --tenant-id ou --all')
        
        self.stdout.write(f'Configurando {len(tenants)} tenant(s)...')
        
        success_count = 0
        error_count = 0
        
        for tenant in tenants:
            self.stdout.write(f'\nConfigurando tenant: {tenant.nome_empresa} (ID: {tenant.id})')
            
            try:
                with transaction.atomic():
                    # Criar schema de banco de dados
                    if options['create_schemas']:
                        self._create_tenant_schema(tenant, options['dry_run'])
                    
                    # Criar instância Evolution API
                    if options['create_evolution']:
                        self._create_evolution_instance(tenant, options['dry_run'])
                    
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Tenant {tenant.nome_empresa} configurado com sucesso')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao configurar {tenant.nome_empresa}: {str(e)}')
                )
                logger.error(f'Erro ao configurar tenant {tenant.id}: {str(e)}')
        
        # Resumo final
        self.stdout.write(f'\n{"-" * 50}')
        self.stdout.write(f'Configuração concluída:')
        self.stdout.write(f'✓ Sucessos: {success_count}')
        self.stdout.write(f'✗ Erros: {error_count}')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração foi feita')
            )
    
    def _create_tenant_schema(self, tenant, dry_run=False):
        """
        Cria schema de banco de dados para o tenant
        """
        self.stdout.write(f'  Criando schema de banco de dados...')
        
        if dry_run:
            self.stdout.write('    [DRY-RUN] Schema seria criado')
            return
        
        db_manager = TenantDatabaseManager()
        success = db_manager.create_tenant_schema(tenant)
        
        if success:
            self.stdout.write('    ✓ Schema criado com sucesso')
        else:
            raise Exception('Falha ao criar schema de banco de dados')
    
    def _create_evolution_instance(self, tenant, dry_run=False):
        """
        Cria instância Evolution API para o tenant
        """
        self.stdout.write(f'  Criando instância Evolution API...')
        
        if dry_run:
            self.stdout.write('    [DRY-RUN] Instância Evolution seria criada')
            return
        
        # Verificar se já existe instância
        from saas.evolution_models import EvolutionInstance
        existing = EvolutionInstance.objects.filter(tenant=tenant).first()
        
        if existing:
            self.stdout.write('    ⚠ Instância Evolution já existe')
            return
        
        # Criar nova instância
        instance = tenant_evolution_service.provision_tenant_instance(tenant)
        
        if instance:
            self.stdout.write(f'    ✓ Instância criada: {instance.instance_name}')
            self.stdout.write(f'    Token: {instance.token}')
        else:
            raise Exception('Falha ao criar instância Evolution API')