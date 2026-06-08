#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.conf import settings

print("=== CONFIGURAÇÕES DA EMPRESA ===")
print(f"Nome: {getattr(settings, 'EMPRESA_NOME', 'NÃO CONFIGURADO')}")
print(f"Telefone: {getattr(settings, 'EMPRESA_TELEFONE', 'NÃO CONFIGURADO')}")
print(f"Email: {getattr(settings, 'EMPRESA_EMAIL', 'NÃO CONFIGURADO')}")

# Testar contexto do comando
from notificacoes.management.commands.verificar_vencimentos_bancas import Command
from imoveis.models import ContratoBancaFeira

# Buscar um contrato para testar
contrato = ContratoBancaFeira.objects.first()
if contrato:
    print(f"\n=== TESTANDO CONTEXTO COM CONTRATO {contrato.numero} ===")
    command = Command()
    contexto = command.criar_contexto_banca(contrato)
    
    print(f"Empresa nome: {contexto.get('empresa_nome', 'VAZIO')}")
    print(f"Empresa telefone: {contexto.get('empresa_telefone', 'VAZIO')}")
    print(f"Empresa email: {contexto.get('empresa_email', 'VAZIO')}")
else:
    print("\nNenhum contrato encontrado para testar")