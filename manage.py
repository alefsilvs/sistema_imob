#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.

Django's command-line utility for administrative tasks.
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
    
    # Sistema de proteção
    try:
        from sistema_imobiliario.protection import log_module_access
        command = ' '.join(sys.argv) if len(sys.argv) > 1 else 'manage.py'
        log_module_access(f'manage.py - {command}')
    except Exception:
        pass
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
