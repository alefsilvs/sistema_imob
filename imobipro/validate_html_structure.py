import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

def validate_html_file(file_path):
    """Valida um arquivo HTML específico"""
    errors = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar tags não fechadas usando regex
        # Tags que devem ser fechadas
        tags_to_check = ['div', 'header', 'nav', 'section', 'article', 'aside', 'main', 'footer']
        
        for tag in tags_to_check:
            # Contar tags de abertura (excluindo self-closing)
            open_pattern = rf'<{tag}[^>]*(?<!/)>'
            close_pattern = rf'</{tag}>'
            
            opens = len(re.findall(open_pattern, content, re.IGNORECASE))
            closes = len(re.findall(close_pattern, content, re.IGNORECASE))
            
            if opens != closes:
                errors.append(f"Tag <{tag}>: {opens} abertas, {closes} fechadas (diferença: {opens - closes})")
        
        # Verificar com BeautifulSoup se possível
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Verificar se há elementos órfãos
            orphan_divs = soup.find_all('div', recursive=False)
            if len(orphan_divs) > 15:
                warnings.append(f"Muitas divs no nível raiz: {len(orphan_divs)} (pode indicar estrutura problemática)")
            
            # Verificar se há JavaScript com possíveis erros
            scripts = soup.find_all('script')
            for i, script in enumerate(scripts):
                if script.string:
                    script_content = script.string.lower()
                    if 'error' in script_content or 'undefined' in script_content:
                        warnings.append(f"Script {i+1} pode conter erros")
            
        except Exception as e:
            warnings.append(f"Erro ao analisar com BeautifulSoup: {e}")
        
        # Verificar padrões problemáticos específicos
        problematic_patterns = [
            (r'<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>\s*<div[^>]*>', "Muitas divs aninhadas consecutivas"),
            (r'<header[^>]*>.*?(?!.*</header>)', "Header possivelmente não fechado"),
            (r'</div>\s*</div>\s*</div>\s*</div>\s*</div>', "Muitas divs fechadas consecutivamente"),
        ]
        
        for pattern, description in problematic_patterns:
            if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                warnings.append(description)
        
    except Exception as e:
        errors.append(f"Erro ao ler arquivo: {e}")
    
    return errors, warnings

def scan_templates_directory(templates_dir):
    """Escaneia todos os templates em busca de problemas"""
    all_errors = defaultdict(list)
    all_warnings = defaultdict(list)
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, templates_dir)
                
                errors, warnings = validate_html_file(file_path)
                
                if errors:
                    all_errors[relative_path] = errors
                if warnings:
                    all_warnings[relative_path] = warnings
    
    return all_errors, all_warnings

def main():
    templates_dir = "templates"
    
    print("🔍 VALIDANDO ESTRUTURA HTML DOS TEMPLATES")
    print("=" * 60)
    
    if not os.path.exists(templates_dir):
        print(f"❌ Diretório {templates_dir} não encontrado!")
        return
    
    errors, warnings = scan_templates_directory(templates_dir)
    
    # Mostrar erros
    if errors:
        print("\n🚨 ERROS ENCONTRADOS:")
        print("-" * 40)
        for file_path, file_errors in errors.items():
            print(f"\n📄 {file_path}:")
            for error in file_errors:
                print(f"  ❌ {error}")
    else:
        print("\n✅ Nenhum erro crítico encontrado!")
    
    # Mostrar avisos
    if warnings:
        print("\n⚠️  AVISOS:")
        print("-" * 40)
        for file_path, file_warnings in warnings.items():
            print(f"\n📄 {file_path}:")
            for warning in file_warnings:
                print(f"  ⚠️  {warning}")
    else:
        print("\n✅ Nenhum aviso encontrado!")
    
    # Resumo
    print(f"\n📊 RESUMO:")
    print(f"  • Arquivos com erros: {len(errors)}")
    print(f"  • Arquivos com avisos: {len(warnings)}")
    print(f"  • Total de erros: {sum(len(e) for e in errors.values())}")
    print(f"  • Total de avisos: {sum(len(w) for w in warnings.values())}")
    
    # Focar nos templates mais problemáticos
    if errors:
        print(f"\n🎯 TEMPLATES MAIS PROBLEMÁTICOS:")
        sorted_errors = sorted(errors.items(), key=lambda x: len(x[1]), reverse=True)
        for file_path, file_errors in sorted_errors[:5]:
            print(f"  • {file_path}: {len(file_errors)} erros")

if __name__ == "__main__":
    main()