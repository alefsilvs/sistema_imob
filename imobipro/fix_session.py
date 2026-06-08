#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
import django.utils.timezone as timezone

def fix_user_session():
    # Encontrar o usuário
    user = User.objects.get(username='alef63134@gmail.com')
    print(f'Usuário encontrado: {user.username}')
    
    # Atualizar todas as sessões do usuário
    sessions = Session.objects.filter(expire_date__gt=timezone.now())
    updated_sessions = 0
    
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            # Criar um novo SessionStore para codificar os dados
            store = SessionStore()
            data['tenant_id'] = 6
            session.session_data = store.encode(data)
            session.save()
            updated_sessions += 1
            print(f'Sessão atualizada com tenant_id: 6')
    
    print(f'Total de sessões atualizadas: {updated_sessions}')

if __name__ == '__main__':
    fix_user_session()