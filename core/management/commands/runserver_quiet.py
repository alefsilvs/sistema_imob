"""
Comando customizado para executar o servidor Django sem warnings
"""
import sys
import warnings
import io
from contextlib import redirect_stderr
from django.core.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    """
    Comando runserver customizado que suprime warnings do servidor de desenvolvimento
    """
    
    def add_arguments(self, parser):
        super().add_arguments(parser)
        
    def inner_run(self, *args, **options):
        """
        Override do método inner_run para suprimir o warning específico
        """
        # Capturar stderr original
        original_stderr = sys.stderr
        
        # Criar um buffer para capturar a saída
        captured_output = io.StringIO()
        
        # Redirecionar stderr temporariamente
        sys.stderr = captured_output
        
        try:
            # Executar o método original
            super().inner_run(*args, **options)
        except Exception as e:
            # Em caso de erro, restaurar stderr e re-lançar
            sys.stderr = original_stderr
            raise e
        finally:
            # Obter o conteúdo capturado
            output = captured_output.getvalue()
            
            # Restaurar stderr original
            sys.stderr = original_stderr
            
            # Filtrar e exibir apenas as linhas que não são warnings
            lines = output.split('\n')
            for line in lines:
                if line and not any(warning_text in line for warning_text in [
                    'WARNING: This is a development server',
                    'Do not use it in a production setting',
                    'For more information on production servers'
                ]):
                    sys.stderr.write(line + '\n')
                    
    def handle(self, *args, **options):
        # Suprimir warnings específicos do servidor de desenvolvimento
        warnings.filterwarnings('ignore', message='.*development server.*')
        warnings.filterwarnings('ignore', message='.*Do not use it in a production setting.*')
        
        # Executar o comando runserver original
        super().handle(*args, **options)