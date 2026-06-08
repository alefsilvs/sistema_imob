import requests
from bs4 import BeautifulSoup

try:
    # Testar a página principal
    response = requests.get('http://127.0.0.1:8000/', timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "N/A")}')
    
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f'Tamanho do HTML: {len(html_content)} caracteres')
        
        # Verificar se é uma página de login ou redirecionamento
        title = soup.find('title')
        if title:
            print(f'Título da página: {title.get_text()}')
        
        # Verificar se há elementos header no HTML bruto
        header_count_raw = html_content.count('<header')
        print(f'Elementos <header> no HTML bruto: {header_count_raw}')
        
        # Verificar elementos header com BeautifulSoup
        headers = soup.find_all('header')
        print(f'Elementos header encontrados pelo BeautifulSoup: {len(headers)}')
        
        # Verificar se há divs com classes específicas
        sidebar_divs = soup.find_all('div', class_=lambda x: x and 'sidebar' in ' '.join(x))
        navbar_divs = soup.find_all('div', class_=lambda x: x and 'navbar' in ' '.join(x))
        main_divs = soup.find_all('div', class_=lambda x: x and 'main' in ' '.join(x))
        
        print(f'Divs com classe sidebar: {len(sidebar_divs)}')
        print(f'Divs com classe navbar: {len(navbar_divs)}')
        print(f'Divs com classe main: {len(main_divs)}')
        
        # Verificar se há elementos aside (sidebar)
        asides = soup.find_all('aside')
        print(f'Elementos aside encontrados: {len(asides)}')
        
        # Verificar se há elementos nav
        navs = soup.find_all('nav')
        print(f'Elementos nav encontrados: {len(navs)}')
        
        # Mostrar os primeiros 1000 caracteres do HTML
        print('\n--- Primeiros 1000 caracteres do HTML ---')
        print(html_content[:1000])
        
        # Verificar se há redirecionamento ou login
        if 'login' in html_content.lower() or 'entrar' in html_content.lower():
            print('\nAVISO: Página parece ser de login - usuário pode não estar autenticado')
        
        # Verificar se há JavaScript que pode estar afetando a renderização
        scripts = soup.find_all('script')
        print(f'\nScripts encontrados: {len(scripts)}')
        
    else:
        print(f'Erro HTTP: {response.status_code}')
        print(f'Resposta: {response.text[:500]}')
        
except Exception as e:
    print(f'Erro na requisição: {e}')
    import traceback
    traceback.print_exc()