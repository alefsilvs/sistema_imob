#!/usr/bin/env python
"""
Script para testar acesso direto à view mapa_bancas_feira
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from saas.models import Tenant
from imoveis.views import mapa_bancas_feira

def test_direct_access():
    """Testa acesso direto à view"""
    
    print("🎯 TESTANDO ACESSO DIRETO À VIEW")
    print("=" * 50)
    
    try:
        # Buscar usuário e tenant
        user = User.objects.filter(email='alef63134@gmail.com', is_active=True).first()
        tenant = Tenant.objects.get(id=6)
        
        print(f"✓ Usuário: {user.username} ({user.email})")
        print(f"✓ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"✓ Usuário autenticado: {user.is_authenticated}")
        
        # Criar request factory
        factory = RequestFactory()
        request = factory.get('/imoveis/bancas/mapa/')
        
        # Configurar sessão
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session['tenant_id'] = tenant.id
        request.session['_auth_user_id'] = str(user.id)
        request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        request.session.save()
        
        # Configurar usuário e tenant
        request.user = user
        request.tenant = tenant
        
        print(f"✓ Request configurado:")
        print(f"  - Usuário: {request.user}")
        print(f"  - Tenant: {request.tenant}")
        print(f"  - Sessão tenant_id: {request.session.get('tenant_id')}")
        print(f"  - Sessão user_id: {request.session.get('_auth_user_id')}")
        
        # Testar se o usuário passa pelo @login_required
        print(f"\n🔐 TESTANDO @login_required:")
        print(f"  - user.is_authenticated: {request.user.is_authenticated}")
        print(f"  - user.is_active: {request.user.is_active}")
        
        if not request.user.is_authenticated:
            print("  ❌ Usuário não está autenticado - @login_required vai redirecionar")
            return
        
        # Chamar a view diretamente
        print(f"\n📋 EXECUTANDO VIEW mapa_bancas_feira:")
        
        try:
            response = mapa_bancas_feira(request)
            print(f"  ✅ View executada com sucesso!")
            print(f"  ✓ Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ SUCESSO - Página carregada!")
                
                # Verificar conteúdo
                content = response.content.decode('utf-8')
                if 'Mapa das Bancas da Feira' in content:
                    print("  ✅ CONTEÚDO CORRETO - Título encontrado!")
                elif 'login' in content.lower():
                    print("  ❌ AINDA REDIRECIONANDO PARA LOGIN")
                else:
                    print("  ⚠️ Conteúdo inesperado")
                    
            elif response.status_code == 302:
                print(f"  ❌ REDIRECIONAMENTO - Para: {response.get('Location', 'N/A')}")
            else:
                print(f"  ❌ ERRO - Status: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro ao executar view: {e}")
            import traceback
            traceback.print_exc()
        
        # Verificar dados do banco para a view
        print(f"\n📊 DADOS DISPONÍVEIS PARA A VIEW:")
        from imoveis.models import LayoutFeira, BancaFeira
        
        layouts = LayoutFeira.objects.filter(tenant=tenant)
        bancas = BancaFeira.objects.filter(tenant=tenant)
        
        print(f"  ✓ Layouts: {layouts.count()}")
        print(f"  ✓ Bancas: {bancas.count()}")
        
        if layouts.exists():
            layout = layouts.first()
            print(f"  ✓ Primeiro layout: {layout.nome} (Setor: {layout.setor})")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_access()