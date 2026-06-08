import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime

def check_page_errors(url, page_name):
    """Verifica erros específicos em uma página"""
    print(f"\n{'='*50}")
    print(f"ANALISANDO: {page_name}")
    print(f"URL: {url}")
    print(f"Horário: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    try:
        session = requests.Session()
        response = session.get(url, timeout=10)
        
        print(f"Status HTTP: {response.status_code}")
        print(f"Tamanho do conteúdo: {len(response.text)} caracteres")
        
        # Analisar HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar elementos header
        headers = soup.find_all('header')
        print(f"Elementos <header>: {len(headers)}")
        
        # Verificar divs
        divs = soup.find_all('div')
        print(f"Elementos <div>: {len(divs)}")
        
        # Verificar fechamento de tags
        div_opens = len(re.findall(r'<div[^>]*>', response.text))
        div_closes = len(re.findall(r'</div>', response.text))
        header_opens = len(re.findall(r'<header[^>]*>', response.text))
        header_closes = len(re.findall(r'</header>', response.text))
        
        print(f"Tags <div> abertas: {div_opens}")
        print(f"Tags </div> fechadas: {div_closes}")
        print(f"Diferença divs: {div_opens - div_closes}")
        
        print(f"Tags <header> abertas: {header_opens}")
        print(f"Tags </header> fechadas: {header_closes}")
        print(f"Diferença headers: {header_opens - header_closes}")
        
        # Verificar erros específicos no HTML
        errors_found = []
        
        if 'error' in response.text.lower():
            errors_found.append("Palavra 'error' encontrada no HTML")
        
        if 'exception' in response.text.lower():
            errors_found.append("Palavra 'exception' encontrada no HTML")
            
        if 'traceback' in response.text.lower():
            errors_found.append("Palavra 'traceback' encontrada no HTML")
            
        # Verificar se há tags não fechadas
        if div_opens != div_closes:
            errors_found.append(f"Tags <div> não balanceadas: {div_opens} abertas, {div_closes} fechadas")
            
        if header_opens != header_closes:
            errors_found.append(f"Tags <header> não balanceadas: {header_opens} abertas, {header_closes} fechadas")
        
        # Verificar se há elementos órfãos
        orphan_divs = soup.find_all('div', recursive=False)
        if len(orphan_divs) > 10:  # Muitas divs no nível raiz pode indicar problema
            errors_found.append(f"Muitas divs no nível raiz: {len(orphan_divs)}")
        
        # Verificar se há JavaScript com erros
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('error' in script.string.lower() or 'undefined' in script.string.lower()):
                errors_found.append("Possível erro em JavaScript encontrado")
                break
        
        # Verificar se há CSS com problemas
        styles = soup.find_all('style')
        for style in styles:
            if style.string and ('{' in style.string and '}' not in style.string):
                errors_found.append("Possível CSS malformado encontrado")
                break
        
        if errors_found:
            print("\n🚨 ERROS ENCONTRADOS:")
            for error in errors_found:
                print(f"  ❌ {error}")
        else:
            print("\n✅ Nenhum erro óbvio encontrado")
        
        # Mostrar início e fim do HTML para debug
        print(f"\n--- INÍCIO DO HTML (300 chars) ---")
        print(response.text[:300])
        
        print(f"\n--- FIM DO HTML (300 chars) ---")
        print(response.text[-300:])
        
        return errors_found
        
    except Exception as e:
        print(f"❌ ERRO ao analisar {page_name}: {e}")
        return [f"Erro de conexão: {e}"]

def main():
    """Função principal para testar múltiplas páginas"""
    
    # URLs para testar
    urls_to_test = [
        ("http://127.0.0.1:8000/", "Página Inicial"),
        ("http://127.0.0.1:8000/accounts/login/", "Página de Login"),
        ("http://127.0.0.1:8000/imoveis/", "Lista de Imóveis"),
        ("http://127.0.0.1:8000/imoveis/layouts/", "Layouts (requer login)"),
        ("http://127.0.0.1:8000/admin/", "Admin Django"),
    ]
    
    all_errors = {}
    
    for url, name in urls_to_test:
        errors = check_page_errors(url, name)
        if errors:
            all_errors[name] = errors
        time.sleep(1)  # Pequena pausa entre requisições
    
    # Resumo final
    print(f"\n{'='*60}")
    print("RESUMO FINAL DE ERROS")
    print(f"{'='*60}")
    
    if all_errors:
        for page, errors in all_errors.items():
            print(f"\n🚨 {page}:")
            for error in errors:
                print(f"  ❌ {error}")
    else:
        print("\n✅ Nenhum erro encontrado em nenhuma página!")
    
    print(f"\nAnálise concluída em: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()