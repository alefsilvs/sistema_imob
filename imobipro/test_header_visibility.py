#!/usr/bin/env python3
"""
Script para testar a visibilidade do header no dashboard
"""

import requests
from bs4 import BeautifulSoup
import re

def test_header_visibility():
    """Testa a visibilidade do header no dashboard"""
    
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    try:
        # 1. Obter página de login
        print("1. Obtendo página de login...")
        login_page = session.get(f"{base_url}/accounts/login/")
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if not csrf_input:
            print("❌ CSRF token não encontrado")
            return
        csrf_token = csrf_input['value']
        print(f"CSRF token obtido: {csrf_token[:20]}...")
        
        # 2. Fazer login
        print("2. Fazendo login...")
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_response = session.post(f"{base_url}/accounts/login/", data=login_data, allow_redirects=False)
        print(f"Status do login: {login_response.status_code}")
        
        if login_response.status_code in [200, 302]:
            if login_response.status_code == 302:
                redirect_url = login_response.headers.get('Location', '/')
                print(f"Redirecionamento para: {redirect_url}")
                
                # Seguir redirecionamento
                if redirect_url.startswith('/'):
                    redirect_url = f"{base_url}{redirect_url}"
                
                print("3. Seguindo redirecionamento...")
                dashboard_response = session.get(redirect_url)
            else:
                # Login retornou 200, tentar acessar dashboard diretamente
                print("3. Login retornou 200, tentando acessar dashboard...")
                dashboard_response = session.get(f"{base_url}/dashboard/")
                
            print(f"Status do dashboard: {dashboard_response.status_code}")
            
            if dashboard_response.status_code == 200:
                print("✅ Dashboard acessado com sucesso!")
                
                # Analisar HTML
                soup = BeautifulSoup(dashboard_response.content, 'html.parser')
                
                print("\n=== ANÁLISE DETALHADA DO HEADER ===")
                
                # Verificar navbar
                navbar = soup.find('nav', class_=re.compile(r'navbar'))
                if navbar:
                    print("✅ Navbar encontrada")
                    print(f"Classes da navbar: {navbar.get('class', [])}")
                    
                    # Verificar se navbar tem display: none
                    style = navbar.get('style', '')
                    if 'display:none' in style.replace(' ', '') or 'display: none' in style:
                        print("❌ Navbar tem display: none!")
                    else:
                        print("✅ Navbar não tem display: none")
                    
                    # Verificar conteúdo da navbar
                    navbar_content = navbar.get_text(strip=True)
                    if navbar_content:
                        print(f"✅ Navbar tem conteúdo: {navbar_content[:100]}...")
                    else:
                        print("❌ Navbar está vazia")
                        
                else:
                    print("❌ Navbar não encontrada")
                
                # Verificar header
                header = soup.find('header')
                if header:
                    print("✅ Header encontrado")
                    print(f"Classes do header: {header.get('class', [])}")
                    
                    # Verificar se header tem display: none
                    style = header.get('style', '')
                    if 'display:none' in style.replace(' ', '') or 'display: none' in style:
                        print("❌ Header tem display: none!")
                    else:
                        print("✅ Header não tem display: none")
                        
                    # Verificar conteúdo do header
                    header_content = header.get_text(strip=True)
                    if header_content:
                        print(f"✅ Header tem conteúdo: {header_content[:100]}...")
                    else:
                        print("❌ Header está vazio")
                        
                else:
                    print("❌ Header não encontrado")
                
                # Verificar sidebar
                sidebar = soup.find('aside', class_=re.compile(r'sidebar'))
                if sidebar:
                    print("✅ Sidebar encontrada")
                    print(f"Classes da sidebar: {sidebar.get('class', [])}")
                    
                    # Verificar se sidebar tem display: none
                    style = sidebar.get('style', '')
                    if 'display:none' in style.replace(' ', '') or 'display: none' in style:
                        print("❌ Sidebar tem display: none!")
                    else:
                        print("✅ Sidebar não tem display: none")
                        
                else:
                    print("❌ Sidebar não encontrada")
                
                print("\n=== ANÁLISE DE CSS ===")
                
                # Verificar links CSS
                css_links = soup.find_all('link', rel='stylesheet')
                for link in css_links:
                    href = link.get('href', '')
                    if 'custom.css' in href:
                        print(f"✅ CSS customizado encontrado: {href}")
                    elif 'bootstrap' in href:
                        print(f"✅ Bootstrap CSS encontrado: {href}")
                
                # Verificar estilos inline que podem ocultar elementos
                style_tags = soup.find_all('style')
                for style_tag in style_tags:
                    style_content = style_tag.get_text()
                    if 'display:none' in style_content.replace(' ', '') or 'display: none' in style_content:
                        print("⚠️ Encontrado display: none em estilos inline")
                        # Procurar por seletores específicos
                        if '.navbar' in style_content or '.header' in style_content or '.sidebar' in style_content:
                            print("❌ Possível ocultação de navbar/header/sidebar em CSS inline")
                
                # Salvar HTML para análise
                with open('header_analysis.html', 'w', encoding='utf-8') as f:
                    f.write(dashboard_response.text)
                print("\n📄 HTML salvo em: header_analysis.html")
                
            else:
                print(f"❌ Erro ao acessar dashboard: {dashboard_response.status_code}")
                print("Conteúdo:", dashboard_response.text[:500])
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    test_header_visibility()