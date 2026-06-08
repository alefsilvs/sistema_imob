#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para associar inquilinos ao tenant com instância Evolution
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.db import transaction
from saas.models import Tenant
from saas.evolution_models import EvolutionInstance
from core.models import Inquilino

def associar_inquilinos_tenant_evolution():
    print("🔧 ASSOCIAÇÃO DE INQUILINOS AO TENANT COM EVOLUTION")
    print("=" * 60)
    
    # 1. Encontrar tenant com instância Evolution
    print("\n1. BUSCANDO TENANT COM INSTÂNCIA EVOLUTION:")
    
    tenant_com_evolution = None
    evolution_instance = None
    
    for tenant in Tenant.objects.all():
        instance = EvolutionInstance.objects.filter(tenant=tenant).first()
        if instance:
            tenant_com_evolution = tenant
            evolution_instance = instance
            print(f"   ✅ Encontrado: {tenant.nome_empresa}")
            print(f"   📱 Instância: {instance.instance_name}")
            print(f"   📊 Status: {instance.status}")
            break
    
    if not tenant_com_evolution:
        print("   ❌ Nenhum tenant com instância Evolution encontrado!")
        return
    
    # 2. Verificar inquilinos sem tenant
    inquilinos_sem_tenant = Inquilino.objects.filter(tenant__isnull=True)
    total_sem_tenant = inquilinos_sem_tenant.count()
    
    print(f"\n2. INQUILINOS SEM TENANT: {total_sem_tenant}")
    
    if total_sem_tenant == 0:
        print("   ✅ Todos os inquilinos já têm tenant!")
        return
    
    # 3. Listar alguns inquilinos
    print("\n3. PRIMEIROS INQUILINOS SEM TENANT:")
    for inquilino in inquilinos_sem_tenant[:5]:
        print(f"   👤 {inquilino.nome} (ID: {inquilino.id})")
    
    if total_sem_tenant > 5:
        print(f"   ... e mais {total_sem_tenant - 5} inquilinos")
    
    # 4. Executar associação
    print(f"\n4. ASSOCIANDO AO TENANT: {tenant_com_evolution.nome_empresa}")
    
    try:
        with transaction.atomic():
            inquilinos_atualizados = inquilinos_sem_tenant.update(tenant=tenant_com_evolution)
            
            print(f"   ✅ {inquilinos_atualizados} inquilinos associados com sucesso!")
            
            # Verificar resultado
            inquilinos_sem_tenant_apos = Inquilino.objects.filter(tenant__isnull=True).count()
            inquilinos_com_tenant_apos = Inquilino.objects.filter(tenant__isnull=False).count()
            
            print(f"\n5. RESULTADO:")
            print(f"   ❌ Sem tenant: {inquilinos_sem_tenant_apos}")
            print(f"   ✅ Com tenant: {inquilinos_com_tenant_apos}")
            
            # Verificar quantos inquilinos estão no tenant com Evolution
            inquilinos_no_tenant_evolution = Inquilino.objects.filter(tenant=tenant_com_evolution).count()
            print(f"   📱 No tenant com Evolution: {inquilinos_no_tenant_evolution}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    print(f"\n🎉 SUCESSO!")
    print(f"💡 Agora os inquilinos usarão a instância Evolution: {evolution_instance.instance_name}")
    print(f"🧪 Execute: python testar_notificacao_tenant.py")

if __name__ == "__main__":
    associar_inquilinos_tenant_evolution()