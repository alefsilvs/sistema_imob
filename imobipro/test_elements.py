import requests
import re
from bs4 import BeautifulSoup

try:
    # Testar a página principal
    response = requests.get('http://127.0.0.1:8000/', timeout=10)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar elementos header
        headers = soup.find_all('header')
        print(f'Elementos header encontrados: {len(headers)}')
        
        for i, header in enumerate(headers):
            classes = header.get('class', [])
            header_id = header.get('id', '')
            print(f'Header {i+1}: classes={classes}, id={header_id}')
        
        # Verificar divs principais
        divs = soup.find_all('div', class_=re.compile(r'(sidebar|navbar|main|content)'))
        print(f'Divs principais encontrados: {len(divs)}')
        
        for div in divs[:5]:  # Mostrar apenas os primeiros 5
            classes = div.get('class', [])
            div_id = div.get('id', '')
            print(f'Div: classes={classes}, id={div_id}')
        
        # Verificar se há erros de CSS ou JS
        if 'error' in response.text.lower() or 'exception' in response.text.lower():
            print('AVISO: Possíveis erros encontrados no HTML')
        else:
            print('Nenhum erro óbvio encontrado no HTML')
            
        # Verificar se os arquivos CSS estão sendo carregados
        css_links = soup.find_all('link', rel='stylesheet')
        print(f'Arquivos CSS encontrados: {len(css_links)}')
        
        for css in css_links:
            href = css.get('href', '')
            if 'custom.css' in href:
                print(f'CSS customizado encontrado: {href}')
            
    else:
        print(f'Erro HTTP: {response.status_code}')
        
except Exception as e:
    print(f'Erro na requisição: {e}')