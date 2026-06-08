import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
import django
django.setup()

from contratos.models import Contrato
from pagamentos.models import ConfiguracaoPagamento
from django.utils import timezone

# Buscar um contrato para teste
contrato = Contrato.objects.first()
if not contrato:
    print("Nenhum contrato encontrado!")
    exit()

print(f"Testando PIX para contrato: {contrato.numero}")

# Buscar qualquer parcela para teste
parcela_pendente = contrato.parcelas.order_by('data_vencimento').first()

if not parcela_pendente:
    print("Nenhuma parcela encontrada! Criando uma para teste...")
    from financeiro.models import Parcela
    from decimal import Decimal
    
    parcela_pendente = Parcela.objects.create(
        contrato=contrato,
        numero_parcela=1,
        data_vencimento=timezone.now().date(),
        valor_aluguel=Decimal('1500.00'),
        status='PENDENTE'
    )
    print(f"Parcela criada: ID {parcela_pendente.id}")
else:
    print(f"Status da parcela: {parcela_pendente.status}")

print(f"Parcela encontrada: ID {parcela_pendente.id}, Valor: R$ {parcela_pendente.valor_total}")

# Obter configuração PIX
config_pix = ConfiguracaoPagamento.get_configuracao()
print(f"PIX Habilitado: {config_pix.pix_habilitado}")
print(f"PIX Chave: {config_pix.pix_chave}")
print(f"PIX Nome: {config_pix.pix_nome_recebedor}")

# Tentar gerar código PIX
try:
    from pagamentos.utils import (
        gerar_link_pagamento, 
        gerar_codigo_pix_real, 
        gerar_qr_code_pix
    )
    
    print("\n=== TESTANDO GERAÇÃO PIX ===")
    
    # Gerar link de pagamento
    link_pagamento = gerar_link_pagamento(parcela_pendente.id)
    print(f"Link de pagamento: {link_pagamento}")
    
    # Gerar código PIX
    dados_pix = {
        'chave': config_pix.pix_chave or 'exemplo@email.com',
        'valor': float(parcela_pendente.valor_total),
        'nome_recebedor': config_pix.pix_nome_recebedor or 'SISTEMA IMOBILIARIO',
        'cidade': 'SAO PAULO',
        'identificador': f'PARC{parcela_pendente.id}'
    }
    
    print(f"\nDados PIX: {dados_pix}")
    
    codigo_pix = gerar_codigo_pix_real(dados_pix)
    print(f"\nCódigo PIX gerado: {codigo_pix}")
    
    if codigo_pix:
        qr_code_pix = gerar_qr_code_pix(codigo_pix)
        print(f"QR Code gerado: {bool(qr_code_pix)}")
        if qr_code_pix:
            print(f"Tamanho do QR Code: {len(qr_code_pix)} caracteres")
    else:
        print("❌ Código PIX não foi gerado!")
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
except Exception as e:
    print(f"❌ Erro na geração PIX: {e}")
    import traceback
    traceback.print_exc()