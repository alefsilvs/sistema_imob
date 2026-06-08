#!/usr/bin/env python
"""
Script para debugar a ordem dos middlewares e identificar qual está causando o redirecionamento
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from saas.models import Tenant
from django.utils.module_loading import import_string

def debug_middleware_order():
    """Debug da ordem dos middlewares"""
    
    print("🔍 DEBUG DA ORDEM DOS MIDDLEWARES")
    print("=" * 60)
    
    try:
        # Buscar usuário e tenant
        user = User.objects.filter(email='alef63134@gmail.com', is_active=True).first()
        tenant = Tenant.objects.get(id=6)
        
        print(f"✓ Usuário: {user.username} ({user.email})")
        print(f"✓ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Criar request factory
        factory = RequestFactory()
        request = factory.get('/imoveis/bancas/mapa/')
        
        # Configurar sessão básica
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session['tenant_id'] = tenant.id
        request.session['_auth_user_id'] = str(user.id)
        request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        request.session.save()
        
        # Configurar usuário e tenant
        request.user = user
        request.tenant = tenant
        
        print(f"\n📋 MIDDLEWARES CONFIGURADOS:")
        print(f"Total: {len(settings.MIDDLEWARE)}")
        
        # Testar cada middleware individualmente
        print(f"\n🧪 TESTANDO CADA MIDDLEWARE:")
        
        for i, middleware_path in enumerate(settings.MIDDLEWARE, 1):
            print(f"\n{i}. {middleware_path}")
            
            try:
                # Importar middleware
                middleware_class = import_string(middleware_path)
                middleware_instance = middleware_class(lambda req: None)
                
                # Testar process_request se existir
                if hasattr(middleware_instance, 'process_request'):
                    print(f"   ✓ Tem process_request")
                    
                    # Criar uma cópia do request para teste
                    test_request = factory.get('/imoveis/bancas/mapa/')
                    test_request.user = user
                    test_request.tenant = tenant
                    test_request.session = request.session
                    
                    # Executar middleware
                    result = middleware_instance.process_request(test_request)
                    
                    if result is None:
                        print(f"   ✅ PASSOU - Retornou None")
                    elif hasattr(result, 'status_code'):
                        print(f"   ❌ BLOQUEOU - Status: {result.status_code}")
                        if hasattr(result, 'url'):
                            print(f"      Redirecionando para: {result.url}")
                        elif result.status_code == 302 and hasattr(result, 'get'):
                            location = result.get('Location', 'N/A')
                            print(f"      Redirecionando para: {location}")
                        
                        # Se este middleware está bloqueando, investigar mais
                        if 'login' in str(result).lower() or result.status_code == 302:
                            print(f"   🔍 INVESTIGANDO MIDDLEWARE SUSPEITO:")
                            
                            # Verificar condições específicas
                            if 'TenantMiddleware' in middleware_path:
                                print(f"      - Verificando tenant no request: {hasattr(test_request, 'tenant')}")
                                print(f"      - Tenant: {getattr(test_request, 'tenant', None)}")
                                print(f"      - Sessão tenant_id: {test_request.session.get('tenant_id')}")
                                
                            elif 'EmailVerificationMiddleware' in middleware_path:
                                print(f"      - Verificando email verificado")
                                from saas.models import VerificacaoEmail
                                try:
                                    verificacao = VerificacaoEmail.objects.get(usuario=user)
                                    print(f"      - Email verificado: {verificacao.email_verificado}")
                                except VerificacaoEmail.DoesNotExist:
                                    print(f"      - Verificação de email não existe")
                                    
                            elif 'ControleAssinaturaMiddleware' in middleware_path:
                                print(f"      - Verificando assinatura do usuário")
                                
                            elif 'SecurityMiddleware' in middleware_path:
                                print(f"      - Verificando segurança")
                                
                    else:
                        print(f"   ⚠️ RETORNO INESPERADO: {type(result)}")
                        
                else:
                    print(f"   - Não tem process_request")
                    
            except Exception as e:
                print(f"   ❌ ERRO ao importar/testar: {e}")
        
        print(f"\n🎯 RESUMO:")
        print(f"✓ Request configurado corretamente")
        print(f"✓ Usuário autenticado: {user.is_authenticated}")
        print(f"✓ Tenant configurado: {tenant.id}")
        print(f"✓ Sessão configurada com tenant_id: {request.session.get('tenant_id')}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_middleware_order()