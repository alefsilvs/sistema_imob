#!/usr/bin/env python3
"""
Script para diagnosticar problemas com o header div
"""

import requests
from bs4 import BeautifulSoup
import re

def diagnose_header_issue():
    """Diagnostica problemas específicos com o header"""
    
    print("=== DIAGNÓSTICO DO PROBLEMA DO HEADER ===\n")
    
    # 1. Testar página inicial (não autenticada)
    print("1. TESTANDO PÁGINA INICIAL (não autenticada)")
    try:
        response = requests.get('http://127.0.0.1:8000/')
        print(f"   Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar se há navbar-header
        navbar_header = soup.find(class_='navbar-header')
        print(f"   navbar-header presente: {'✅ SIM' if navbar_header else '❌ NÃO'}")
        
        # Verificar se há sidebar
        sidebar = soup.find(class_='sidebar')
        print(f"   sidebar presente: {'✅ SIM' if sidebar else '❌ NÃO'}")
        
        # Verificar elementos de navegação
        nav_elements = soup.find_all('nav')
        print(f"   Elementos <nav>: {len(nav_elements)}")
        
        # Verificar se há CSS carregado
        css_links = soup.find_all('link', {'rel': 'stylesheet'})
        print(f"   Links CSS: {len(css_links)}")
        
        # Verificar se há JavaScript
        script_tags = soup.find_all('script')
        print(f"   Scripts: {len(script_tags)}")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Testar página autenticada
    print("2. TESTANDO PÁGINA AUTENTICADA")
    
    session = requests.Session()
    
    try:
        # Login
        login_page = session.get('http://127.0.0.1:8000/accounts/login/')
        soup = BeautifulSoup(login_page.content, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_response = session.post('http://127.0.0.1:8000/accounts/login/', data=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        # Acessar dashboard
        dashboard_response = session.get('http://127.0.0.1:8000/dashboard/')
        print(f"   Dashboard status: {dashboard_response.status_code}")
        
        soup = BeautifulSoup(dashboard_response.text, 'html.parser')
        
        # Verificar elementos do header
        navbar_header = soup.find(class_='navbar-header')
        print(f"   navbar-header presente: {'✅ SIM' if navbar_header else '❌ NÃO'}")
        
        if navbar_header:
            # Verificar se o navbar-header tem conteúdo
            navbar_content = navbar_header.get_text(strip=True)
            print(f"   Conteúdo do navbar-header: {'✅ TEM' if navbar_content else '❌ VAZIO'}")
            
            # Verificar estilos inline
            navbar_style = navbar_header.get('style', '')
            print(f"   Estilos inline: {navbar_style if navbar_style else 'Nenhum'}")
            
            # Verificar classes
            navbar_classes = navbar_header.get('class', [])
            print(f"   Classes: {', '.join(navbar_classes)}")
        
        # Verificar sidebar
        sidebar = soup.find(class_='sidebar')
        print(f"   sidebar presente: {'✅ SIM' if sidebar else '❌ NÃO'}")
        
        # Verificar dropdown do usuário
        dropdown = soup.find(class_='dropdown-toggle')
        print(f"   dropdown do usuário: {'✅ SIM' if dropdown else '❌ NÃO'}")
        
        # Verificar se há erros de CSS
        css_errors = []
        
        # Verificar se o CSS custom está sendo carregado
        custom_css_link = soup.find('link', href=re.compile(r'custom\.css'))
        print(f"   CSS custom carregado: {'✅ SIM' if custom_css_link else '❌ NÃO'}")
        
        # Verificar se há conflitos de z-index ou display
        style_tags = soup.find_all('style')
        for style in style_tags:
            content = style.get_text()
            if 'display: none' in content and 'navbar' in content:
                css_errors.append("Possível display:none no navbar")
            if 'z-index' in content and 'navbar' in content:
                css_errors.append("Possível conflito de z-index")
        
        if css_errors:
            print(f"   ⚠️  Possíveis problemas CSS: {', '.join(css_errors)}")
        else:
            print("   ✅ Nenhum problema CSS óbvio detectado")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 3. Verificar arquivos CSS
    print("3. VERIFICANDO ARQUIVOS CSS")
    
    try:
        css_response = requests.get('http://127.0.0.1:8000/static/css/custom.css')
        print(f"   Status do CSS custom: {css_response.status_code}")
        
        if css_response.status_code == 200:
            css_content = css_response.text
            
            # Verificar se há regras para navbar-header
            if '.navbar-header' in css_content:
                print("   ✅ Regras CSS para .navbar-header encontradas")
                
                # Extrair regras específicas
                navbar_rules = re.findall(r'\.navbar-header[^}]*{[^}]*}', css_content, re.DOTALL)
                for rule in navbar_rules:
                    print(f"   Regra: {rule.strip()}")
                    
                    # Verificar problemas comuns
                    if 'display: none' in rule:
                        print("   ❌ PROBLEMA: display: none encontrado!")
                    if 'visibility: hidden' in rule:
                        print("   ❌ PROBLEMA: visibility: hidden encontrado!")
                    if 'opacity: 0' in rule:
                        print("   ❌ PROBLEMA: opacity: 0 encontrado!")
            else:
                print("   ❌ Nenhuma regra CSS para .navbar-header encontrada")
        
    except Exception as e:
        print(f"   ❌ ERRO ao carregar CSS: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 4. Resumo e recomendações
    print("4. RESUMO E RECOMENDAÇÕES")
    print("   Se o header aparece no HTML mas não na tela:")
    print("   - Verificar CSS (display, visibility, opacity)")
    print("   - Verificar z-index e posicionamento")
    print("   - Verificar se há JavaScript ocultando elementos")
    print("   - Verificar responsividade (media queries)")
    print("   - Verificar se há sobreposição de elementos")
    
    print("\n✅ DIAGNÓSTICO CONCLUÍDO")

if __name__ == '__main__':
    diagnose_header_issue()