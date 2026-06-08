#!/usr/bin/env python
"""
Script para testar se o decorator @login_required está funcionando
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
from saas.models import Tenant

def test_login_required():
    """Testa se o usuário está autenticado corretamente"""
    
    print("🔐 TESTANDO AUTENTICAÇÃO E @login_required")
    print("=" * 50)
    
    try:
        # Buscar usuário e tenant
        users = User.objects.filter(email='alef63134@gmail.com')
        print(f"✓ Usuários encontrados com este email: {users.count()}")
        
        for i, u in enumerate(users):
            print(f"  {i+1}. {u.username} (ID: {u.id}) - Ativo: {u.is_active}")
        
        # Usar o primeiro usuário ativo
        user = users.filter(is_active=True).first()
        if not user:
            user = users.first()
            
        print(f"✓ Usuário selecionado: {user.username} (ID: {user.id})")
        
        # Buscar tenant - pode ser que o usuário não seja admin, mas tenha acesso
        try:
            tenant = Tenant.objects.get(usuario_admin=user)
            print(f"✓ Tenant (como admin): {tenant.nome_empresa} (ID: {tenant.id})")
        except Tenant.DoesNotExist:
            # Tentar encontrar tenant pelo ID 6 que foi configurado na sessão
            try:
                tenant = Tenant.objects.get(id=6)
                print(f"✓ Tenant (ID 6): {tenant.nome_empresa} (ID: {tenant.id})")
                print(f"  - Admin do tenant: {tenant.usuario_admin.username}")
            except Tenant.DoesNotExist:
                print("❌ Nenhum tenant encontrado!")
                return
        
        print(f"✓ Usuário: {user.username} ({user.email})")
        print(f"✓ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        print(f"✓ Usuário ativo: {user.is_active}")
        print(f"✓ Usuário autenticado: {user.is_authenticated}")
        
        # Verificar sessões ativas
        sessions = Session.objects.all()
        print(f"\n📊 SESSÕES ATIVAS: {sessions.count()}")
        
        for session in sessions:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            tenant_id = data.get('tenant_id')
            
            if user_id:
                session_user = User.objects.get(pk=user_id)
                print(f"  ✓ Sessão: {session.session_key[:10]}...")
                print(f"    - Usuário: {session_user.username}")
                print(f"    - Tenant ID: {tenant_id}")
                print(f"    - Expira: {session.expire_date}")
        
        # Testar com Django Test Client
        print(f"\n🌐 TESTANDO COM DJANGO CLIENT:")
        
        client = Client()
        
        # Fazer login
        login_success = client.login(username=user.username, password='123456')  # Assumindo senha padrão
        print(f"  ✓ Login realizado: {login_success}")
        
        if not login_success:
            # Tentar com email
            login_success = client.login(username=user.email, password='123456')
            print(f"  ✓ Login com email: {login_success}")
        
        if login_success:
            # Configurar tenant_id na sessão
            session = client.session
            session['tenant_id'] = tenant.id
            session.save()
            print(f"  ✓ Tenant ID configurado na sessão: {tenant.id}")
            
            # Tentar acessar a página do mapa
            try:
                url = reverse('imoveis:mapa_bancas')
                print(f"  ✓ URL do mapa: {url}")
                
                response = client.get(url)
                print(f"  ✓ Status da resposta: {response.status_code}")
                
                if response.status_code == 200:
                    print("  ✅ ACESSO AUTORIZADO - Página carregada com sucesso!")
                    
                    # Verificar conteúdo
                    content = response.content.decode('utf-8')
                    if 'Mapa das Bancas da Feira' in content:
                        print("  ✅ CONTEÚDO CORRETO - Título encontrado!")
                    else:
                        print("  ⚠️ Conteúdo inesperado")
                        
                elif response.status_code == 302:
                    print(f"  ❌ REDIRECIONAMENTO - Para: {response.url}")
                else:
                    print(f"  ❌ ERRO - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Erro ao acessar URL: {e}")
        else:
            print("  ❌ FALHA NO LOGIN - Não foi possível autenticar")
            
            # Verificar se o usuário tem senha
            if user.has_usable_password():
                print("    - Usuário tem senha configurada")
            else:
                print("    - Usuário NÃO tem senha configurada")
                
                # Configurar senha padrão
                user.set_password('123456')
                user.save()
                print("    - Senha padrão configurada: 123456")
                
                # Tentar login novamente
                login_success = client.login(username=user.username, password='123456')
                print(f"    - Novo login: {login_success}")
        
    except User.DoesNotExist:
        print("❌ Usuário não encontrado!")
    except Tenant.DoesNotExist:
        print("❌ Tenant não encontrado!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_required()