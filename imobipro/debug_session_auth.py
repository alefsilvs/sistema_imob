#!/usr/bin/env python
import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from saas.models import Tenant
import json

def debug_session_auth():
    print("🔍 DEBUGANDO SESSÕES E AUTENTICAÇÃO")
    print("=" * 60)
    
    # 1. Verificar todas as sessões ativas
    print("\n1. SESSÕES ATIVAS:")
    active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
    print(f"   Total de sessões ativas: {active_sessions.count()}")
    
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            tenant_id = session_data.get('tenant_id')
            
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    user = None
            
            print(f"   📋 Session Key: {session.session_key}")
            print(f"      User ID: {user_id} ({'✓' if user else '✗'})")
            if user:
                print(f"      User: {user.username} ({user.email}) - Ativo: {user.is_active}")
            print(f"      Tenant ID: {tenant_id}")
            print(f"      Expira em: {session.expire_date}")
            print(f"      Dados: {json.dumps(session_data, indent=2, default=str)}")
            print()
        except Exception as e:
            print(f"   ❌ Erro ao decodificar sessão {session.session_key}: {e}")
    
    # 2. Verificar usuário específico
    print("\n2. USUÁRIO ESPECÍFICO (alef63134@gmail.com):")
    try:
        users = User.objects.filter(email='alef63134@gmail.com')
        print(f"   Usuários encontrados: {users.count()}")
        
        for user in users:
            print(f"   👤 User: {user.username} (ID: {user.id})")
            print(f"      Email: {user.email}")
            print(f"      Ativo: {user.is_active}")
            print(f"      Staff: {user.is_staff}")
            print(f"      Superuser: {user.is_superuser}")
            print(f"      Último login: {user.last_login}")
            print(f"      Data criação: {user.date_joined}")
            
            # Verificar se tem sessões ativas
            user_sessions = Session.objects.filter(
                expire_date__gt=timezone.now()
            )
            user_active_sessions = []
            for sess in user_sessions:
                try:
                    data = sess.get_decoded()
                    if data.get('_auth_user_id') == str(user.id):
                        user_active_sessions.append(sess)
                except:
                    pass
            
            print(f"      Sessões ativas: {len(user_active_sessions)}")
            for sess in user_active_sessions:
                data = sess.get_decoded()
                print(f"        - {sess.session_key} (tenant: {data.get('tenant_id')})")
            print()
            
    except Exception as e:
        print(f"   ❌ Erro ao buscar usuário: {e}")
    
    # 3. Verificar tenant específico
    print("\n3. TENANT ESPECÍFICO (ID: 6):")
    try:
        tenant = Tenant.objects.get(id=6)
        print(f"   🏢 Tenant: {tenant.nome} (ID: {tenant.id})")
        print(f"      Ativo: {tenant.ativo}")
        print(f"      Admin: {tenant.admin.username if tenant.admin else 'Nenhum'}")
        print(f"      Admin Email: {tenant.admin.email if tenant.admin else 'Nenhum'}")
        print(f"      Admin Ativo: {tenant.admin.is_active if tenant.admin else 'N/A'}")
    except Exception as e:
        print(f"   ❌ Erro ao buscar tenant: {e}")
    
    # 4. Testar autenticação programática
    print("\n4. TESTE DE AUTENTICAÇÃO PROGRAMÁTICA:")
    try:
        from django.contrib.auth import authenticate
        
        # Tentar autenticar com diferentes combinações
        user = User.objects.filter(email='alef63134@gmail.com', is_active=True).first()
        if user:
            print(f"   👤 Testando usuário: {user.username}")
            
            # Verificar se tem senha
            if user.password:
                print(f"   🔐 Usuário tem senha configurada: ✓")
                print(f"      Hash da senha: {user.password[:50]}...")
                
                # Tentar autenticar com username
                auth_user = authenticate(username=user.username, password='123456')  # senha comum
                print(f"   🔑 Autenticação com username '123456': {'✓' if auth_user else '✗'}")
                
                # Tentar outras senhas comuns
                common_passwords = ['admin', 'password', '12345', 'alef', user.username]
                for pwd in common_passwords:
                    auth_user = authenticate(username=user.username, password=pwd)
                    if auth_user:
                        print(f"   🔑 Autenticação com senha '{pwd}': ✓")
                        break
                else:
                    print(f"   🔑 Nenhuma senha comum funcionou")
            else:
                print(f"   🔐 Usuário NÃO tem senha configurada: ✗")
        else:
            print(f"   ❌ Nenhum usuário ativo encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro no teste de autenticação: {e}")

if __name__ == "__main__":
    debug_session_auth()