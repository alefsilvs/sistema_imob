#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant

# Verificar usuário alef
try:
    user = User.objects.get(username='alef')
    print(f"Usuário encontrado: {user.username}")
    print(f"Email: {user.email}")
    print(f"É superuser: {user.is_superuser}")
    print(f"É staff: {user.is_staff}")
    
    # Verificar se tem atributo tenant
    if hasattr(user, 'tenant'):
        print(f"Atributo tenant: {user.tenant}")
    else:
        print("Usuário não tem atributo 'tenant'")
    
    # Verificar se é admin de algum tenant
    tenants_admin = Tenant.objects.filter(usuario_admin=user)
    print(f"\nTenants onde é admin: {tenants_admin.count()}")
    for tenant in tenants_admin:
        print(f"  - {tenant.nome_empresa} (ID: {tenant.id}, Status: {tenant.status})")
    
    # Verificar todos os tenants
    all_tenants = Tenant.objects.all()
    print(f"\nTodos os tenants no sistema: {all_tenants.count()}")
    for tenant in all_tenants:
        print(f"  - {tenant.nome_empresa} (Admin: {tenant.usuario_admin.username}, Status: {tenant.status})")
        
except User.DoesNotExist:
    print("Usuário 'alef' não encontrado")
except Exception as e:
    print(f"Erro: {e}")