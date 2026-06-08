#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from pagamentos.models import ConfiguracaoPagamento

def test_mercadopago():
    print("=== TESTE MERCADO PAGO ===")
    
    try:
        import mercadopago
        print("✅ SDK do Mercado Pago instalado")
    except ImportError:
        print("❌ SDK do Mercado Pago não instalado")
        print("Execute: pip install mercadopago")
        return False
    
    config = ConfiguracaoPagamento.get_configuracao()
    
    if not config.gateway_api_key:
        print("❌ Access Token não configurado")
        return False
    
    print(f"🔑 Access Token: {config.gateway_api_key[:20]}...")
    
    # Verificar se é sandbox ou produção
    is_sandbox = 'TEST-' in config.gateway_api_key
    ambiente = "SANDBOX (Testes)" if is_sandbox else "PRODUÇÃO"
    print(f"🔍 Ambiente: {ambiente}")
    
    try:
        sdk = mercadopago.SDK(config.gateway_api_key)
        
        # Testar API
        print("🔄 Testando conexão...")
        payment_methods = sdk.payment_methods().list_all()
        
        if payment_methods['status'] == 200:
            print("✅ Conexão com Mercado Pago OK!")
            
            methods = payment_methods['response']
            print(f"📊 {len(methods)} métodos de pagamento disponíveis")
            
            # Contar cartões de crédito
            credit_cards = [m for m in methods if m.get('payment_type_id') == 'credit_card']
            print(f"💳 {len(credit_cards)} cartões de crédito suportados")
            
            # Mostrar algumas bandeiras
            bandeiras = [m['id'] for m in credit_cards[:5]]
            print(f"🏷️  Bandeiras: {', '.join(bandeiras)}")
            
            # Verificar PIX
            pix_methods = [m for m in methods if m.get('id') == 'pix']
            if pix_methods:
                print("✅ PIX disponível")
            else:
                print("❌ PIX não disponível")
            
            return True
        else:
            print(f"❌ Erro na conexão: Status {payment_methods['status']}")
            if 'response' in payment_methods:
                print(f"Detalhes: {payment_methods['response']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar: {str(e)}")
        return False

if __name__ == "__main__":
    test_mercadopago()