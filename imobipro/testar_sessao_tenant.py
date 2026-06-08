#!/usr/bin/env python
"""
Script para testar e configurar a sessão do tenant
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from saas.models import Tenant

def configurar_sessao_tenant():
    """Configura a sessão do tenant para o usuário alef"""
    
    print("🔧 CONFIGURANDO SESSÃO DO TENANT")
    print("=" * 50)
    
    try:
        # Buscar usuário alef
        user = User.objects.get(username='alef')
        print(f"✓ Usuário encontrado: {user.username}")
        
        # Buscar tenant
        tenant = Tenant.objects.get(nome_empresa="Y.L. EMPREENDIMENTOS")
        print(f"✓ Tenant encontrado: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Verificar se o usuário é admin do tenant
        if tenant.usuario_admin == user:
            print(f"✓ Usuário {user.username} é admin do tenant {tenant.nome_empresa}")
        else:
            print(f"❌ Usuário {user.username} NÃO é admin do tenant {tenant.nome_empresa}")
            print(f"   Admin atual: {tenant.usuario_admin}")
            
            # Configurar usuário como admin do tenant
            tenant.usuario_admin = user
            tenant.save()
            print(f"✅ Usuário {user.username} configurado como admin do tenant")
        
        # Buscar sessões ativas do usuário
        print(f"\n🔍 VERIFICANDO SESSÕES ATIVAS:")
        
        # Listar todas as sessões
        sessions = Session.objects.all()
        user_sessions = []
        
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                user_sessions.append(session)
                print(f"  Sessão encontrada: {session.session_key}")
                print(f"    tenant_id: {session_data.get('tenant_id')}")
                print(f"    user_id: {session_data.get('_auth_user_id')}")
        
        if user_sessions:
            # Atualizar sessões existentes
            for session in user_sessions:
                session_data = session.get_decoded()
                session_data['tenant_id'] = tenant.id
                
                # Criar nova sessão com dados atualizados
                new_session = SessionStore()
                new_session.update(session_data)
                new_session.save()
                
                # Deletar sessão antiga
                session.delete()
                
                print(f"  ✅ Sessão atualizada: {new_session.session_key}")
                print(f"     tenant_id configurado: {tenant.id}")
        else:
            # Criar nova sessão
            new_session = SessionStore()
            new_session['_auth_user_id'] = str(user.id)
            new_session['tenant_id'] = tenant.id
            new_session.save()
            
            print(f"  ✅ Nova sessão criada: {new_session.session_key}")
            print(f"     tenant_id: {tenant.id}")
            print(f"     user_id: {user.id}")
        
        print(f"\n✅ CONFIGURAÇÃO CONCLUÍDA!")
        print(f"   Tenant: {tenant.nome_empresa}")
        print(f"   Admin: {user.username}")
        print(f"   Tenant ID: {tenant.id}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Usuário 'alef' não encontrado!")
        return False
    except Tenant.DoesNotExist:
        print("❌ Tenant 'Y.L. EMPREENDIMENTOS' não encontrado!")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    sucesso = configurar_sessao_tenant()
    
    if sucesso:
        print("\n💡 PRÓXIMOS PASSOS:")
        print("  1. Faça logout e login novamente no sistema")
        print("  2. Acesse o mapa das bancas")
        print("  3. O layout deve aparecer corretamente")
    else:
        print("\n❌ Falha na configuração da sessão!")