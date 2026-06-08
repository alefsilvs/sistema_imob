#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from imoveis.models import Imovel
from contratos.models import Contrato
from saas.models import Tenant
from core.models import Proprietario, Inquilino

print('=== TESTE DE ISOLAMENTO DE DADOS ===')
print(f'Total de tenants: {Tenant.objects.count()}')
print(f'Total de imóveis no banco: {Imovel.objects.count()}')
print(f'Total de contratos no banco: {Contrato.objects.count()}')

print('\n=== DADOS POR TENANT ===')
for tenant in Tenant.objects.all()[:5]:
    print(f'\nTenant: {tenant.nome_empresa} ({tenant.subdominio})')
    print(f'  Imóveis: {Imovel.objects.for_tenant(tenant).count()}')
    print(f'  Contratos: {Contrato.objects.for_tenant(tenant).count()}')
    print(f'  Proprietários: {Proprietario.objects.for_tenant(tenant).count()}')
    print(f'  Inquilinos: {Inquilino.objects.for_tenant(tenant).count()}')

print('\n=== TESTE SEM TENANT ===')
print(f'Imóveis sem tenant: {Imovel.objects.for_tenant(None).count()}')
print(f'Contratos sem tenant: {Contrato.objects.for_tenant(None).count()}')