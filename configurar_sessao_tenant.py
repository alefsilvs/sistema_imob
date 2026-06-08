#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from saas.models import Tenant
import json

def configurar_sessao_tenant():
    print("=== CONFIGURAÇÃO DO TENANT NA SESSÃO ===")
    
    try:
        # Buscar usuário alef63134@gmail.com (ID: 2)
        user = User.objects.get(id=2)
        print(f"Usuário: {user.username} (ID: {user.id})")
        
        # Buscar tenant associado
        tenant = Tenant.objects.get(usuario_admin=user)
        print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Buscar sessões ativas do usuário
        sessions = Session.objects.filter(expire_date__gte=django.utils.timezone.now())
        print(f"\nSessões ativas encontradas: {sessions.count()}")
        
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                print(f"Sessão do usuário encontrada: {session.session_key}")
                print(f"Dados atuais: {session_data}")
                
                # Configurar tenant_id na sessão
                session_data['tenant_id'] = tenant.id
                
                # Usar o SessionStore para codificar os dados
                from django.contrib.sessions.backends.db import SessionStore
                store = SessionStore(session_key=session.session_key)
                store.update(session_data)
                store.save()
                
                print(f"✓ tenant_id configurado na sessão: {tenant.id}")
                print(f"Novos dados: {session.get_decoded()}")
                break
        else:
            print("⚠ Nenhuma sessão ativa encontrada para o usuário")
            print("O usuário precisa fazer login novamente")
            
    except User.DoesNotExist:
        print("❌ Usuário não encontrado")
    except Tenant.DoesNotExist:
        print("❌ Tenant não encontrado para o usuário")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    configurar_sessao_tenant()