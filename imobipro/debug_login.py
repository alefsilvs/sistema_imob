import requests
from bs4 import BeautifulSoup

# Fazer requisição para a página de login
try:
    response = requests.get('http://127.0.0.1:8000/accounts/login/')
    html_content = response.text
    
    print('=== ANÁLISE DA PÁGINA DE LOGIN ===')
    print(f'Status: {response.status_code}')
    print(f'Tamanho: {len(html_content)} caracteres')
    
    # Verificar estrutura HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Contar elementos
    headers = soup.find_all('header')
    divs = soup.find_all('div')
    
    print(f'\nElementos encontrados:')
    print(f'- Headers: {len(headers)}')
    print(f'- Divs: {len(divs)}')
    
    # Verificar problemas de fechamento
    div_count = html_content.count('<div')
    div_close_count = html_content.count('</div>')
    header_count = html_content.count('<header')
    header_close_count = html_content.count('</header>')
    
    print(f'\nVerificação de fechamento:')
    print(f'- Divs abertas: {div_count}, fechadas: {div_close_count}')
    if div_count == div_close_count:
        print('  Status divs: OK')
    else:
        print('  Status divs: ERRO - Divs não fechadas corretamente')
    
    print(f'- Headers abertas: {header_count}, fechadas: {header_close_count}')
    if header_count == header_close_count:
        print('  Status headers: OK')
    else:
        print('  Status headers: ERRO - Headers não fechadas corretamente')
    
    # Procurar por erros específicos
    if 'Error' in html_content or 'Exception' in html_content:
        print('\nERROS encontrados no HTML:')
        lines = html_content.split('\n')
        for i, line in enumerate(lines):
            if 'Error' in line or 'Exception' in line:
                print(f'  Linha {i+1}: {line.strip()[:100]}')
    else:
        print('\nNenhum erro óbvio encontrado')
    
    # Verificar se há problemas de template Django
    if 'TemplateSyntaxError' in html_content:
        print('\nERRO: Problema de sintaxe de template Django')
    elif 'TemplateDoesNotExist' in html_content:
        print('\nERRO: Template não encontrado')
    
    # Mostrar início e fim do HTML para análise
    print('\n=== INÍCIO DO HTML (primeiros 300 caracteres) ===')
    print(html_content[:300])
    print('\n=== FIM DO HTML (últimos 300 caracteres) ===')
    print(html_content[-300:])
    
except Exception as e:
    print(f'Erro ao analisar página de login: {e}')