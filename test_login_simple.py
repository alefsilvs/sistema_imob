#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client

def test_login_and_pages():
    """Testa login e acesso às páginas para verificar elementos header e div"""
    
    # Criar cliente de teste
    client = Client()
    
    print("=== TESTE DE LOGIN E ELEMENTOS ===")
    
    # Testar acesso direto ao login
    print('\n1. Testando acesso ao login...')
    login_page = client.get('/accounts/login/')
    print(f'   Login page status: {login_page.status_code}')
    
    # Fazer login com o usuário de teste
    login_data = {
        'username': 'teste_header',
        'password': '123456'
    }
    
    print('\n2. Tentando fazer login...')
    response = client.post('/accounts/login/', login_data)
    print(f'   Status do login: {response.status_code}')
    
    redirect_url = response.get('Location', 'Nenhum redirecionamento')
    print(f'   Redirect URL: {redirect_url}')
    
    if response.status_code in [200, 302]:
        print('   ✅ Login processado com sucesso')
        
        # Testar páginas específicas
        pages_to_test = [
            ('/', 'Home/Dashboard'),
            ('/imoveis/', 'Imóveis'),
            ('/suporte/', 'Suporte'),
        ]
        
        print('\n3. Testando páginas autenticadas...')
        for url, name in pages_to_test:
            try:
                resp = client.get(url)
                print(f'\n   📄 {name} ({url}):')
                print(f'      Status: {resp.status_code}')
                
                if resp.status_code == 200:
                    content = resp.content.decode('utf-8')
                    header_count = content.count('<header')
                    div_count = content.count('<div')
                    print(f'      Headers: {header_count}')
                    print(f'      Divs: {div_count}')
                    
                    # Verificar se há erros no HTML
                    if 'error' in content.lower() and 'alert' in content.lower():
                        print('      ⚠️  Possíveis erros encontrados no HTML')
                    else:
                        print('      ✅ HTML sem erros aparentes')
                        
                elif resp.status_code == 302:
                    redirect = resp.get('Location', 'Desconhecido')
                    print(f'      Redirecionamento para: {redirect}')
                    
            except Exception as e:
                print(f'      ❌ ERRO ao acessar {url}: {e}')
    else:
        print('   ❌ Falha no login')
    
    print('\n=== FIM DO TESTE ===')

if __name__ == '__main__':
    test_login_and_pages()