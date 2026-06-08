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
from django.contrib.messages.middleware import MessageMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from django.middleware.common import CommonMiddleware
from django.db import transaction
from core.models import Inquilino
from core.forms import InquilinoForm
from saas.models import Tenant
import importlib

def debug_middleware_interferencia():
    """Debug específico para identificar middleware que interfere no save"""
    print("=== DEBUG MIDDLEWARE INTERFERÊNCIA ===")
    print()
    
    # Criar dados de teste
    try:
        # Buscar ou criar tenant
        tenant = Tenant.objects.first()
        if not tenant:
            print("❌ Nenhum tenant encontrado!")
            return
            
        # Buscar ou criar usuário
        user = User.objects.first()
        if not user:
            print("❌ Nenhum usuário encontrado!")
            return
            
        print(f"✅ Usando tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"✅ Usando usuário: {user.username}")
        print()
        
        # Dados do inquilino
        dados_inquilino = {
            'nome': 'João Silva Middleware Test',
            'cpf': '12345678901',
            'email': 'joao.middleware@test.com',
            'telefone': '11999999999',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-567'
        }
        
        # Lista de middlewares para testar
        middlewares_para_testar = [
            'saas.middleware.TenantMiddleware',
            'saas.middleware.TenantDatabaseMiddleware', 
            'saas.middleware.TenantSecurityMiddleware',
            'assinaturas.middleware.ControleAssinaturaMiddleware',
            'assinaturas.middleware.LimiteRecursosMiddleware',
            'saas.middleware_pkg.trial_middleware.TrialMiddleware',
            'security.middleware.SecurityMiddleware',
            'security.middleware.MasterUserMiddleware',
            'security.middleware.AuditMiddleware',
        ]
        
        factory = RequestFactory()
        
        for middleware_name in middlewares_para_testar:
            print(f"🔍 TESTANDO MIDDLEWARE: {middleware_name}")
            
            try:
                # Importar o middleware
                module_path, class_name = middleware_name.rsplit('.', 1)
                module = importlib.import_module(module_path)
                middleware_class = getattr(module, class_name)
                
                # Criar request simulado
                request = factory.post('/inquilinos/cadastrar/', dados_inquilino)
                request.user = user
                request.tenant = tenant
                request.tenant_id = tenant.id
                
                # Adicionar sessão
                session_middleware = SessionMiddleware(lambda req: None)
                session_middleware.process_request(request)
                request.session.save()
                
                # Adicionar autenticação
                auth_middleware = AuthenticationMiddleware(lambda req: None)
                auth_middleware.process_request(request)
                
                # Contar inquilinos antes
                inquilinos_antes = Inquilino.objects.filter(tenant=tenant).count()
                
                # Aplicar o middleware
                if hasattr(middleware_class, 'process_request'):
                    # Middleware antigo
                    middleware_instance = middleware_class()
                    response = middleware_instance.process_request(request)
                else:
                    # Middleware novo
                    middleware_instance = middleware_class(lambda req: None)
                    response = middleware_instance(request)
                
                # Se o middleware retornou uma resposta, ele bloqueou
                if response is not None:
                    print(f"   ❌ MIDDLEWARE BLOQUEOU! Resposta: {type(response)} - Status: {getattr(response, 'status_code', 'N/A')}")
                    if hasattr(response, 'content'):
                        content = response.content.decode('utf-8')[:200]
                        print(f"   📄 Conteúdo: {content}...")
                    continue
                
                # Tentar salvar inquilino após middleware
                try:
                    with transaction.atomic():
                        form = InquilinoForm(dados_inquilino)
                        if form.is_valid():
                            inquilino = form.save(commit=False)
                            inquilino.tenant = tenant
                            inquilino.save()
                            
                            # Verificar se foi salvo
                            inquilinos_depois = Inquilino.objects.filter(tenant=tenant).count()
                            
                            if inquilinos_depois > inquilinos_antes:
                                print(f"   ✅ MIDDLEWARE OK - Inquilino salvo com sucesso")
                                # Limpar o inquilino criado
                                inquilino.delete()
                            else:
                                print(f"   ❌ MIDDLEWARE SUSPEITO - Inquilino não foi salvo")
                        else:
                            print(f"   ⚠️  Formulário inválido: {form.errors}")
                            
                except Exception as e:
                    print(f"   ❌ ERRO NO SAVE: {e}")
                    
            except ImportError as e:
                print(f"   ⚠️  Middleware não encontrado: {e}")
            except Exception as e:
                print(f"   ❌ ERRO NO TESTE: {e}")
                
            print()
        
        print("=== TESTE ESPECÍFICO DO TENANTDATABASEMIDDLEWARE ===")
        
        # Teste específico do TenantDatabaseMiddleware
        try:
            from saas.middleware import TenantDatabaseMiddleware
            
            request = factory.post('/inquilinos/cadastrar/', dados_inquilino)
            request.user = user
            request.tenant = tenant
            
            # Aplicar middleware
            middleware = TenantDatabaseMiddleware()
            middleware.process_request(request)
            
            print(f"✅ TenantDatabaseMiddleware aplicado")
            print(f"   request.tenant_id: {getattr(request, 'tenant_id', 'N/A')}")
            
            # Verificar se tenant_id está correto
            if hasattr(request, 'tenant_id') and request.tenant_id == tenant.id:
                print(f"   ✅ tenant_id configurado corretamente: {request.tenant_id}")
            else:
                print(f"   ❌ tenant_id incorreto ou não configurado")
                
        except Exception as e:
            print(f"❌ Erro no teste específico: {e}")
            
        print()
        print("=== TESTE COM TODOS OS MIDDLEWARES ATIVOS ===")
        
        # Teste com client real (todos os middlewares)
        client = Client()
        
        # Login
        client.force_login(user)
        
        # Definir tenant na sessão
        session = client.session
        session['tenant_id'] = tenant.id
        session.save()
        
        # Contar antes
        inquilinos_antes = Inquilino.objects.filter(tenant=tenant).count()
        print(f"Inquilinos antes: {inquilinos_antes}")
        
        # Fazer POST
        response = client.post('/inquilinos/cadastrar/', dados_inquilino, follow=True)
        
        # Contar depois
        inquilinos_depois = Inquilino.objects.filter(tenant=tenant).count()
        print(f"Inquilinos depois: {inquilinos_depois}")
        print(f"Status da resposta: {response.status_code}")
        
        if inquilinos_depois > inquilinos_antes:
            print("✅ Com todos os middlewares: SUCESSO")
            # Limpar
            Inquilino.objects.filter(tenant=tenant, nome='João Silva Middleware Test').delete()
        else:
            print("❌ Com todos os middlewares: FALHOU")
            
            # Verificar mensagens
            from django.contrib.messages import get_messages
            messages = list(get_messages(response.wsgi_request))
            if messages:
                print("📨 Mensagens:")
                for message in messages:
                    print(f"   - {message}")
                    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_middleware_interferencia()