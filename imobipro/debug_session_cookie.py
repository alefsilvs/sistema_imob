#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import Client
import requests

def debug_session_cookie():
    print("🔍 DEBUGANDO COOKIES DE SESSÃO")
    print("=" * 60)
    
    # 1. Verificar sessões ativas
    print("\n1. SESSÕES ATIVAS NO BANCO:")
    active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
    
    for session in active_sessions:
        try:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id')
            tenant_id = data.get('tenant_id')
            
            print(f"   📋 Session: {session.session_key}")
            print(f"      User ID: {user_id}")
            print(f"      Tenant ID: {tenant_id}")
            print(f"      Expira: {session.expire_date}")
            print()
        except Exception as e:
            print(f"   ❌ Erro na sessão {session.session_key}: {e}")
    
    # 2. Testar com requests library
    print("\n2. TESTANDO COM REQUESTS LIBRARY:")
    
    # Pegar uma sessão válida
    valid_session = None
    for session in active_sessions:
        try:
            data = session.get_decoded()
            if data.get('_auth_user_id') and data.get('tenant_id') == 6:
                valid_session = session
                break
        except:
            continue
    
    if valid_session:
        print(f"   ✓ Usando sessão: {valid_session.session_key}")
        
        # Fazer requisição com requests
        cookies = {'sessionid': valid_session.session_key}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(
                'http://127.0.0.1:8000/imoveis/bancas/mapa/',
                cookies=cookies,
                headers=headers,
                allow_redirects=False,
                timeout=10
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"   🔄 Redirecionamento para: {response.headers.get('Location', 'N/A')}")
            elif response.status_code == 200:
                print(f"   ✅ Sucesso!")
                if 'Login' in response.text:
                    print(f"   ⚠️  Mas ainda mostra página de login")
                elif 'Mapa' in response.text:
                    print(f"   ✅ Conteúdo do mapa encontrado")
            
            # Verificar cookies de resposta
            if response.cookies:
                print(f"   🍪 Cookies de resposta:")
                for cookie in response.cookies:
                    print(f"      {cookie.name}: {cookie.value}")
            
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
    
    # 3. Testar criando nova sessão
    print("\n3. CRIANDO NOVA SESSÃO:")
    
    try:
        # Buscar usuário
        user = User.objects.filter(email='alef63134@gmail.com', is_active=True).first()
        if user:
            print(f"   👤 Usuário: {user.username} (ID: {user.id})")
            
            # Criar client e fazer login
            client = Client()
            
            # Tentar fazer login programático
            login_success = client.force_login(user)
            print(f"   🔐 Login forçado: {'✓' if login_success is None else '✗'}")
            
            # Configurar tenant na sessão
            session = client.session
            session['tenant_id'] = 6
            session.save()
            
            print(f"   📋 Nova sessão criada: {session.session_key}")
            print(f"   🏢 Tenant ID configurado: {session.get('tenant_id')}")
            
            # Testar acesso
            response = client.get('/imoveis/bancas/mapa/')
            print(f"   📊 Status da resposta: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if 'Login' in content:
                    print(f"   ⚠️  Ainda mostra página de login")
                elif 'Mapa' in content:
                    print(f"   ✅ Conteúdo do mapa encontrado!")
                    
                    # Salvar conteúdo correto
                    with open('temp_mapa_correto.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   💾 Conteúdo salvo em temp_mapa_correto.html")
            
            elif response.status_code == 302:
                print(f"   🔄 Redirecionamento para: {response.url}")
        
        else:
            print(f"   ❌ Usuário não encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro ao criar nova sessão: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_session_cookie()