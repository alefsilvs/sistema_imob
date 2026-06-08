#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client

def test_dashboard_elements():
    """Testa elementos header e div no dashboard"""
    
    client = Client()
    
    print("=== TESTE DE ELEMENTOS DO DASHBOARD ===")
    
    # Login
    login_data = {'username': 'teste_header', 'password': '123456'}
    login_resp = client.post('/accounts/login/', login_data)
    print(f'Login status: {login_resp.status_code}')
    
    # Testar dashboard diretamente
    resp = client.get('/dashboard/')
    print(f'Dashboard status: {resp.status_code}')
    
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        header_count = content.count('<header')
        div_count = content.count('<div')
        print(f'Headers encontrados: {header_count}')
        print(f'Divs encontrados: {div_count}')
        
        # Verificar elementos específicos
        if 'class="header"' in content:
            print('✓ Encontrado elemento com class="header"')
        if 'id="header"' in content:
            print('✓ Encontrado elemento com id="header"')
        
        # Verificar erros
        error_indicators = ['error', 'exception', 'traceback']
        errors_found = []
        for indicator in error_indicators:
            if indicator in content.lower():
                errors_found.append(indicator)
        
        if errors_found:
            print(f'⚠️  Possíveis erros encontrados: {", ".join(errors_found)}')
        else:
            print('✅ Sem erros aparentes no HTML')
        
        # Salvar amostra do HTML
        with open('dashboard_sample.html', 'w', encoding='utf-8') as f:
            f.write(content[:3000])  # Primeiros 3000 caracteres
        print('📄 Amostra do HTML salva em dashboard_sample.html')
        
        # Verificar se há elementos header específicos
        if '<header' in content:
            print('\n📋 Análise de elementos <header>:')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '<header' in line:
                    print(f'   Linha {i+1}: {line.strip()[:100]}...')
    
    elif resp.status_code == 302:
        redirect_url = resp.get('Location', 'Desconhecido')
        print(f'Dashboard redirecionou para: {redirect_url}')
        
        # Seguir o redirecionamento
        final_resp = client.get(redirect_url)
        print(f'Página final status: {final_resp.status_code}')
        
        if final_resp.status_code == 200:
            content = final_resp.content.decode('utf-8')
            header_count = content.count('<header')
            div_count = content.count('<div')
            print(f'Headers na página final: {header_count}')
            print(f'Divs na página final: {div_count}')
    
    print('\n=== FIM DO TESTE ===')

if __name__ == '__main__':
    test_dashboard_elements()