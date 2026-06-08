#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import requests

def test_correct_cookie():
    """Testar com o nome correto do cookie de sessão"""
    
    print("🔍 TESTANDO COM NOME CORRETO DO COOKIE")
    print("=" * 60)
    
    try:
        # 1. Verificar configuração
        print(f"SESSION_COOKIE_NAME configurado: {settings.SESSION_COOKIE_NAME}")
        
        # 2. Buscar sessão ativa
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
        
        valid_session = None
        for session in active_sessions:
            try:
                data = session.get_decoded()
                if data.get('_auth_user_id') and data.get('tenant_id') == 6:
                    valid_session = session
                    break
            except:
                continue
        
        if not valid_session:
            print("❌ Nenhuma sessão válida encontrada")
            return
        
        print(f"✓ Sessão válida: {valid_session.session_key}")
        
        # 3. Testar com requests usando nome correto do cookie
        print(f"\n🌐 TESTANDO REQUISIÇÃO HTTP COM COOKIE CORRETO:")
        
        cookies = {settings.SESSION_COOKIE_NAME: valid_session.session_key}
        print(f"   Cookie: {cookies}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
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
                
                # Verificar conteúdo
                if 'Login' in response.text:
                    print(f"   ⚠️  Ainda mostra página de login")
                elif 'Mapa' in response.text or 'mapa' in response.text:
                    print(f"   🎉 CONTEÚDO DO MAPA ENCONTRADO!")
                    
                    # Salvar conteúdo correto
                    with open('temp_mapa_cookie_correto.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"   💾 Conteúdo salvo em temp_mapa_cookie_correto.html")
                else:
                    print(f"   ❓ Conteúdo desconhecido")
                    
                    # Salvar para análise
                    with open('temp_response_analysis.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"   💾 Resposta salva para análise em temp_response_analysis.html")
            
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
        
        # 4. Testar com PowerShell/Invoke-WebRequest
        print(f"\n💻 TESTANDO COM POWERSHELL:")
        
        import subprocess
        
        cookie_header = f"{settings.SESSION_COOKIE_NAME}={valid_session.session_key}"
        
        powershell_cmd = [
            'powershell', '-Command',
            f'Invoke-WebRequest -Uri "http://127.0.0.1:8000/imoveis/bancas/mapa/" -Headers @{{"Cookie"="{cookie_header}"}} -OutFile "temp_mapa_powershell_correto.html"'
        ]
        
        try:
            result = subprocess.run(powershell_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"   ✅ PowerShell executado com sucesso")
                print(f"   💾 Arquivo salvo: temp_mapa_powershell_correto.html")
            else:
                print(f"   ❌ Erro no PowerShell: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Erro ao executar PowerShell: {e}")
        
        # 5. Comparar com Django Test Client
        print(f"\n🧪 COMPARANDO COM DJANGO TEST CLIENT:")
        
        user = User.objects.get(id=valid_session.get_decoded()['_auth_user_id'])
        
        client = Client()
        client.force_login(user)
        
        # Configurar tenant na sessão
        session = client.session
        session['tenant_id'] = 6
        session.save()
        
        response = client.get('/imoveis/bancas/mapa/')
        print(f"   📊 Status Django Client: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'Mapa' in content or 'mapa' in content:
                print(f"   ✅ Django Client funciona corretamente!")
            else:
                print(f"   ⚠️  Django Client com problema")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_correct_cookie()