import requests
from bs4 import BeautifulSoup

# Testar diferentes URLs para verificar os elementos header e div
urls_to_test = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/dashboard/',
    'http://127.0.0.1:8000/login/',
]

for url in urls_to_test:
    try:
        print(f'\n=== Testando URL: {url} ===')
        response = requests.get(url, timeout=10)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Verificar título
            title = soup.find('title')
            if title:
                print(f'Título: {title.get_text()}')
            
            # Verificar elementos header no HTML bruto
            header_count_raw = html_content.count('<header')
            print(f'Elementos <header> no HTML bruto: {header_count_raw}')
            
            # Verificar elementos específicos
            headers = soup.find_all('header')
            asides = soup.find_all('aside')
            navs = soup.find_all('nav')
            
            print(f'Headers: {len(headers)}')
            print(f'Asides: {len(asides)}')
            print(f'Navs: {len(navs)}')
            
            # Verificar divs importantes
            sidebar_divs = soup.find_all('div', class_=lambda x: x and any('sidebar' in cls for cls in x))
            main_divs = soup.find_all('div', class_=lambda x: x and any('main' in cls for cls in x))
            content_divs = soup.find_all('div', class_=lambda x: x and any('content' in cls for cls in x))
            
            print(f'Divs sidebar: {len(sidebar_divs)}')
            print(f'Divs main: {len(main_divs)}')
            print(f'Divs content: {len(content_divs)}')
            
            # Se encontrarmos elementos, mostrar detalhes
            if headers:
                for i, header in enumerate(headers):
                    classes = header.get('class', [])
                    header_id = header.get('id', '')
                    print(f'  Header {i+1}: classes={classes}, id={header_id}')
            
            if asides:
                for i, aside in enumerate(asides):
                    classes = aside.get('class', [])
                    aside_id = aside.get('id', '')
                    print(f'  Aside {i+1}: classes={classes}, id={aside_id}')
                    
        elif response.status_code == 302:
            print(f'Redirecionamento para: {response.headers.get("Location", "N/A")}')
        else:
            print(f'Erro HTTP: {response.status_code}')
            
    except Exception as e:
        print(f'Erro ao testar {url}: {e}')

print('\n=== Resumo ===')
print('Se todos os testes mostraram 0 elementos header/aside/nav,')
print('o problema pode ser:')
print('1. Usuário não autenticado (redirecionamento para login)')
print('2. Problema no template base.html')
print('3. Problema no CSS que oculta os elementos')
print('4. Erro no Django que impede renderização correta')