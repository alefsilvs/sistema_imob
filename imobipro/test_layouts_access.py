#!/usr/bin/env python3
"""
Script para testar o acesso à página de layouts com autenticação
"""

import requests
from bs4 import BeautifulSoup
import sys

def test_layouts_access():
    """Testa o acesso à página de layouts com login"""
    
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    try:
        print("1. Obtendo página de login...")
        login_url = f"{base_url}/accounts/login/"
        login_response = session.get(login_url)
        
        if login_response.status_code != 200:
            print(f"❌ Erro ao acessar página de login: {login_response.status_code}")
            return False
            
        # Extrair token CSRF
        soup = BeautifulSoup(login_response.content, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_input:
            print("❌ Token CSRF não encontrado")
            return False
            
        csrf_token = csrf_input.get('value')
        print(f"CSRF token obtido: {csrf_token[:20]}...")
        
        print("2. Fazendo login...")
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_post_response = session.post(login_url, data=login_data)
        print(f"Status do login: {login_post_response.status_code}")
        
        # Verificar se houve redirecionamento (sucesso no login)
        if login_post_response.status_code == 302:
            redirect_url = login_post_response.headers.get('Location', '/')
            print(f"Redirecionamento para: {redirect_url}")
            
            # Seguir redirecionamento
            dashboard_response = session.get(f"{base_url}{redirect_url}")
            print(f"Status do dashboard: {dashboard_response.status_code}")
            
        elif login_post_response.status_code == 200:
            print("Login retornou 200, tentando acessar layouts diretamente...")
        else:
            print(f"❌ Erro no login: {login_post_response.status_code}")
            return False
            
        print("3. Testando acesso à página de layouts...")
        layouts_url = f"{base_url}/imoveis/layouts/"
        layouts_response = session.get(layouts_url)
        
        print(f"Status da página de layouts: {layouts_response.status_code}")
        
        if layouts_response.status_code == 200:
            print("✅ Página de layouts acessada com sucesso!")
            
            # Verificar conteúdo da página
            soup = BeautifulSoup(layouts_response.content, 'html.parser')
            
            # Procurar por elementos específicos
            title = soup.find('title')
            if title:
                print(f"Título da página: {title.get_text()}")
                
            # Procurar por erros no HTML
            error_divs = soup.find_all('div', class_=['alert-danger', 'error', 'exception'])
            if error_divs:
                print("❌ Erros encontrados na página:")
                for error in error_divs:
                    print(f"  - {error.get_text().strip()}")
            else:
                print("✅ Nenhum erro visível encontrado na página")
                
            # Verificar se há conteúdo de layouts
            layout_cards = soup.find_all('div', class_='layout-card')
            if layout_cards:
                print(f"✅ {len(layout_cards)} layout(s) encontrado(s)")
            else:
                # Verificar se há mensagem de "nenhum layout"
                no_layout_msg = soup.find('h4', string=lambda text: text and 'Nenhum layout' in text)
                if no_layout_msg:
                    print("ℹ️ Nenhum layout configurado (comportamento normal)")
                else:
                    print("⚠️ Estrutura de layouts não encontrada")
                    
            # Salvar HTML para análise
            with open('layouts_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(layouts_response.text)
            print("📄 HTML salvo em: layouts_page_debug.html")
            
            return True
            
        elif layouts_response.status_code == 302:
            redirect_url = layouts_response.headers.get('Location', 'N/A')
            print(f"❌ Redirecionamento inesperado para: {redirect_url}")
            return False
            
        elif layouts_response.status_code == 500:
            print("❌ Erro interno do servidor (500)")
            
            # Tentar extrair informações do erro
            soup = BeautifulSoup(layouts_response.content, 'html.parser')
            error_info = soup.find('div', class_='exception_value')
            if error_info:
                print(f"Erro: {error_info.get_text().strip()}")
                
            # Salvar página de erro para análise
            with open('layouts_error_500.html', 'w', encoding='utf-8') as f:
                f.write(layouts_response.text)
            print("📄 Página de erro salva em: layouts_error_500.html")
            
            return False
            
        else:
            print(f"❌ Status inesperado: {layouts_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTE DE ACESSO À PÁGINA DE LAYOUTS ===")
    success = test_layouts_access()
    
    if success:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)