#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.db import transaction
from core.models import Inquilino
from core.forms import InquilinoForm
from saas.models import Tenant

def debug_middleware_simples():
    """Debug simples para identificar o problema"""
    print("=== DEBUG MIDDLEWARE SIMPLES ===")
    print()
    
    try:
        # Buscar dados
        tenant = Tenant.objects.first()
        user = User.objects.first()
        
        if not tenant or not user:
            print("❌ Tenant ou usuário não encontrado!")
            return
            
        print(f"✅ Tenant: {tenant.nome_empresa}")
        print(f"✅ Usuário: {user.username}")
        print()
        
        # Dados do inquilino
        dados_inquilino = {
            'nome': 'João Silva Simples',
            'cpf': '12345678901',
            'email': 'joao.simples@test.com',
            'telefone': '11999999999',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-567'
        }
        
        print("1. TESTE DIRETO DO FORMULÁRIO (SEM MIDDLEWARES):")
        
        # Teste direto do formulário
        try:
            with transaction.atomic():
                form = InquilinoForm(dados_inquilino)
                if form.is_valid():
                    inquilino = form.save(commit=False)
                    inquilino.tenant = tenant
                    inquilino.save()
                    print(f"   ✅ Inquilino salvo diretamente: ID {inquilino.id}")
                    inquilino.delete()  # Limpar
                else:
                    print(f"   ❌ Formulário inválido: {form.errors}")
        except Exception as e:
            print(f"   ❌ Erro no save direto: {e}")
            
        print()
        print("2. TESTE COM APENAS TENANT MIDDLEWARES:")
        
        # Teste com apenas middlewares de tenant
        try:
            from saas.middleware import TenantMiddleware, TenantDatabaseMiddleware
            
            factory = RequestFactory()
            request = factory.post('/inquilinos/cadastrar/', dados_inquilino)
            request.user = user
            
            # Aplicar TenantMiddleware
            tenant_middleware = TenantMiddleware()
            
            # Simular sessão com tenant_id
            session_middleware = SessionMiddleware(lambda req: None)
            session_middleware.process_request(request)
            request.session['tenant_id'] = tenant.id
            request.session.save()
            
            # Aplicar middleware de autenticação
            auth_middleware = AuthenticationMiddleware(lambda req: None)
            auth_middleware.process_request(request)
            
            # Aplicar tenant middleware
            response = tenant_middleware.process_request(request)
            
            if response is not None:
                print(f"   ❌ TenantMiddleware bloqueou: {response}")
            else:
                print(f"   ✅ TenantMiddleware OK - Tenant: {getattr(request, 'tenant', 'N/A')}")
                
                # Aplicar TenantDatabaseMiddleware
                db_middleware = TenantDatabaseMiddleware()
                db_response = db_middleware.process_request(request)
                
                if db_response is not None:
                    print(f"   ❌ TenantDatabaseMiddleware bloqueou: {db_response}")
                else:
                    print(f"   ✅ TenantDatabaseMiddleware OK - tenant_id: {getattr(request, 'tenant_id', 'N/A')}")
                    
                    # Tentar salvar
                    try:
                        with transaction.atomic():
                            form = InquilinoForm(dados_inquilino)
                            if form.is_valid():
                                inquilino = form.save(commit=False)
                                inquilino.tenant = tenant
                                inquilino.save()
                                print(f"   ✅ Inquilino salvo com middlewares de tenant: ID {inquilino.id}")
                                inquilino.delete()  # Limpar
                            else:
                                print(f"   ❌ Formulário inválido: {form.errors}")
                    except Exception as e:
                        print(f"   ❌ Erro no save com middlewares: {e}")
                        
        except Exception as e:
            print(f"   ❌ Erro no teste com middlewares: {e}")
            
        print()
        print("3. TESTE COM CLIENT (TODOS OS MIDDLEWARES ATIVOS):")
        
        # Desabilitar temporariamente middlewares problemáticos
        middlewares_originais = settings.MIDDLEWARE.copy()
        
        # Remover middlewares de segurança problemáticos
        middlewares_filtrados = [
            m for m in middlewares_originais 
            if not m.startswith('security.middleware.LoginSecurityMiddleware')
        ]
        
        settings.MIDDLEWARE = middlewares_filtrados
        
        try:
            client = Client()
            client.force_login(user)
            
            # Definir tenant na sessão
            session = client.session
            session['tenant_id'] = tenant.id
            session.save()
            
            # Contar antes
            inquilinos_antes = Inquilino.objects.filter(tenant=tenant).count()
            print(f"   Inquilinos antes: {inquilinos_antes}")
            
            # Fazer POST
            response = client.post('/inquilinos/cadastrar/', dados_inquilino, follow=True)
            
            # Contar depois
            inquilinos_depois = Inquilino.objects.filter(tenant=tenant).count()
            print(f"   Inquilinos depois: {inquilinos_depois}")
            print(f"   Status da resposta: {response.status_code}")
            
            if inquilinos_depois > inquilinos_antes:
                print("   ✅ Com middlewares filtrados: SUCESSO")
                # Limpar
                Inquilino.objects.filter(tenant=tenant, nome='João Silva Simples').delete()
            else:
                print("   ❌ Com middlewares filtrados: FALHOU")
                
                # Verificar mensagens
                from django.contrib.messages import get_messages
                messages = list(get_messages(response.wsgi_request))
                if messages:
                    print("   📨 Mensagens:")
                    for message in messages:
                        print(f"      - {message}")
                        
        except Exception as e:
            print(f"   ❌ Erro no teste com client: {e}")
        finally:
            # Restaurar middlewares originais
            settings.MIDDLEWARE = middlewares_originais
            
        print()
        print("4. VERIFICANDO CONFIGURAÇÃO ATUAL DOS MIDDLEWARES:")
        
        middlewares_problematicos = [
            'security.middleware.LoginSecurityMiddleware',
            'assinaturas.middleware.ControleAssinaturaMiddleware',
            'saas.middleware_pkg.trial_middleware.TrialMiddleware',
        ]
        
        for middleware in middlewares_problematicos:
            if middleware in settings.MIDDLEWARE:
                print(f"   ❌ {middleware} - ATIVO (pode causar problemas)")
            else:
                print(f"   ✅ {middleware} - INATIVO")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_middleware_simples()