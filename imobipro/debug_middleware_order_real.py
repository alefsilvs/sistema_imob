#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.models import Session
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from saas.models import Tenant
from django.utils.module_loading import import_string
from django.utils import timezone

def debug_middleware_order_real():
    """Debug da ordem real dos middlewares com requisição HTTP simulada"""
    
    print("🔍 DEBUG DA ORDEM REAL DOS MIDDLEWARES")
    print("=" * 60)
    
    try:
        # Buscar sessão ativa real
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
        
        valid_session = None
        for session in active_sessions:
            try:
                data = session.get_decoded()
                if data.get('_auth_user_id') and data.get('tenant_id') == 6:
                    valid_session = session
                    break
            except:
                continue
        
        if not valid_session:
            print("❌ Nenhuma sessão válida encontrada")
            return
        
        session_data = valid_session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        tenant_id = session_data.get('tenant_id')
        
        user = User.objects.get(id=user_id)
        tenant = Tenant.objects.get(id=tenant_id)
        
        print(f"✓ Sessão: {valid_session.session_key}")
        print(f"✓ Usuário: {user.username} ({user.email})")
        print(f"✓ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Criar request simulando requisição HTTP real
        factory = RequestFactory()
        request = factory.get('/imoveis/bancas/mapa/', HTTP_HOST='127.0.0.1:8000')
        
        # Configurar cookies como em requisição real
        request.COOKIES = {'sessionid': valid_session.session_key}
        
        print(f"\n📋 PROCESSANDO MIDDLEWARES NA ORDEM REAL:")
        
        # Processar middlewares na ordem exata do settings
        for i, middleware_path in enumerate(settings.MIDDLEWARE, 1):
            print(f"\n{i}. {middleware_path}")
            
            try:
                # Importar middleware
                middleware_class = import_string(middleware_path)
                middleware_instance = middleware_class(lambda req: None)
                
                # Verificar se tem process_request
                if hasattr(middleware_instance, 'process_request'):
                    print(f"   🔄 Executando process_request...")
                    
                    # Estado antes
                    user_before = getattr(request, 'user', 'Não definido')
                    tenant_before = getattr(request, 'tenant', 'Não definido')
                    session_before = getattr(request, 'session', None)
                    
                    print(f"      ANTES - User: {user_before}")
                    print(f"      ANTES - Tenant: {tenant_before}")
                    print(f"      ANTES - Session: {'Configurada' if session_before else 'Não configurada'}")
                    
                    # Executar middleware
                    result = middleware_instance.process_request(request)
                    
                    # Estado depois
                    user_after = getattr(request, 'user', 'Não definido')
                    tenant_after = getattr(request, 'tenant', 'Não definido')
                    session_after = getattr(request, 'session', None)
                    
                    print(f"      DEPOIS - User: {user_after}")
                    print(f"      DEPOIS - Tenant: {tenant_after}")
                    print(f"      DEPOIS - Session: {'Configurada' if session_after else 'Não configurada'}")
                    
                    if result is None:
                        print(f"   ✅ Passou (retornou None)")
                    else:
                        print(f"   🚨 BLOQUEOU! Retornou: {type(result)}")
                        
                        if hasattr(result, 'status_code'):
                            print(f"      Status: {result.status_code}")
                            
                        if hasattr(result, 'url'):
                            print(f"      Redirect URL: {result.url}")
                        elif hasattr(result, 'get') and 'Location' in result:
                            print(f"      Location: {result['Location']}")
                        
                        # Se este middleware bloqueou, investigar mais
                        print(f"\n   🔍 INVESTIGAÇÃO DETALHADA:")
                        
                        if 'TenantMiddleware' in middleware_path:
                            print(f"      - Request.user: {getattr(request, 'user', 'Não definido')}")
                            print(f"      - User.is_authenticated: {getattr(request.user, 'is_authenticated', False) if hasattr(request, 'user') else False}")
                            print(f"      - Session tenant_id: {request.session.get('tenant_id') if hasattr(request, 'session') else 'Sem sessão'}")
                            print(f"      - Request.tenant: {getattr(request, 'tenant', 'Não definido')}")
                            
                        elif 'EmailVerificationMiddleware' in middleware_path:
                            print(f"      - Verificando email do usuário...")
                            if hasattr(request, 'user') and request.user.is_authenticated:
                                from saas.models import VerificacaoEmail
                                try:
                                    verificacao = VerificacaoEmail.objects.get(usuario=request.user)
                                    print(f"      - Email verificado: {verificacao.email_verificado}")
                                except VerificacaoEmail.DoesNotExist:
                                    print(f"      - Verificação de email não existe")
                            else:
                                print(f"      - Usuário não autenticado")
                        
                        # PARAR aqui se middleware bloqueou
                        print(f"\n🛑 MIDDLEWARE {middleware_path} BLOQUEOU A REQUISIÇÃO!")
                        print(f"   Este é o middleware causador do problema.")
                        break
                        
                else:
                    print(f"   - Não tem process_request")
                    
            except Exception as e:
                print(f"   ❌ ERRO ao importar/testar: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎯 ESTADO FINAL DO REQUEST:")
        print(f"✓ User: {getattr(request, 'user', 'Não definido')}")
        print(f"✓ User authenticated: {getattr(request.user, 'is_authenticated', False) if hasattr(request, 'user') else False}")
        print(f"✓ Tenant: {getattr(request, 'tenant', 'Não definido')}")
        print(f"✓ Session: {'Configurada' if hasattr(request, 'session') else 'Não configurada'}")
        if hasattr(request, 'session'):
            print(f"✓ Session tenant_id: {request.session.get('tenant_id')}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_middleware_order_real()