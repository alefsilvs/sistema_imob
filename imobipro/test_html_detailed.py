#!/usr/bin/env python3
"""
Script detalhado para testar estrutura HTML e identificar erros específicos
"""

import requests
from bs4 import BeautifulSoup
import re

def test_html_detailed():
    print('=== TESTE DETALHADO DE HTML ===')
    
    base_url = 'http://127.0.0.1:8000'
    
    # Testar especificamente o mapa das bancas
    url = f'{base_url}/imoveis/bancas/mapa/'
    
    try:
        print(f'🔍 Testando: {url}')
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Parse com BeautifulSoup para análise mais precisa
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print(f'✓ Status: {response.status_code}')
            print(f'✓ Content-Type: {response.headers.get("content-type", "N/A")}')
            
            # Verificar estrutura básica
            doctype = bool(re.search(r'<!DOCTYPE\s+html>', html_content, re.IGNORECASE))
            html_tag = soup.find('html')
            head_tag = soup.find('head')
            body_tag = soup.find('body')
            
            print(f'\n📋 ESTRUTURA BÁSICA:')
            print(f'   DOCTYPE: {"✓" if doctype else "❌"}')
            print(f'   HTML tag: {"✓" if html_tag else "❌"}')
            print(f'   HEAD tag: {"✓" if head_tag else "❌"}')
            print(f'   BODY tag: {"✓" if body_tag else "❌"}')
            
            # Verificar tags semânticas
            headers = soup.find_all('header')
            mains = soup.find_all('main')
            footers = soup.find_all('footer')
            
            print(f'\n🏷️ TAGS SEMÂNTICAS:')
            print(f'   HEADER tags: {len(headers)}')
            for i, header in enumerate(headers):
                classes = header.get('class', [])
                print(f'     #{i+1}: classes={classes}')
            
            print(f'   MAIN tags: {len(mains)}')
            for i, main in enumerate(mains):
                classes = main.get('class', [])
                print(f'     #{i+1}: classes={classes}')
            
            print(f'   FOOTER tags: {len(footers)}')
            for i, footer in enumerate(footers):
                classes = footer.get('class', [])
                print(f'     #{i+1}: classes={classes}')
            
            # Verificar erros comuns
            print(f'\n🔍 VERIFICAÇÃO DE ERROS:')
            
            # Tags não fechadas
            unclosed_tags = []
            for tag_name in ['header', 'main', 'footer', 'div', 'section', 'nav']:
                open_count = len(re.findall(f'<{tag_name}[^>]*>', html_content, re.IGNORECASE))
                close_count = len(re.findall(f'</{tag_name}>', html_content, re.IGNORECASE))
                if open_count != close_count:
                    unclosed_tags.append(f'{tag_name} ({open_count} abertas vs {close_count} fechadas)')
            
            if unclosed_tags:
                print(f'   ❌ Tags desbalanceadas: {", ".join(unclosed_tags)}')
            else:
                print(f'   ✅ Todas as tags estão balanceadas')
            
            # Verificar IDs duplicados
            all_ids = [elem.get('id') for elem in soup.find_all(id=True)]
            duplicate_ids = [id_val for id_val in set(all_ids) if all_ids.count(id_val) > 1]
            
            if duplicate_ids:
                print(f'   ❌ IDs duplicados: {duplicate_ids}')
            else:
                print(f'   ✅ Nenhum ID duplicado encontrado')
            
            # Verificar atributos malformados
            malformed_attrs = re.findall(r'<[^>]*\s+[a-zA-Z-]+\s*=\s*[^"\'\s>][^>\s]*[^"\'>]', html_content)
            if malformed_attrs:
                print(f'   ⚠️ Possíveis atributos malformados encontrados: {len(malformed_attrs)}')
            else:
                print(f'   ✅ Atributos bem formados')
            
            # Verificar JavaScript errors no HTML
            script_errors = re.findall(r'<script[^>]*>.*?error.*?</script>', html_content, re.DOTALL | re.IGNORECASE)
            if script_errors:
                print(f'   ⚠️ Possíveis erros em scripts: {len(script_errors)}')
            
            # Verificar CSS errors
            style_errors = re.findall(r'<style[^>]*>.*?error.*?</style>', html_content, re.DOTALL | re.IGNORECASE)
            if style_errors:
                print(f'   ⚠️ Possíveis erros em estilos: {len(style_errors)}')
            
            print(f'\n📊 ESTATÍSTICAS:')
            print(f'   Tamanho do HTML: {len(html_content)} caracteres')
            print(f'   Total de elementos: {len(soup.find_all())}')
            print(f'   Scripts externos: {len(soup.find_all("script", src=True))}')
            print(f'   Estilos externos: {len(soup.find_all("link", rel="stylesheet"))}')
            
        else:
            print(f'❌ Erro HTTP: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Erro: {e}')
    
    print('\n=== FIM DO TESTE DETALHADO ===')

if __name__ == "__main__":
    test_html_detailed()