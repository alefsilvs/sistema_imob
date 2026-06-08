#!/usr/bin/env python
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import PerfilUsuario, UsuarioPerfil

def test_header_with_authentication():
    """Testa o header com autenticação real do Django"""
    print("🔍 TESTANDO HEADER COM AUTENTICAÇÃO")
    print("=" * 50)
    
    # Usar requests.Session para manter cookies
    session = requests.Session()
    
    try:
        # 1. Acessar página de login
        print("1. Acessando página de login...")
        login_page = session.get('http://127.0.0.1:8000/accounts/login/')
        print(f"   Status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            print("❌ Erro ao acessar página de login")
            return
        
        # 2. Extrair CSRF token
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_token:
            print("❌ CSRF token não encontrado")
            return
        
        csrf_value = csrf_token['value']
        print(f"   CSRF token obtido: {csrf_value[:20]}...")
        
        # 3. Fazer login
        print("2. Fazendo login...")
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_value
        }
        
        login_response = session.post('http://127.0.0.1:8000/accounts/login/', data=login_data)
        print(f"   Status do login: {login_response.status_code}")
        
        # 4. Testar diferentes páginas
        pages_to_test = [
            ('Dashboard', 'http://127.0.0.1:8000/dashboard/'),
            ('Indicadores', 'http://127.0.0.1:8000/indicadores/dashboard/'),
            ('Imóveis', 'http://127.0.0.1:8000/imoveis/'),
            ('Contratos', 'http://127.0.0.1:8000/contratos/'),
        ]
        
        for page_name, url in pages_to_test:
            print(f"\n3. Testando página: {page_name}")
            try:
                response = session.get(url)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Verificar se há erro RelatedObjectDoesNotExist
                    if 'RelatedObjectDoesNotExist' in response.text:
                        print(f"   ❌ ERRO ENCONTRADO: RelatedObjectDoesNotExist em {page_name}")
                        
                        # Salvar HTML para análise
                        filename = f"error_{page_name.lower()}.html"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"   📄 HTML salvo em: {filename}")
                        
                        # Procurar linha específica do erro
                        lines = response.text.split('\n')
                        for i, line in enumerate(lines):
                            if 'RelatedObjectDoesNotExist' in line:
                                print(f"   🔍 Linha {i+1}: {line.strip()[:100]}...")
                                break
                    else:
                        print(f"   ✅ {page_name} - Sem erro RelatedObjectDoesNotExist")
                        
                        # Verificar se o header está presente
                        soup = BeautifulSoup(response.content, 'html.parser')
                        navbar_header = soup.find(class_='navbar-header')
                        if navbar_header:
                            print(f"   ✅ Header encontrado em {page_name}")
                        else:
                            print(f"   ⚠️  Header não encontrado em {page_name}")
                else:
                    print(f"   ❌ Erro HTTP {response.status_code} em {page_name}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar {page_name}: {e}")
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")

def check_user_profiles():
    """Verifica se todos os usuários têm perfil"""
    print("\n🔍 VERIFICANDO PERFIS DE USUÁRIOS")
    print("=" * 50)
    
    users_without_profile = []
    
    for user in User.objects.all():
        try:
            # Tentar acessar o perfil
            profile = user.perfil_usuario
            print(f"✅ {user.username} - Perfil: {profile.nome}")
        except:
            users_without_profile.append(user.username)
            print(f"❌ {user.username} - SEM PERFIL")
    
    if users_without_profile:
        print(f"\n⚠️  {len(users_without_profile)} usuários sem perfil encontrados:")
        for username in users_without_profile:
            print(f"   - {username}")
    else:
        print("\n✅ Todos os usuários possuem perfil")

if __name__ == "__main__":
    check_user_profiles()
    test_header_with_authentication()