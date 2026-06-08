#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from contratos.models import Contrato
from financeiro.models import Parcela
from django.utils import timezone
from datetime import timedelta

print('=== VERIFICANDO CONTRATO TESTE001 ===')

# Buscar contrato TESTE001
contrato = Contrato.objects.filter(numero='TESTE001').first()
if not contrato:
    print('❌ Contrato TESTE001 não encontrado')
    exit()

print(f'Contrato: {contrato.numero}')
print(f'Inquilino: {contrato.inquilino.nome}')
print(f'Status: {contrato.status}')
print(f'Valor aluguel: R$ {contrato.valor_aluguel}')
print(f'Data início: {contrato.data_inicio}')
print(f'Data fim: {contrato.data_fim}')

# Verificar parcelas
parcelas = contrato.parcelas.all()
print(f'\nTotal de parcelas: {parcelas.count()}')

for parcela in parcelas:
    print(f'  - Parcela {parcela.numero_parcela}: R$ {parcela.valor_total} - {parcela.status} - Vence: {parcela.data_vencimento}')

# Verificar parcelas pendentes
parcelas_pendentes = contrato.parcelas.filter(status='PENDENTE')
print(f'\nParcelas pendentes: {parcelas_pendentes.count()}')

if parcelas_pendentes.count() == 0:
    print('\n⚠️ PROBLEMA IDENTIFICADO: Não há parcelas pendentes!')
    print('Sem parcelas pendentes, o sistema não gera dados PIX.')
    
    # Criar uma parcela pendente para teste
    print('\n🔧 Criando parcela pendente para teste...')
    
    parcela_teste = Parcela.objects.create(
        contrato=contrato,
        numero_parcela=1,
        data_vencimento=timezone.now().date() + timedelta(days=5),
        valor_aluguel=contrato.valor_aluguel,
        status='PENDENTE',
        tipo='ALUGUEL'
    )
    
    print(f'✅ Parcela criada: ID {parcela_teste.id}')
    print(f'   - Valor: R$ {parcela_teste.valor_total}')
    print(f'   - Vencimento: {parcela_teste.data_vencimento}')
    print(f'   - Status: {parcela_teste.status}')
    
    print('\n🚀 Agora o contrato TESTE001 tem uma parcela pendente!')
    print('Execute novamente o comando de verificação de vencimentos.')
else:
    print('\n✅ Contrato tem parcelas pendentes. O problema pode estar em outro lugar.')
    for parcela in parcelas_pendentes:
        print(f'   - Parcela {parcela.id}: R$ {parcela.valor_total} - Vence: {parcela.data_vencimento}')