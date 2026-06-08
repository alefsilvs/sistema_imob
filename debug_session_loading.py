#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils import timezone
from django.conf import settings

def debug_session_loading():
    """Debug do carregamento de sessão pelo SessionMiddleware"""
    
    print("🔍 DEBUG DO CARREGAMENTO DE SESSÃO")
    print("=" * 60)
    
    try:
        # 1. Verificar sessões ativas no banco
        print("\n1. SESSÕES ATIVAS NO BANCO:")
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
        
        valid_session = None
        for session in active_sessions:
            try:
                data = session.get_decoded()
                user_id = data.get('_auth_user_id')
                tenant_id = data.get('tenant_id')
                
                print(f"   📋 Session: {session.session_key}")
                print(f"      User ID: {user_id}")
                print(f"      Tenant ID: {tenant_id}")
                print(f"      Expira: {session.expire_date}")
                print(f"      Dados: {data}")
                
                if user_id and tenant_id == 6:
                    valid_session = session
                    print(f"      ✅ SESSÃO VÁLIDA SELECIONADA")
                print()
            except Exception as e:
                print(f"   ❌ Erro na sessão {session.session_key}: {e}")
        
        if not valid_session:
            print("❌ Nenhuma sessão válida encontrada")
            return
        
        # 2. Testar carregamento manual da sessão
        print(f"\n2. TESTE MANUAL DE CARREGAMENTO:")
        print(f"   Session key: {valid_session.session_key}")
        
        # Criar request com cookie
        factory = RequestFactory()
        request = factory.get('/imoveis/bancas/mapa/')
        
        # Configurar cookie manualmente
        request.COOKIES = {'sessionid': valid_session.session_key}
        print(f"   Cookie configurado: {request.COOKIES}")
        
        # 3. Testar SessionMiddleware step by step
        print(f"\n3. TESTANDO SESSION MIDDLEWARE:")
        
        # Criar middleware
        session_middleware = SessionMiddleware(lambda req: None)
        
        # Verificar configurações de sessão
        print(f"   SESSION_ENGINE: {settings.SESSION_ENGINE}")
        print(f"   SESSION_COOKIE_NAME: {settings.SESSION_COOKIE_NAME}")
        print(f"   SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE}")
        print(f"   SESSION_COOKIE_DOMAIN: {getattr(settings, 'SESSION_COOKIE_DOMAIN', None)}")
        print(f"   SESSION_COOKIE_PATH: {getattr(settings, 'SESSION_COOKIE_PATH', '/')}")
        print(f"   SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}")
        print(f"   SESSION_COOKIE_HTTPONLY: {getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)}")
        
        # Processar request
        print(f"\n   🔄 Executando process_request...")
        session_middleware.process_request(request)
        
        print(f"   Session key após middleware: {request.session.session_key}")
        print(f"   Session data após middleware: {dict(request.session)}")
        print(f"   Session exists: {request.session.exists(request.session.session_key) if request.session.session_key else False}")
        
        # 4. Verificar se a sessão está sendo encontrada
        print(f"\n4. VERIFICAÇÃO DETALHADA:")
        
        if request.session.session_key:
            print(f"   ✅ Session key carregado: {request.session.session_key}")
            
            # Verificar se é a mesma sessão
            if request.session.session_key == valid_session.session_key:
                print(f"   ✅ Mesma sessão do banco!")
            else:
                print(f"   ⚠️ Sessão diferente!")
                print(f"      Esperado: {valid_session.session_key}")
                print(f"      Obtido: {request.session.session_key}")
            
            # Verificar dados
            session_data = dict(request.session)
            if session_data:
                print(f"   ✅ Dados carregados: {session_data}")
                
                user_id = session_data.get('_auth_user_id')
                tenant_id = session_data.get('tenant_id')
                
                print(f"   User ID: {user_id}")
                print(f"   Tenant ID: {tenant_id}")
                
                if user_id and tenant_id:
                    print(f"   ✅ Dados de autenticação presentes!")
                else:
                    print(f"   ❌ Dados de autenticação ausentes!")
            else:
                print(f"   ❌ Nenhum dado carregado!")
        else:
            print(f"   ❌ Session key não carregado!")
            
            # Tentar carregar manualmente
            print(f"\n   🔧 TENTANDO CARREGAMENTO MANUAL:")
            
            from django.contrib.sessions.backends.db import SessionStore
            
            session_store = SessionStore(session_key=valid_session.session_key)
            
            print(f"   Session store criado: {session_store.session_key}")
            print(f"   Session exists: {session_store.exists(valid_session.session_key)}")
            
            if session_store.exists(valid_session.session_key):
                session_data = session_store.load()
                print(f"   Dados carregados manualmente: {session_data}")
            else:
                print(f"   ❌ Sessão não existe no store!")
        
        # 5. Testar com diferentes configurações de cookie
        print(f"\n5. TESTANDO DIFERENTES CONFIGURAÇÕES DE COOKIE:")
        
        # Teste 1: Cookie com domínio
        request2 = factory.get('/imoveis/bancas/mapa/', HTTP_HOST='127.0.0.1:8000')
        request2.COOKIES = {'sessionid': valid_session.session_key}
        request2.META['HTTP_HOST'] = '127.0.0.1:8000'
        
        session_middleware2 = SessionMiddleware(lambda req: None)
        session_middleware2.process_request(request2)
        
        print(f"   Teste com HTTP_HOST: {dict(request2.session)}")
        
        # Teste 2: Cookie sem domínio específico
        request3 = factory.get('/imoveis/bancas/mapa/')
        request3.COOKIES = {'sessionid': valid_session.session_key}
        
        session_middleware3 = SessionMiddleware(lambda req: None)
        session_middleware3.process_request(request3)
        
        print(f"   Teste sem HTTP_HOST: {dict(request3.session)}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_session_loading()