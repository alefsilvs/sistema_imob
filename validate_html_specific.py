#!/usr/bin/env python3
"""
Script para validar problemas específicos de HTML nos elementos td, header e div
"""

import os
import re
from pathlib import Path

class HTMLSpecificValidator:
    def __init__(self):
        self.errors = []
        
    def validate_file(self, file_path):
        """Valida um arquivo HTML específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove comentários HTML
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            
            # Remove tags de template Django
            content = re.sub(r'{%.*?%}', '', content, flags=re.DOTALL)
            content = re.sub(r'{{.*?}}', '', content, flags=re.DOTALL)
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                self._check_line(file_path, i, line)
                
        except Exception as e:
            self.errors.append(f"Erro ao ler {file_path}: {e}")
    
    def _check_line(self, file_path, line_num, line):
        """Verifica problemas específicos em uma linha"""
        
        # Verifica tags td mal formadas
        if '<td' in line:
            # Verifica se td tem fechamento na mesma linha ou se está bem formada
            if '<td' in line and not ('</td>' in line or line.strip().endswith('>')):
                if not line.strip().endswith('>'):
                    self.errors.append(f"{file_path}:{line_num} - Tag <td> mal formada: {line.strip()}")
        
        # Verifica tags header mal formadas
        if '<header' in line:
            if '<header' in line and not ('</header>' in line or line.strip().endswith('>')):
                if not line.strip().endswith('>'):
                    self.errors.append(f"{file_path}:{line_num} - Tag <header> mal formada: {line.strip()}")
        
        # Verifica tags div mal formadas
        if '<div' in line:
            # Verifica se div tem fechamento na mesma linha ou se está bem formada
            if '<div' in line and not ('</div>' in line or line.strip().endswith('>')):
                if not line.strip().endswith('>'):
                    self.errors.append(f"{file_path}:{line_num} - Tag <div> mal formada: {line.strip()}")
        
        # Verifica atributos mal formados
        if re.search(r'<(td|header|div)[^>]*[^"\s]=[^"\s][^>]*>', line):
            self.errors.append(f"{file_path}:{line_num} - Atributo sem aspas: {line.strip()}")
        
        # Verifica tags não fechadas
        open_tags = re.findall(r'<(td|header|div)(?:\s[^>]*)?>(?!</)', line)
        close_tags = re.findall(r'</(td|header|div)>', line)
        
        for tag in open_tags:
            if tag not in close_tags and not line.strip().endswith('/>'):
                # Verifica se é uma tag que deve ser fechada
                if not re.search(r'<' + tag + r'[^>]*/?>', line):
                    pass  # Tag pode ser fechada em outra linha
    
    def validate_templates(self):
        """Valida templates específicos"""
        templates_to_check = [
            'templates/base.html',
            'templates/financeiro/sangria/listar.html',
            'templates/notificacoes/templates/listar.html'
        ]
        
        for template in templates_to_check:
            if os.path.exists(template):
                print(f"Validando {template}...")
                self.validate_file(template)
            else:
                print(f"Arquivo não encontrado: {template}")
        
        if self.errors:
            print(f"\n❌ Encontrados {len(self.errors)} problemas:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Nenhum problema encontrado nos elementos td, header e div!")

if __name__ == "__main__":
    validator = HTMLSpecificValidator()
    validator.validate_templates()