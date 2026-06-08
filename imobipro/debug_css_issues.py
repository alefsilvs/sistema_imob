#!/usr/bin/env python3
"""
Script para detectar problemas específicos de CSS que afetam td, header e div
"""

import re
import os

def analyze_css_file(file_path):
    """Analisa o arquivo CSS para problemas específicos"""
    print(f"Analisando {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    lines = content.split('\n')
    
    # Verifica regras CSS específicas que podem causar problemas
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Verifica regras CSS para td, header, div que podem causar problemas
        if any(element in line_stripped for element in ['td', 'header', 'div']):
            
            # Verifica propriedades que podem causar problemas de layout
            if any(prop in line_stripped for prop in ['display:', 'position:', 'overflow:', 'visibility:']):
                issues.append(f"Linha {i}: Propriedade potencialmente problemática - {line_stripped}")
            
            # Verifica seletores muito específicos que podem causar conflitos
            if line_stripped.count('.') > 3 or line_stripped.count('#') > 1:
                issues.append(f"Linha {i}: Seletor muito específico - {line_stripped}")
            
            # Verifica !important que pode causar conflitos
            if '!important' in line_stripped:
                issues.append(f"Linha {i}: Uso de !important - {line_stripped}")
    
    # Verifica regras CSS específicas para elementos problemáticos
    td_rules = re.findall(r'\.?[^{]*td[^{]*{[^}]*}', content, re.DOTALL)
    header_rules = re.findall(r'\.?[^{]*header[^{]*{[^}]*}', content, re.DOTALL)
    div_rules = re.findall(r'\.?[^{]*div[^{]*{[^}]*}', content, re.DOTALL)
    
    print(f"\n📊 Estatísticas:")
    print(f"  - Regras para TD: {len(td_rules)}")
    print(f"  - Regras para HEADER: {len(header_rules)}")
    print(f"  - Regras para DIV: {len(div_rules)}")
    
    if issues:
        print(f"\n⚠️  Problemas potenciais encontrados ({len(issues)}):")
        for issue in issues[:10]:  # Mostra apenas os primeiros 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... e mais {len(issues) - 10} problemas")
    else:
        print("\n✅ Nenhum problema óbvio encontrado")
    
    return issues

def check_specific_css_conflicts():
    """Verifica conflitos específicos de CSS"""
    css_file = "static/css/custom.css"
    
    if not os.path.exists(css_file):
        print(f"❌ Arquivo {css_file} não encontrado")
        return
    
    print("🔍 Verificando conflitos específicos de CSS...")
    print("=" * 60)
    
    issues = analyze_css_file(css_file)
    
    # Verifica problemas específicos conhecidos
    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n🔍 Verificações específicas:")
    
    # Verifica se há regras conflitantes para td
    if 'table td' in content and '.table td' in content:
        print("  ⚠️  Possível conflito: regras para 'table td' e '.table td'")
    
    # Verifica se há regras conflitantes para header
    if 'header' in content and '.header' in content:
        print("  ⚠️  Possível conflito: regras para 'header' e '.header'")
    
    # Verifica se há regras conflitantes para div
    if re.search(r'\bdiv\s*{', content) and re.search(r'\..*div', content):
        print("  ⚠️  Possível conflito: regras genéricas e específicas para div")
    
    # Verifica media queries que podem afetar elementos
    media_queries = re.findall(r'@media[^{]*{[^}]*}', content, re.DOTALL)
    print(f"  📱 Media queries encontradas: {len(media_queries)}")
    
    print("\n" + "=" * 60)
    print("✅ Análise concluída!")

if __name__ == "__main__":
    check_specific_css_conflicts()