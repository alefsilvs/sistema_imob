#!/usr/bin/env python
"""
Script para executar o servidor Django sem o warning de desenvolvimento
"""
import os
import sys
import subprocess
import threading
import select

def filter_output(line):
    """Filtra linhas que contêm warnings específicos"""
    warnings_to_filter = [
        'WARNING: This is a development server',
        'Do not use it in a production setting',
        'For more information on production servers'
    ]
    return not any(warning in line for warning in warnings_to_filter)

def read_output(pipe, output_func):
    """Lê a saída do pipe e aplica filtro"""
    try:
        for line in iter(pipe.readline, ''):
            if filter_output(line):
                output_func(line)
                sys.stdout.flush()
                sys.stderr.flush()
    except:
        pass

def run_server_quiet():
    """Executa o servidor Django filtrando o warning"""
    
    # Comando para executar o servidor
    cmd = [sys.executable, 'manage.py', 'runserver']
    
    # Iniciar o processo
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Redirecionar stderr para stdout
        universal_newlines=True,
        bufsize=1
    )
    
    try:
        # Ler e filtrar a saída
        for line in iter(process.stdout.readline, ''):
            if filter_output(line):
                print(line, end='')
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        # Encerrar o processo quando Ctrl+C for pressionado
        process.terminate()
        process.wait()
        print("\nServidor encerrado.")

if __name__ == '__main__':
    run_server_quiet()