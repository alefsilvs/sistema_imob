#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar o envio de notificações com o novo serviço tenant-aware
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.utils import timezone
from saas.models import Tenant
from core.models import Inquilino
from notificacoes.models import Notificacao
from notificacoes.tenant_whatsapp_service import get_whatsapp_service_for_tenant
from notificacoes.views import enviar_notificacao_individual

def testar_servico_tenant():
    print("🧪 TESTE DO SERVIÇO WHATSAPP TENANT-AWARE")
    print("=" * 60)
    
    # 1. Verificar tenants disponíveis
    print("\n1. TENANTS DISPONÍVEIS:")
    tenants = Tenant.objects.all()
    for tenant in tenants:
        print(f"   📋 {tenant.nome_empresa} (slug: {tenant.slug})")
        
        # Verificar se tem instância Evolution
        from saas.evolution_models import EvolutionInstance
        evolution_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
        if evolution_instance:
            print(f"      ✅ Instância Evolution: {evolution_instance.instance_name}")
            print(f"      📊 Status: {evolution_instance.status}")
        else:
            print(f"      ❌ Sem instância Evolution")
    
    # 2. Testar serviço para tenant específico
    print("\n2. TESTE DO SERVIÇO WHATSAPP:")
    
    # Buscar um tenant com instância Evolution
    tenant_com_instancia = None
    for tenant in tenants:
        evolution_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
        if evolution_instance:
            tenant_com_instancia = tenant
            break
    
    if tenant_com_instancia:
        print(f"   🎯 Testando com tenant: {tenant_com_instancia.nome_empresa}")
        
        # Criar serviço para o tenant
        whatsapp_service = get_whatsapp_service_for_tenant(tenant_com_instancia)
        
        print(f"   📱 Provedor: {whatsapp_service.provider}")
        print(f"   ⚙️  Configurado: {whatsapp_service.is_configured()}")
        
        # Obter informações da instância
        instance_info = whatsapp_service.get_instance_info()
        print(f"   📊 Tipo de instância: {instance_info['type']}")
        print(f"   🏷️  Nome da instância: {instance_info['instance_name']}")
        
        if instance_info['type'] == 'tenant_specific':
            print(f"   ✅ Usando instância específica do tenant!")
            print(f"   🌐 Server URL: {instance_info['server_url']}")
            print(f"   📊 Status: {instance_info['status']}")
        else:
            print(f"   ⚠️  Usando instância global (fallback)")
    
    else:
        print("   ❌ Nenhum tenant com instância Evolution encontrado")
        
        # Testar com tenant sem instância (deve usar global)
        tenant_sem_instancia = tenants.first()
        if tenant_sem_instancia:
            print(f"   🎯 Testando fallback com tenant: {tenant_sem_instancia.nome_empresa}")
            
            whatsapp_service = get_whatsapp_service_for_tenant(tenant_sem_instancia)
            instance_info = whatsapp_service.get_instance_info()
            
            print(f"   📊 Tipo de instância: {instance_info['type']}")
            print(f"   🏷️  Nome da instância: {instance_info['instance_name']}")
    
    # 3. Testar criação de notificação (sem enviar)
    print("\n3. TESTE DE CRIAÇÃO DE NOTIFICAÇÃO:")
    
    # Buscar um inquilino para teste
    inquilino = Inquilino.objects.first()
    if inquilino:
        print(f"   👤 Inquilino: {inquilino.nome}")
        print(f"   🏢 Tenant do inquilino: {getattr(inquilino, 'tenant', 'N/A')}")
        
        # Criar notificação de teste (sem salvar)
        notificacao_teste = Notificacao(
            inquilino=inquilino,
            canal='WHATSAPP',
            destinatario='5511999999999',
            assunto='Teste Tenant WhatsApp',
            corpo='Esta é uma mensagem de teste para verificar o tenant correto.',
            status='PENDENTE'
        )
        
        print(f"   📧 Notificação criada (não salva)")
        print(f"   📱 Canal: {notificacao_teste.canal}")
        print(f"   📞 Destinatário: {notificacao_teste.destinatario}")
        
        # Verificar qual tenant seria usado
        tenant_da_notificacao = getattr(notificacao_teste.inquilino, 'tenant', None)
        if tenant_da_notificacao:
            print(f"   🎯 Tenant que seria usado: {tenant_da_notificacao.nome_empresa}")
            
            # Verificar qual instância seria usada
            whatsapp_service = get_whatsapp_service_for_tenant(tenant_da_notificacao)
            instance_info = whatsapp_service.get_instance_info()
            print(f"   🏷️  Instância que seria usada: {instance_info['instance_name']}")
            print(f"   📊 Tipo: {instance_info['type']}")
        else:
            print(f"   ⚠️  Inquilino sem tenant - usaria instância global")
    
    else:
        print("   ❌ Nenhum inquilino encontrado para teste")
    
    print("\n✅ TESTE CONCLUÍDO!")
    print("💡 Para testar o envio real, use a interface web ou modifique este script")

if __name__ == "__main__":
    testar_servico_tenant()