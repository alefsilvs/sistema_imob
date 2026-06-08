#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from pagamentos.models import ConfiguracaoPagamento

print("=== CONFIGURAÇÃO PIX ATUAL ===")

try:
    config = ConfiguracaoPagamento.get_configuracao()
    
    print(f"PIX Habilitado: {config.pix_habilitado}")
    print(f"Chave PIX: {config.pix_chave or 'Não configurada'}")
    print(f"Nome do Recebedor: {config.pix_nome_recebedor or 'Não configurado'}")
    
    if config.pix_habilitado and config.pix_chave:
        print("\n✅ PIX está configurado e habilitado")
        print(f"\n📋 RESUMO:")
        print(f"   • Os pagamentos PIX serão direcionados para a chave: {config.pix_chave}")
        print(f"   • Nome que aparecerá no PIX: {config.pix_nome_recebedor or 'SISTEMA IMOBILIARIO'}")
        print(f"   • Cidade: SAO PAULO (padrão do sistema)")
    else:
        print("\n⚠️ PIX não está totalmente configurado")
        if not config.pix_habilitado:
            print("   • PIX está desabilitado")
        if not config.pix_chave:
            print("   • Chave PIX não foi configurada")
            
except Exception as e:
    print(f"❌ Erro ao verificar configuração: {e}")

print("\n=== COMO CONFIGURAR ===")
print("Para configurar o PIX, acesse:")
print("1. Admin do Django: /admin/pagamentos/configuracaopagamento/")
print("2. Configure a chave PIX (email, telefone, CPF/CNPJ ou chave aleatória)")
print("3. Configure o nome do recebedor")
print("4. Certifique-se de que 'PIX Habilitado' está marcado")