#!/usr/bin/env python
"""
Script para iniciar o servidor Django sem warnings
"""
import os
import sys
import subprocess
import warnings

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')

import django
from django.core.management import execute_from_command_line
from django.core.management.commands.runserver import Command as RunserverCommand

# Suprimir warnings
warnings.filterwarnings('ignore')

class QuietRunserver(RunserverCommand):
    """Versão silenciosa do runserver"""
    
    def log_message(self, format, *args):
        """Override para filtrar mensagens de log"""
        message = format % args
        if 'WARNING: This is a development server' not in message and \
           'Do not use it in a production setting' not in message and \
           'For more information on production servers' not in message:
            super().log_message(format, *args)
    
    def inner_run(self, *args, **options):
        """Override para suprimir warnings específicos"""
        import sys
        from io import StringIO
        
        # Capturar stderr
        old_stderr = sys.stderr
        sys.stderr = mystderr = StringIO()
        
        try:
            super().inner_run(*args, **options)
        finally:
            # Restaurar stderr e filtrar output
            sys.stderr = old_stderr
            output = mystderr.getvalue()
            
            # Filtrar linhas de warning
            lines = output.split('\n')
            for line in lines:
                if line and not any(warning in line for warning in [
                    'WARNING: This is a development server',
                    'Do not use it in a production setting',
                    'For more information on production servers'
                ]):
                    print(line, file=sys.stderr)

if __name__ == '__main__':
    django.setup()
    
    # Substituir o comando runserver padrão
    from django.core.management.commands import runserver
    runserver.Command = QuietRunserver
    
    # Executar o comando
    execute_from_command_line(['manage.py', 'runserver'] + sys.argv[1:])