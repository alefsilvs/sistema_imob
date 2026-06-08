import requests
import re
from bs4 import BeautifulSoup

def test_direct_dashboard_access():
    """Testa acesso direto ao dashboard após login"""
    
    session = requests.Session()
    
    try:
        # 1. Obter página de login
        print("1. Obtendo página de login...")
        login_url = "http://127.0.0.1:8000/accounts/login/"
        response = session.get(login_url)
        
        if response.status_code != 200:
            print(f"Erro ao acessar página de login: {response.status_code}")
            return
        
        # Extrair CSRF token
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        print(f"CSRF token obtido: {csrf_token[:20]}...")
        
        # 2. Fazer login
        print("2. Fazendo login...")
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=False)
        print(f"Status do login: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"Redirecionamento para: {redirect_url}")
            
            # 3. Seguir redirecionamento
            if redirect_url:
                print("3. Seguindo redirecionamento...")
                # Corrigir URL relativa
                if redirect_url.startswith('/'):
                    redirect_url = f"http://127.0.0.1:8000{redirect_url}"
                
                response = session.get(redirect_url)
                print(f"Status após redirecionamento: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Dashboard acessado com sucesso!")
                    
                    # Analisar HTML do dashboard
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Verificar elementos do header
                    print("\n=== ANÁLISE DO HEADER ===")
                    
                    # Procurar por navbar
                    navbar = soup.find('nav', class_='navbar')
                    if navbar:
                        print("✅ Navbar encontrada")
                        print(f"Classes da navbar: {navbar.get('class', [])}")
                    else:
                        print("❌ Navbar não encontrada")
                    
                    # Procurar por header
                    header = soup.find('header')
                    if header:
                        print("✅ Header encontrado")
                        print(f"Classes do header: {header.get('class', [])}")
                    else:
                        print("❌ Header não encontrado")
                    
                    # Procurar por sidebar
                    sidebar = soup.find('div', class_='sidebar')
                    if sidebar:
                        print("✅ Sidebar encontrada")
                        print(f"Classes da sidebar: {sidebar.get('class', [])}")
                    else:
                        print("❌ Sidebar não encontrada")
                    
                    # Verificar CSS
                    print("\n=== ANÁLISE DE CSS ===")
                    css_links = soup.find_all('link', rel='stylesheet')
                    for link in css_links:
                        href = link.get('href', '')
                        if 'custom.css' in href or 'dashboard.css' in href:
                            print(f"✅ CSS encontrado: {href}")
                    
                    # Salvar HTML para análise
                    with open('dashboard_success.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print("\n📄 HTML salvo em: dashboard_success.html")
                    
                else:
                    print(f"❌ Erro ao acessar dashboard: {response.status_code}")
                    print(f"Conteúdo: {response.text[:500]}...")
        else:
            print(f"❌ Login falhou: {response.status_code}")
            print(f"Conteúdo: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")

if __name__ == "__main__":
    test_direct_dashboard_access()