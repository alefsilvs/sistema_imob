#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant

def associar_usuario_tenant():
    print("=== ASSOCIAÇÃO DO USUÁRIO AO TENANT ===")
    
    try:
        # Buscar usuário alef63134@gmail.com (ID: 2)
        user = User.objects.get(id=2)
        print(f"Usuário: {user.username} (ID: {user.id})")
        print(f"Email: {user.email}")
        
        # Buscar tenant Y.L. EMPREENDIMENTOS (ID: 6) que já foi configurado
        tenant = Tenant.objects.get(id=6)
        print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"Admin atual: {tenant.usuario_admin.username}")
        print(f"Status: {tenant.status}")
        
        # Associar o usuário alef63134@gmail.com como admin do tenant
        print(f"\nAssociando {user.username} como admin do tenant {tenant.nome_empresa}...")
        tenant.usuario_admin = user
        tenant.save()
        
        # Verificar se funcionou
        tenant.refresh_from_db()
        print(f"✓ Admin do tenant alterado para: {tenant.usuario_admin.username}")
        
        # Verificar se o tenant está ativo
        if tenant.status in ['ativo', 'trial', 'pendente_pagamento']:
            print(f"✓ Tenant está ativo (Status: {tenant.status})")
        else:
            print(f"⚠ Tenant não está ativo (Status: {tenant.status})")
            print("Ativando tenant...")
            tenant.status = 'ativo'
            tenant.save()
            print("✓ Tenant ativado")
            
        print(f"\n=== RESULTADO ===")
        print(f"Usuário: {user.username}")
        print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"Status: {tenant.status}")
        print("✓ ASSOCIAÇÃO CONCLUÍDA COM SUCESSO!")
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    associar_usuario_tenant()