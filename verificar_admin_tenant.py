#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant

def verificar_admin_tenant():
    print("=== VERIFICAÇÃO DO ADMIN DO TENANT ===")
    
    try:
        # Buscar usuário alef
        user_alef = User.objects.get(username='alef')
        print(f"Usuário alef: {user_alef.username} (ID: {user_alef.id})")
        
        # Buscar tenant ID 6
        tenant = Tenant.objects.get(id=6)
        print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"Admin do tenant: {tenant.usuario_admin.username} (ID: {tenant.usuario_admin.id})")
        
        # Verificar se alef é o admin
        if tenant.usuario_admin == user_alef:
            print("✓ ALEF É O ADMIN DO TENANT")
        else:
            print("✗ ALEF NÃO É O ADMIN DO TENANT")
            print(f"Admin atual: {tenant.usuario_admin.username}")
            
        # Listar todos os tenants onde alef é admin
        tenants_alef = Tenant.objects.filter(usuario_admin=user_alef)
        print(f"\nTenants onde alef é admin: {tenants_alef.count()}")
        for t in tenants_alef:
            print(f"  - {t.nome_empresa} (ID: {t.id})")
            
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_admin_tenant()