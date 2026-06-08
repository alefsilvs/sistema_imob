#!/usr/bin/env python
import os
import sys
import django

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imobilpro.settings')
django.setup()

from django.conf import settings

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
import requests

print("🔍 VERIFICANDO VALIDADE DA SESSÃO")
print("=" * 60)

# Verificar sessões ativas
sessions = Session.objects.filter(expire_date__gt=timezone.now())
print(f"📊 Total de sessões ativas: {sessions.count()}")

for session in sessions:
    data = session.get_decoded()
    user_id = data.get('_auth_user_id')
    tenant_id = data.get('tenant_id')
    if user_id and tenant_id:
        try:
            user = User.objects.get(id=user_id)
            print(f"✓ Sessão válida: {session.session_key}")
            print(f"  👤 Usuário: {user.username} (ID: {user_id})")
            print(f"  🏢 Tenant ID: {tenant_id}")
            print(f"  ⏰ Expira em: {session.expire_date}")
            
            # Testar com esta sessão
            print(f"\n🌐 TESTANDO REQUISIÇÃO HTTP:")
            cookie = {settings.SESSION_COOKIE_NAME: session.session_key}
            print(f"   Cookie: {cookie}")
            
            try:
                response = requests.get(
                    'http://127.0.0.1:8000/imoveis/bancas/mapa/',
                    cookies=cookie,
                    timeout=10
                )
                print(f"   📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    if "Mapa das Bancas da Feira" in response.text:
                        print("   ✅ SUCESSO! Página do mapa carregada!")
                        with open('temp_mapa_sessao_valida.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print("   💾 Conteúdo salvo em temp_mapa_sessao_valida.html")
                        break
                    else:
                        print("   ❌ Redirecionado para login")
                elif response.status_code == 302:
                    print(f"   🔄 Redirecionamento para: {response.headers.get('Location', 'N/A')}")
                else:
                    print(f"   ❌ Erro: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Erro na requisição: {e}")
                
        except User.DoesNotExist:
            print(f"❌ Usuário ID {user_id} não encontrado")
            
print("\n🧪 CRIANDO NOVA SESSÃO DE TESTE")
print("=" * 60)

# Criar nova sessão com Django Test Client
client = Client()

# Fazer login com usuário conhecido
try:
    user = User.objects.get(username='alef')
    client.force_login(user)
    
    # Configurar tenant na sessão
    session = client.session
    session['tenant_id'] = 6
    session.save()
    
    print(f"✓ Nova sessão criada para usuário: {user.username}")
    print(f"✓ Tenant ID configurado: {session.get('tenant_id')}")
    print(f"✓ Session key: {session.session_key}")
    
    # Testar com a nova sessão
    print(f"\n🌐 TESTANDO COM NOVA SESSÃO:")
    cookie = {settings.SESSION_COOKIE_NAME: session.session_key}
    print(f"   Cookie: {cookie}")
    
    response = requests.get(
        'http://127.0.0.1:8000/imoveis/bancas/mapa/',
        cookies=cookie,
        timeout=10
    )
    print(f"   📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        if "Mapa das Bancas da Feira" in response.text:
            print("   ✅ SUCESSO! Nova sessão funcionou!")
            with open('temp_mapa_nova_sessao.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("   💾 Conteúdo salvo em temp_mapa_nova_sessao.html")
        else:
            print("   ❌ Redirecionado para login")
    elif response.status_code == 302:
        print(f"   🔄 Redirecionamento para: {response.headers.get('Location', 'N/A')}")
    else:
        print(f"   ❌ Erro: {response.status_code}")
        
except User.DoesNotExist:
    print("❌ Usuário 'alef' não encontrado")
except Exception as e:
    print(f"❌ Erro ao criar nova sessão: {e}")

print("\n✅ TESTE CONCLUÍDO")