import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from imoveis.models import ContratoBancaFeira
from notificacoes.management.commands.verificar_vencimentos_bancas import Command

# Pegar o contrato
contrato = ContratoBancaFeira.objects.first()
if contrato:
    # Criar instância do comando
    cmd = Command()
    
    # Gerar contexto
    contexto = cmd.criar_contexto_banca(contrato)
    
    print('=== CONTEXTO GERADO ===')
    print(f'Banca código: {contexto.get("banca_codigo", "VAZIO")}')
    print(f'Banca localização: {contexto.get("banca_localizacao", "VAZIO")}')
    print(f'Banca tipo: {contexto.get("banca_tipo", "VAZIO")}')
    print(f'Valor total: {contexto.get("valor_total", "VAZIO")}')
    print(f'Link pagamento: {contexto.get("link_pagamento", "VAZIO")}')
    print(f'PIX código: {contexto.get("pix", {}).get("codigo_pix", "VAZIO")}')
    print(f'Empresa telefone: {contexto.get("empresa_telefone", "VAZIO")}')
    print(f'Empresa email: {contexto.get("empresa_email", "VAZIO")}')
    
    print('\n=== DADOS DO CONTRATO ===')
    print(f'Valor total mensal: R$ {contrato.valor_total_mensal}')
    print(f'Banca feira: {contrato.banca_feira}')
    print(f'Banca código: {contrato.banca_feira.codigo}')
else:
    print('Nenhum contrato encontrado')