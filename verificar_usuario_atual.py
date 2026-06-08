#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant

def verificar_usuario_atual():
    print("=== VERIFICAÇÃO DO USUÁRIO ATUAL ===")
    
    try:
        # Verificar usuário alef63134@gmail.com (ID: 2)
        user = User.objects.get(id=2)
        print(f"Usuário logado: {user.username} (ID: {user.id})")
        print(f"Email: {user.email}")
        
        # Verificar tenants onde este usuário é admin
        tenants_admin = Tenant.objects.filter(usuario_admin=user)
        print(f"\nTenants onde {user.username} é admin: {tenants_admin.count()}")
        for tenant in tenants_admin:
            print(f"  - {tenant.nome_empresa} (ID: {tenant.id}, Status: {tenant.status})")
        
        # Verificar todos os tenants
        all_tenants = Tenant.objects.all()
        print(f"\nTodos os tenants no sistema: {all_tenants.count()}")
        for tenant in all_tenants:
            print(f"  - {tenant.nome_empresa} (Admin: {tenant.usuario_admin.username}, ID: {tenant.id}, Status: {tenant.status})")
            
        # Verificar se há algum tenant ativo para este usuário
        tenant_ativo = Tenant.objects.filter(
            usuario_admin=user,
            status__in=['ativo', 'trial', 'pendente_pagamento']
        ).first()
        
        if tenant_ativo:
            print(f"\n✓ TENANT ATIVO ENCONTRADO: {tenant_ativo.nome_empresa} (ID: {tenant_ativo.id})")
            print("Sugestão: Configurar tenant_id na sessão")
        else:
            print("\n✗ NENHUM TENANT ATIVO ENCONTRADO PARA ESTE USUÁRIO")
            
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_usuario_atual()