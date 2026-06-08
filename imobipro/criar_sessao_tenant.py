import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import login
from django.test import RequestFactory
from saas.models import Tenant

print("=== CRIANDO SESSÃO COM TENANT ===")

# Buscar usuário
user = User.objects.get(username='alef')
print(f"Usuário: {user.username} (ID: {user.id})")

# Buscar tenant do usuário
tenant = Tenant.objects.filter(usuario_admin=user).first()
if not tenant:
    print("❌ Usuário não é admin de nenhum tenant!")
    exit(1)
print(f"Tenant do usuário: ID {tenant.id} - {tenant.nome_empresa}")

# Criar uma nova sessão
from django.contrib.sessions.backends.db import SessionStore

session = SessionStore()
session['_auth_user_id'] = str(user.id)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['tenant_id'] = tenant.id

# Salvar a sessão
session.save()

print(f"✅ Nova sessão criada com session_key: {session.session_key}")
print(f"   - auth_user_id: {session['_auth_user_id']}")
print(f"   - tenant_id: {session['tenant_id']}")

# Verificar se a sessão foi salva corretamente
saved_session = Session.objects.get(session_key=session.session_key)
data = saved_session.get_decoded()
print(f"✅ Sessão verificada:")
print(f"   - auth_user_id: {data.get('_auth_user_id')}")
print(f"   - tenant_id: {data.get('tenant_id')}")

print("\n📋 INSTRUÇÕES:")
print("1. Faça logout do sistema")
print("2. Faça login novamente com o usuário 'alef'")
print("3. Teste o mapa das bancas")