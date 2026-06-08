#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from pagamentos.models import ConfiguracaoPagamento

def main():
    print("=== CONFIGURAÇÕES DE PAGAMENTO ===")
    
    config = ConfiguracaoPagamento.get_configuracao()
    
    print(f"\n📱 PIX:")
    print(f"   Habilitado: {'✅ Sim' if config.pix_habilitado else '❌ Não'}")
    print(f"   Chave: {config.pix_chave or 'Não configurado'}")
    print(f"   Nome: {config.pix_nome_recebedor or 'Não configurado'}")
    
    print(f"\n💳 CARTÃO:")
    print(f"   Habilitado: {'✅ Sim' if config.cartao_habilitado else '❌ Não'}")
    print(f"   API Key: {'✅ Configurado' if config.gateway_api_key else '❌ Não configurado'}")
    print(f"   Secret Key: {'✅ Configurado' if config.gateway_secret_key else '❌ Não configurado'}")
    print(f"   Endpoint: {config.gateway_endpoint or '❌ Não configurado'}")
    
    print(f"\n🧾 BOLETO:")
    print(f"   Habilitado: {'✅ Sim' if config.boleto_habilitado else '❌ Não'}")
    print(f"   Banco: {config.banco_codigo or 'Não configurado'}")
    print(f"   Agência: {config.agencia or 'Não configurado'}")
    print(f"   Conta: {config.conta or 'Não configurado'}")
    
    print(f"\n⚙️ CONFIGURAÇÕES GERAIS:")
    print(f"   Tempo Expiração: {config.tempo_expiracao_horas}h")
    print(f"   Valor Mínimo: R$ {config.valor_minimo}")
    print(f"   Taxa Processamento: {config.taxa_processamento}%")
    
    print(f"\n🔗 URLs DE RETORNO:")
    print(f"   Sucesso: {config.url_sucesso or 'Não configurado'}")
    print(f"   Erro: {config.url_erro or 'Não configurado'}")
    print(f"   Cancelamento: {config.url_cancelamento or 'Não configurado'}")

if __name__ == "__main__":
    main()