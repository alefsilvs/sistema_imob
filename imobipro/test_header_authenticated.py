import requests
from bs4 import BeautifulSoup
import re

# Configurações
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = f'{BASE_URL}/accounts/login/'
DASHBOARD_URL = f'{BASE_URL}/dashboard/'

# Credenciais
USERNAME = 'admin'
PASSWORD = 'admin123'

def test_authenticated_header():
    """Testa o header após login autenticado"""
    
    session = requests.Session()
    
    try:
        # 1. Obter página de login e CSRF token
        print("1. Obtendo página de login...")
        login_page = session.get(LOGIN_URL)
        if login_page.status_code != 200:
            print(f"Erro ao acessar página de login: {login_page.status_code}")
            return
        
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_token:
            print("CSRF token não encontrado!")
            return
        
        csrf_value = csrf_token.get('value')
        print(f"CSRF token obtido: {csrf_value[:20]}...")
        
        # 2. Fazer login
        print("2. Fazendo login...")
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'csrfmiddlewaretoken': csrf_value
        }
        
        login_response = session.post(LOGIN_URL, data=login_data)
        print(f"Status do login: {login_response.status_code}")
        print(f"URL após login: {login_response.url}")
        
        # 3. Acessar dashboard
        print("3. Acessando dashboard...")
        dashboard_response = session.get(DASHBOARD_URL)
        print(f"Status do dashboard: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            # Salvar HTML para análise
            with open('temp_dashboard_header_test.html', 'w', encoding='utf-8') as f:
                f.write(dashboard_response.text)
            
            # Analisar conteúdo
            soup = BeautifulSoup(dashboard_response.content, 'html.parser')
            
            # Verificar elementos do header
            print("\n=== ANÁLISE DO HEADER ===")
            
            # Procurar por navbar-header
            navbar_header = soup.find(class_='navbar-header')
            print(f"navbar-header encontrado: {navbar_header is not None}")
            if navbar_header:
                print(f"Conteúdo do navbar-header: {str(navbar_header)[:200]}...")
            
            # Procurar por sidebar
            sidebar = soup.find(class_='sidebar')
            print(f"sidebar encontrado: {sidebar is not None}")
            
            # Procurar por elementos nav
            nav_elements = soup.find_all('nav')
            print(f"Elementos <nav> encontrados: {len(nav_elements)}")
            
            # Procurar por dashboard-header
            dashboard_header = soup.find(class_='dashboard-header')
            print(f"dashboard-header encontrado: {dashboard_header is not None}")
            if dashboard_header:
                print(f"Conteúdo do dashboard-header: {str(dashboard_header)[:200]}...")
            
            # Verificar CSS carregado
            css_links = soup.find_all('link', {'rel': 'stylesheet'})
            print(f"\nCSS carregado: {len(css_links)} arquivos")
            for link in css_links:
                href = link.get('href', '')
                if 'custom.css' in href:
                    print(f"  - custom.css encontrado: {href}")
            
            # Verificar se há estilos inline que podem estar ocultando o header
            style_tags = soup.find_all('style')
            print(f"\nTags <style> encontradas: {len(style_tags)}")
            
            # Procurar por display: none ou visibility: hidden
            page_content = dashboard_response.text.lower()
            if 'display: none' in page_content or 'display:none' in page_content:
                print("AVISO: Encontrado 'display: none' na página")
            if 'visibility: hidden' in page_content or 'visibility:hidden' in page_content:
                print("AVISO: Encontrado 'visibility: hidden' na página")
            
            print(f"\nHTML salvo em: temp_dashboard_header_test.html")
            
        else:
            print(f"Erro ao acessar dashboard: {dashboard_response.status_code}")
            print(f"Conteúdo da resposta: {dashboard_response.text[:500]}...")
    
    except Exception as e:
        print(f"Erro durante o teste: {e}")

if __name__ == "__main__":
    test_authenticated_header()