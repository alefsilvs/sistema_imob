#!/usr/bin/env python3
"""
Script para testar páginas específicas e detectar erros
"""

import requests
import time
from urllib.parse import urljoin

def test_page(url, page_name):
    """Testa uma página específica"""
    try:
        print(f"Testando {page_name}: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Verifica erros comuns no HTML
            errors = []
            
            # Verifica se há elementos td, header, div mal formados
            if '<td' in content and '</td>' not in content:
                errors.append("Tags <td> podem estar mal formadas")
            
            if '<header' in content and '</header>' not in content:
                errors.append("Tags <header> podem estar mal formadas")
            
            # Verifica se há erros de JavaScript inline
            if 'Uncaught' in content or 'TypeError' in content or 'ReferenceError' in content:
                errors.append("Possíveis erros de JavaScript detectados")
            
            # Verifica se há problemas de CSS
            if 'style=' in content:
                # Verifica estilos inline mal formados
                import re
                inline_styles = re.findall(r'style="([^"]*)"', content)
                for style in inline_styles:
                    if not style.strip().endswith(';') and style.strip():
                        errors.append(f"Estilo inline mal formado: {style}")
            
            if errors:
                print(f"  ❌ Problemas encontrados em {page_name}:")
                for error in errors:
                    print(f"    - {error}")
            else:
                print(f"  ✅ {page_name} carregou sem problemas detectados")
                
        else:
            print(f"  ❌ Erro HTTP {response.status_code} em {page_name}")
            
    except Exception as e:
        print(f"  ❌ Erro ao testar {page_name}: {e}")

def main():
    base_url = "http://127.0.0.1:8000"
    
    pages_to_test = [
        ("/financeiro/sangrias/", "Página de Sangrias"),
        ("/notificacoes/templates/", "Página de Templates de Notificações"),
        ("/", "Página Inicial")
    ]
    
    print("🔍 Testando páginas para detectar problemas...")
    print("=" * 50)
    
    for path, name in pages_to_test:
        url = urljoin(base_url, path)
        test_page(url, name)
        time.sleep(1)  # Pausa entre requests
    
    print("=" * 50)
    print("✅ Teste concluído!")

if __name__ == "__main__":
    main()