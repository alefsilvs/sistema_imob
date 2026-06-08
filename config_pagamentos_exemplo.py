#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração de Exemplo para Pagamentos Reais

Copie este arquivo para config_pagamentos.py e ajuste as configurações
"""

# =============================================================================
# CONFIGURAÇÕES DO MERCADO PAGO
# =============================================================================

# Obtenha em: https://www.mercadopago.com.br/developers/panel/credentials
MERCADOPAGO_ACCESS_TOKEN_SANDBOX = "TEST-1234567890-123456-abcdef123456789-12345678"
MERCADOPAGO_ACCESS_TOKEN_PRODUCAO = "APP_USR-1234567890-123456-abcdef123456789-12345678"

# Use sandbox para testes, produção para uso real
MERCADOPAGO_USAR_SANDBOX = True

# Configurações PIX
PIX_CHAVE = "seu@email.com"  # ou CPF, CNPJ, telefone
PIX_NOME_RECEBEDOR = "Sua Empresa Ltda"

# URLs de retorno (ajuste para seu domínio)
BASE_URL = "http://localhost:8000"  # ou https://seusite.com
URL_SUCESSO = f"{BASE_URL}/pagamentos/sucesso/"
URL_ERRO = f"{BASE_URL}/pagamentos/erro/"
URL_CANCELAMENTO = f"{BASE_URL}/pagamentos/cancelado/"

# =============================================================================
# CONFIGURAÇÕES DO ASAAS (ALTERNATIVA)
# =============================================================================

# Obtenha em: https://www.asaas.com/api/v3/
ASAAS_API_KEY_SANDBOX = "$aact_YTU5YTE0M2M2N2I4MTliNzk0YTI5N2U5MzdjNWZmNDQ6OjAwMDAwMDAwMDAwMDAwNzI1Mjk6OiRhYWRkOmY3YjJhMjljLTI0YjItNGY4Yy1iNzI4LWI4NzZkNDVkNGY4Nw=="
ASAAS_API_KEY_PRODUCAO = "$aact_SUA_API_KEY_AQUI"

# Use sandbox para testes
ASAAS_USAR_SANDBOX = True

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

# Métodos de pagamento habilitados
PIX_HABILITADO = True
CARTAO_HABILITADO = True
BOLETO_HABILITADO = True

# Configurações de parcelamento
PARCELAS_MAXIMAS = 12
PARCELAS_SEM_JUROS = 3
JUROS_MENSAL = 2.99  # %

# Configurações de boleto
BOLETO_VENCIMENTO_DIAS = 3
BOLETO_INSTRUCOES = "Pagamento referente ao plano do sistema imobiliário"

# =============================================================================
# WEBHOOKS
# =============================================================================

# URLs para receber notificações dos gateways
WEBHOOK_MERCADOPAGO = f"{BASE_URL}/pagamentos/webhook/mercadopago/"
WEBHOOK_ASAAS = f"{BASE_URL}/pagamentos/webhook/asaas/"

# =============================================================================
# CONFIGURAÇÕES DE EMAIL
# =============================================================================

# Para envio de comprovantes e notificações
EMAIL_PAGAMENTOS = "pagamentos@suaempresa.com"
EMAIL_FINANCEIRO = "financeiro@suaempresa.com"

# =============================================================================
# FUNÇÃO PARA APLICAR CONFIGURAÇÕES
# =============================================================================

def aplicar_configuracoes():
    """
    Aplica as configurações no sistema
    Execute: python -c "from config_pagamentos import aplicar_configuracoes; aplicar_configuracoes()"
    """
    import os
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
    django.setup()
    
    from pagamentos.models import ConfiguracaoPagamento
    
    # Obter configuração
    config = ConfiguracaoPagamento.get_configuracao()
    
    # Aplicar configurações do Mercado Pago
    if MERCADOPAGO_USAR_SANDBOX:
        config.gateway_api_key = MERCADOPAGO_ACCESS_TOKEN_SANDBOX
        config.gateway_endpoint = "https://api.mercadopago.com"
        print("🔧 Configurado Mercado Pago SANDBOX")
    else:
        config.gateway_api_key = MERCADOPAGO_ACCESS_TOKEN_PRODUCAO
        config.gateway_endpoint = "https://api.mercadopago.com"
        print("🚀 Configurado Mercado Pago PRODUÇÃO")
    
    # Configurações PIX
    config.pix_habilitado = PIX_HABILITADO
    config.pix_chave = PIX_CHAVE
    config.pix_nome_recebedor = PIX_NOME_RECEBEDOR
    
    # Configurações gerais
    config.cartao_habilitado = CARTAO_HABILITADO
    config.boleto_habilitado = BOLETO_HABILITADO
    
    # URLs
    config.url_sucesso = URL_SUCESSO
    config.url_erro = URL_ERRO
    config.url_cancelamento = URL_CANCELAMENTO
    
    # Salvar
    config.save()
    
    print("✅ Configurações aplicadas com sucesso!")
    print(f"PIX: {'✅' if config.pix_habilitado else '❌'}")
    print(f"Cartão: {'✅' if config.cartao_habilitado else '❌'}")
    print(f"Boleto: {'✅' if config.boleto_habilitado else '❌'}")
    
    return config


def testar_configuracao():
    """
    Testa se a configuração está funcionando
    """
    import os
    import django
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
    django.setup()
    
    from pagamentos.utils import validar_configuracao_pagamento
    
    print("🔄 Testando configuração...")
    
    validacao = validar_configuracao_pagamento()
    
    if validacao['valido']:
        print("✅ Configuração válida!")
    else:
        print("❌ Configuração inválida:")
        for erro in validacao['erros']:
            print(f"  • {erro}")
    
    return validacao['valido']


if __name__ == '__main__':
    print("🔧 Aplicando configurações de pagamento...")
    aplicar_configuracoes()
    
    print("\n🔄 Testando configuração...")
    testar_configuracao()
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Ajuste as configurações neste arquivo")
    print("2. Execute: python config_pagamentos.py")
    print("3. Teste os pagamentos em sandbox")
    print("4. Configure webhooks no gateway")
    print("5. Mude para produção quando pronto")