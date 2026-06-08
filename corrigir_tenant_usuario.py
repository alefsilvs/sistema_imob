#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant

def corrigir_tenant_usuario():
    print("=== CORREÇÃO DO TENANT DO USUÁRIO ===")
    
    try:
        # Buscar usuário alef
        user_alef = User.objects.get(username='alef')
        print(f"Usuário alef: {user_alef.username} (ID: {user_alef.id})")
        
        # Buscar tenant onde alef deveria ser admin
        tenant = Tenant.objects.get(id=6)
        print(f"Tenant atual: {tenant.nome_empresa}")
        print(f"Admin atual: {tenant.usuario_admin.username} (ID: {tenant.usuario_admin.id})")
        
        # Opção 1: Alterar o admin do tenant para alef
        print("\nOpção 1: Alterar admin do tenant para alef")
        tenant.usuario_admin = user_alef
        tenant.save()
        print(f"✓ Admin do tenant alterado para: {user_alef.username}")
        
        # Verificar se funcionou
        tenant.refresh_from_db()
        print(f"Verificação - Admin atual: {tenant.usuario_admin.username}")
        
        # Opção 2: Criar um tenant específico para alef (se necessário)
        # Vamos comentar por enquanto
        """
        print("\nOpção 2: Criar tenant específico para alef")
        novo_tenant = Tenant.objects.create(
            nome_empresa="Empresa do Alef",
            subdominio="alef",
            usuario_admin=user_alef,
            status="ativo"
        )
        print(f"✓ Novo tenant criado: {novo_tenant.nome_empresa} (ID: {novo_tenant.id})")
        """
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    corrigir_tenant_usuario()