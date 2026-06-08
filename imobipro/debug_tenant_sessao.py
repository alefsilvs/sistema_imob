#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant
from django.test import Client
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_tenant_sessao():
    """Debug para verificar o estado da sessão e tenant do usuário"""
    print("=== DEBUG TENANT SESSÃO ===")
    print()
    
    # Listar usuários disponíveis
    usuarios = User.objects.all()
    print("👥 USUÁRIOS DISPONÍVEIS:")
    for user in usuarios:
        print(f"   - {user.username} (ID: {user.id}) - Email: {user.email}")
    print()
    
    # Listar tenants disponíveis
    tenants = Tenant.objects.all()
    print("🏢 TENANTS DISPONÍVEIS:")
    for tenant in tenants:
        print(f"   - {tenant.nome_empresa} (ID: {tenant.id}) - Admin: {tenant.usuario_admin.username} - Status: {tenant.status}")
    print()
    
    if not usuarios.exists():
        print("❌ Nenhum usuário encontrado!")
        return
        
    if not tenants.exists():
        print("❌ Nenhum tenant encontrado!")
        return
    
    # Usar o primeiro usuário disponível
    user = usuarios.first()
    print(f"🔍 TESTANDO COM USUÁRIO: {user.username}")
    print()
    
    # Verificar se o usuário tem tenant associado
    tenant_do_usuario = tenants.filter(usuario_admin=user).first()
    if tenant_do_usuario:
        print(f"✅ Usuário tem tenant associado: {tenant_do_usuario.nome_empresa} (ID: {tenant_do_usuario.id})")
    else:
        print("❌ Usuário não tem tenant associado!")
        # Usar o primeiro tenant disponível para teste
        tenant_do_usuario = tenants.first()
        print(f"🔄 Usando primeiro tenant disponível: {tenant_do_usuario.nome_empresa}")
    print()
    
    # Teste 1: Simular login e verificar sessão
    print("🧪 TESTE 1: SIMULAÇÃO DE LOGIN")
    client = Client()
    
    # Fazer login
    client.force_login(user)
    print(f"   ✅ Login realizado para: {user.username}")
    
    # Verificar sessão
    session = client.session
    tenant_id_sessao = session.get('tenant_id')
    print(f"   📋 tenant_id na sessão: {tenant_id_sessao}")
    
    if tenant_id_sessao:
        try:
            tenant_sessao = Tenant.objects.get(id=tenant_id_sessao)
            print(f"   ✅ Tenant da sessão encontrado: {tenant_sessao.nome_empresa}")
        except Tenant.DoesNotExist:
            print(f"   ❌ Tenant ID {tenant_id_sessao} não existe!")
    else:
        print("   ⚠️  Nenhum tenant_id na sessão - configurando manualmente...")
        session['tenant_id'] = tenant_do_usuario.id
        session.save()
        print(f"   ✅ tenant_id configurado manualmente: {tenant_do_usuario.id}")
    print()
    
    # Teste 2: Acessar página de layouts
    print("🧪 TESTE 2: ACESSO À PÁGINA DE LAYOUTS")
    try:
        response = client.get('/layouts/', follow=True)
        print(f"   📊 Status da resposta: {response.status_code}")
        print(f"   📍 URL final: {response.request['PATH_INFO']}")
        
        if response.status_code == 200:
            print("   ✅ Acesso bem-sucedido!")
            # Verificar se há layouts no contexto
            if hasattr(response, 'context') and response.context:
                layouts = response.context.get('layouts')
                if layouts is not None:
                    print(f"   📋 Layouts encontrados: {len(layouts)}")
                else:
                    print("   ⚠️  Nenhum layout no contexto")
        else:
            print("   ❌ Acesso negado ou erro!")
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar página: {e}")
    print()
    
    # Teste 3: Verificar middleware diretamente
    print("🧪 TESTE 3: TESTE DIRETO DO MIDDLEWARE")
    from django.test import RequestFactory
    from saas.middleware import TenantMiddleware
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.auth.middleware import AuthenticationMiddleware
    
    factory = RequestFactory()
    request = factory.get('/layouts/')
    request.user = user
    
    # Aplicar SessionMiddleware
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session['tenant_id'] = tenant_do_usuario.id
    request.session.save()
    
    # Aplicar AuthenticationMiddleware
    auth_middleware = AuthenticationMiddleware(lambda req: None)
    auth_middleware.process_request(request)
    
    # Aplicar TenantMiddleware
    tenant_middleware = TenantMiddleware()
    response = tenant_middleware.process_request(request)
    
    if response is not None:
        print(f"   ❌ TenantMiddleware bloqueou a requisição: {response}")
    else:
        if hasattr(request, 'tenant'):
            print(f"   ✅ TenantMiddleware configurou tenant: {request.tenant.nome_empresa}")
        else:
            print("   ❌ TenantMiddleware não configurou tenant!")
    print()
    
    # Teste 4: Verificar logs
    print("🧪 TESTE 4: VERIFICAÇÃO DE LOGS")
    print("   📝 Verifique os logs do Django para mensagens de debug do TenantMiddleware")
    print("   🔍 Procure por mensagens como 'DEBUG: tenant_id da sessão' e 'request.tenant configurado'")
    print()
    
    print("=== RESUMO ===")
    print(f"✅ Usuário testado: {user.username}")
    print(f"✅ Tenant usado: {tenant_do_usuario.nome_empresa} (ID: {tenant_do_usuario.id})")
    print(f"✅ Status do tenant: {tenant_do_usuario.status}")
    print("📋 Se ainda houver erro de 'Acesso negado', verifique:")
    print("   1. Se o signal configurar_tenant_na_sessao está sendo executado")
    print("   2. Se o middleware TenantMiddleware está na ordem correta")
    print("   3. Se há outros middlewares interferindo")
    print("   4. Se o usuário é realmente o admin do tenant")

if __name__ == '__main__':
    debug_tenant_sessao()