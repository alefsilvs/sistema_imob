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

def test_login_and_header():
    session = requests.Session()
    
    # 1. Obter a página de login para pegar o CSRF token
    print("1. Obtendo página de login...")
    login_page = session.get(LOGIN_URL)
    print(f"Status da página de login: {login_page.status_code}")
    
    # Extrair CSRF token
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if not csrf_token:
        print("❌ CSRF token não encontrado!")
        return
    
    csrf_value = csrf_token['value']
    print(f"✅ CSRF token obtido: {csrf_value[:20]}...")
    
    # 2. Fazer login
    print("2. Fazendo login...")
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_value
    }
    
    login_response = session.post(LOGIN_URL, data=login_data)
    print(f"Status do login: {login_response.status_code}")
    
    # 3. Acessar dashboard
    print("3. Acessando dashboard...")
    dashboard_response = session.get(DASHBOARD_URL)
    print(f"Status do dashboard: {dashboard_response.status_code}")
    
    # 4. Salvar HTML do dashboard
    with open('temp_dashboard_authenticated.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_response.text)
    
    # 5. Verificar elementos do header
    soup = BeautifulSoup(dashboard_response.text, 'html.parser')
    
    print("\n=== VERIFICAÇÃO DO HEADER ===")
    
    # Verificar navbar-header
    navbar_header = soup.find(class_='navbar-header')
    print(f"navbar-header encontrado: {'✅' if navbar_header else '❌'}")
    
    # Verificar sidebar
    sidebar = soup.find(class_='sidebar')
    print(f"sidebar encontrado: {'✅' if sidebar else '❌'}")
    
    # Verificar dropdown-toggle
    dropdown_toggle = soup.find(class_='dropdown-toggle')
    print(f"dropdown-toggle encontrado: {'✅' if dropdown_toggle else '❌'}")
    
    # Verificar se há elementos de navegação
    nav_elements = soup.find_all('nav')
    print(f"Elementos <nav> encontrados: {len(nav_elements)}")
    
    # Verificar se há divs com classes relacionadas ao header
    header_divs = soup.find_all('div', class_=re.compile(r'header|navbar|nav'))
    print(f"Divs relacionadas ao header: {len(header_divs)}")
    
    print(f"\n✅ HTML do dashboard salvo em 'temp_dashboard_authenticated.html'")

if __name__ == '__main__':
    test_login_and_header()