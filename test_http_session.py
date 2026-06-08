#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth import get_user
from django.utils import timezone
from saas.models import Tenant
import json

def test_http_session():
    print("🔍 TESTANDO PROCESSAMENTO DE SESSÕES HTTP")
    print("=" * 60)
    
    # 1. Pegar uma sessão ativa válida
    print("\n1. BUSCANDO SESSÃO ATIVA:")
    active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
    
    valid_session = None
    for session in active_sessions:
        try:
            data = session.get_decoded()
            if data.get('_auth_user_id') and data.get('tenant_id') == 6:
                valid_session = session
                print(f"   ✓ Sessão encontrada: {session.session_key}")
                print(f"     User ID: {data.get('_auth_user_id')}")
                print(f"     Tenant ID: {data.get('tenant_id')}")
                break
        except:
            continue
    
    if not valid_session:
        print("   ❌ Nenhuma sessão válida encontrada!")
        return
    
    # 2. Criar uma requisição HTTP simulada
    print("\n2. CRIANDO REQUISIÇÃO HTTP SIMULADA:")
    factory = RequestFactory()
    request = factory.get('/imoveis/bancas/mapa/')
    
    # Configurar cookies da sessão
    request.COOKIES = {'sessionid': valid_session.session_key}
    print(f"   ✓ Cookie sessionid configurado: {valid_session.session_key}")
    
    # 3. Processar middlewares manualmente
    print("\n3. PROCESSANDO MIDDLEWARES:")
    
    # SessionMiddleware
    print("   📋 Processando SessionMiddleware...")
    session_middleware = SessionMiddleware(lambda r: None)
    session_middleware.process_request(request)
    
    print(f"      Session key: {request.session.session_key}")
    print(f"      Session data: {dict(request.session)}")
    
    # AuthenticationMiddleware
    print("   🔐 Processando AuthenticationMiddleware...")
    auth_middleware = AuthenticationMiddleware(lambda r: None)
    auth_middleware.process_request(request)
    
    print(f"      User: {request.user}")
    print(f"      User authenticated: {request.user.is_authenticated}")
    print(f"      User active: {request.user.is_active if hasattr(request.user, 'is_active') else 'N/A'}")
    
    # 4. Verificar TenantMiddleware
    print("\n4. VERIFICANDO TENANT MIDDLEWARE:")
    try:
        from saas.middleware import TenantMiddleware
        tenant_middleware = TenantMiddleware(lambda r: None)
        
        # Simular subdomínio (se necessário)
        request.META['HTTP_HOST'] = '127.0.0.1:8000'
        
        response = tenant_middleware.process_request(request)
        
        if response:
            print(f"   ❌ TenantMiddleware retornou resposta: {response}")
            print(f"      Status: {response.status_code}")
            if hasattr(response, 'url'):
                print(f"      Redirect URL: {response.url}")
        else:
            print(f"   ✓ TenantMiddleware passou")
            print(f"      Tenant: {getattr(request, 'tenant', 'Não definido')}")
            print(f"      Tenant ID: {getattr(request, 'tenant_id', 'Não definido')}")
            
    except Exception as e:
        print(f"   ❌ Erro no TenantMiddleware: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Verificar EmailVerificationMiddleware
    print("\n5. VERIFICANDO EMAIL VERIFICATION MIDDLEWARE:")
    try:
        from saas.middleware import EmailVerificationMiddleware
        email_middleware = EmailVerificationMiddleware(lambda r: None)
        
        response = email_middleware.process_request(request)
        
        if response:
            print(f"   ❌ EmailVerificationMiddleware retornou resposta: {response}")
            print(f"      Status: {response.status_code}")
            if hasattr(response, 'url'):
                print(f"      Redirect URL: {response.url}")
        else:
            print(f"   ✓ EmailVerificationMiddleware passou")
            
    except Exception as e:
        print(f"   ❌ Erro no EmailVerificationMiddleware: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Testar com Django Test Client
    print("\n6. TESTANDO COM DJANGO TEST CLIENT:")
    client = Client()
    
    # Configurar sessão no client
    session = client.session
    session_data = valid_session.get_decoded()
    for key, value in session_data.items():
        session[key] = value
    session.save()
    
    print(f"   ✓ Sessão configurada no client")
    print(f"   📋 Session key: {session.session_key}")
    
    # Fazer requisição
    response = client.get('/imoveis/bancas/mapa/', HTTP_HOST='127.0.0.1:8000')
    
    print(f"   📊 Status da resposta: {response.status_code}")
    
    if response.status_code == 302:
        print(f"   🔄 Redirecionamento para: {response.url}")
    elif response.status_code == 200:
        print(f"   ✅ Sucesso! Página carregada")
        content = response.content.decode('utf-8')
        if 'Login' in content:
            print(f"   ⚠️  Mas o conteúdo ainda é a página de login")
        elif 'Mapa' in content:
            print(f"   ✅ Conteúdo correto do mapa encontrado")
    else:
        print(f"   ❌ Status inesperado: {response.status_code}")

if __name__ == "__main__":
    test_http_session()