import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from imoveis.models import ContratoBancaFeira

contratos = ContratoBancaFeira.objects.all()
print(f'Total de contratos de banca: {contratos.count()}')

for contrato in contratos:
    print(f'\n=== CONTRATO {contrato.numero} ===')
    print(f'Inquilino: {contrato.inquilino.nome}')
    print(f'Banca: {contrato.banca_feira}')
    if contrato.banca_feira:
        print(f'Banca código: {contrato.banca_feira.codigo}')
        print(f'Banca localização: {contrato.banca_feira.localizacao_completa}')
        print(f'Banca tipo: {contrato.banca_feira.get_tipo_display()}')
    else:
        print('Banca: N/A')
    print(f'Valor total: {contrato.valor_total_mensal}')
    print(f'Data fim: {contrato.data_fim}')