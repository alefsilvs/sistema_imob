#!/usr/bin/env python3
"""
Script para testar estrutura HTML e identificar erros nas tags header, main, footer
"""

import requests
import time
from urllib.parse import urljoin

def test_html_structure():
    print('=== TESTE DE ESTRUTURA HTML ===')
    
    base_url = 'http://127.0.0.1:8000'
    pages_to_test = [
        ('/', 'Dashboard'),
        ('/imoveis/bancas/mapa/', 'Mapa das Bancas'),
        ('/imoveis/', 'Lista de Imóveis'),
        ('/contratos/', 'Contratos'),
        ('/financeiro/', 'Financeiro'),
        ('/imoveis/bancas/mapa-customizavel/', 'Mapa Customizável')
    ]
    
    for path, name in pages_to_test:
        try:
            url = urljoin(base_url, path)
            print(f'\n🔍 Testando {name}: {url}')
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Verificar estrutura HTML básica
                has_doctype = '<!doctype html>' in content
                has_html = '<html' in content
                has_head = '<head>' in content
                has_body = '<body>' in content
                
                print(f'   ✓ Status: {response.status_code}')
                print(f'   ✓ DOCTYPE: {"✓" if has_doctype else "❌"}')
                print(f'   ✓ HTML tag: {"✓" if has_html else "❌"}')
                print(f'   ✓ HEAD tag: {"✓" if has_head else "❌"}')
                print(f'   ✓ BODY tag: {"✓" if has_body else "❌"}')
                
                # Verificar tags específicas
                header_count = content.count('<header')
                main_count = content.count('<main')
                footer_count = content.count('<footer')
                
                header_close = content.count('</header>')
                main_close = content.count('</main>')
                footer_close = content.count('</footer>')
                
                print(f'   📊 HEADER: {header_count} abertas, {header_close} fechadas')
                print(f'   📊 MAIN: {main_count} abertas, {main_close} fechadas')
                print(f'   📊 FOOTER: {footer_count} abertas, {footer_close} fechadas')
                
                # Verificar problemas
                problems = []
                if header_count != header_close:
                    problems.append(f'HEADER desbalanceada ({header_count} vs {header_close})')
                if main_count != main_close:
                    problems.append(f'MAIN desbalanceada ({main_count} vs {main_close})')
                if footer_count != footer_close:
                    problems.append(f'FOOTER desbalanceada ({footer_count} vs {footer_close})')
                
                if problems:
                    print(f'   ❌ PROBLEMAS: {", ".join(problems)}')
                else:
                    print(f'   ✅ Estrutura HTML OK')
                    
            else:
                print(f'   ❌ Erro HTTP: {response.status_code}')
                
        except requests.exceptions.ConnectionError:
            print(f'   ❌ Servidor não está rodando')
            break
        except Exception as e:
            print(f'   ❌ Erro: {e}')
    
    print('\n=== FIM DO TESTE ===')

if __name__ == "__main__":
    test_html_structure()