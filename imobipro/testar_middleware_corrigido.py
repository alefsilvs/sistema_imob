#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from saas.middleware import TenantMiddleware
from saas.models import Tenant

def testar_middleware_corrigido():
    print("=== TESTE DO MIDDLEWARE CORRIGIDO ===")
    
    # Criar factory para requests
    factory = RequestFactory()
    
    # Buscar usuário e tenant
    try:
        user = User.objects.get(username='alef')
        tenant = Tenant.objects.get(id=6)
        
        print(f"Usuário: {user.username}")
        print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Criar request simulado
        request = factory.get('/imoveis/layouts/')
        
        # Configurar sessão
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        
        # Configurar tenant_id na sessão
        request.session['tenant_id'] = tenant.id
        
        # Configurar autenticação
        auth_middleware = AuthenticationMiddleware(lambda req: None)
        auth_middleware.process_request(request)
        
        # Simular usuário autenticado
        request.user = user
        
        # Testar middleware
        tenant_middleware = TenantMiddleware(lambda req: None)
        response = tenant_middleware.process_request(request)
        
        print(f"\nResultado do middleware:")
        print(f"Response: {response}")
        print(f"Tem request.tenant: {hasattr(request, 'tenant')}")
        
        if hasattr(request, 'tenant'):
            print(f"Tenant configurado: {request.tenant.nome_empresa}")
            print(f"Tenant ID: {request.tenant.id}")
            print("✓ MIDDLEWARE FUNCIONANDO CORRETAMENTE!")
        else:
            print("✗ MIDDLEWARE NÃO CONFIGUROU O TENANT")
            
    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    testar_middleware_corrigido()