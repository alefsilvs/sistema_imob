#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corrigir a associação de inquilinos aos tenants
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.db import transaction
from saas.models import Tenant
from core.models import Inquilino

def corrigir_tenant_inquilinos():
    print("🔧 CORREÇÃO DE TENANT DOS INQUILINOS")
    print("=" * 50)
    
    # 1. Verificar situação atual
    print("\n1. SITUAÇÃO ATUAL:")
    total_inquilinos = Inquilino.objects.count()
    inquilinos_sem_tenant = Inquilino.objects.filter(tenant__isnull=True).count()
    inquilinos_com_tenant = Inquilino.objects.filter(tenant__isnull=False).count()
    
    print(f"   📊 Total de inquilinos: {total_inquilinos}")
    print(f"   ❌ Sem tenant: {inquilinos_sem_tenant}")
    print(f"   ✅ Com tenant: {inquilinos_com_tenant}")
    
    # 2. Listar tenants disponíveis
    print("\n2. TENANTS DISPONÍVEIS:")
    tenants = Tenant.objects.all()
    for i, tenant in enumerate(tenants, 1):
        print(f"   {i}. {tenant.nome_empresa} (slug: {tenant.slug})")
    
    if inquilinos_sem_tenant == 0:
        print("\n✅ Todos os inquilinos já têm tenant associado!")
        return
    
    # 3. Estratégias de correção
    print(f"\n3. ESTRATÉGIAS DE CORREÇÃO PARA {inquilinos_sem_tenant} INQUILINOS:")
    print("   A. Associar todos a um tenant específico")
    print("   B. Associar baseado em algum critério (ex: primeiro tenant)")
    print("   C. Listar inquilinos sem tenant para análise manual")
    
    # Para este exemplo, vamos usar a estratégia B (primeiro tenant ativo)
    tenant_padrao = tenants.first()
    if not tenant_padrao:
        print("   ❌ Nenhum tenant encontrado!")
        return
    
    print(f"\n4. USANDO TENANT PADRÃO: {tenant_padrao.nome_empresa}")
    
    # Confirmar antes de proceder
    resposta = input(f"\n❓ Deseja associar todos os {inquilinos_sem_tenant} inquilinos ao tenant '{tenant_padrao.nome_empresa}'? (s/N): ")
    
    if resposta.lower() not in ['s', 'sim', 'y', 'yes']:
        print("   ❌ Operação cancelada pelo usuário")
        return
    
    # 5. Executar correção
    print("\n5. EXECUTANDO CORREÇÃO:")
    
    try:
        with transaction.atomic():
            inquilinos_atualizados = Inquilino.objects.filter(tenant__isnull=True).update(tenant=tenant_padrao)
            
            print(f"   ✅ {inquilinos_atualizados} inquilinos atualizados com sucesso!")
            
            # Verificar resultado
            inquilinos_sem_tenant_apos = Inquilino.objects.filter(tenant__isnull=True).count()
            inquilinos_com_tenant_apos = Inquilino.objects.filter(tenant__isnull=False).count()
            
            print(f"\n6. RESULTADO FINAL:")
            print(f"   📊 Total de inquilinos: {total_inquilinos}")
            print(f"   ❌ Sem tenant: {inquilinos_sem_tenant_apos}")
            print(f"   ✅ Com tenant: {inquilinos_com_tenant_apos}")
            
            if inquilinos_sem_tenant_apos == 0:
                print(f"\n🎉 SUCESSO! Todos os inquilinos agora têm tenant associado!")
            
    except Exception as e:
        print(f"   ❌ Erro durante a correção: {e}")
        return
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Teste o envio de notificações novamente")
    print("   2. Verifique se as instâncias Evolution corretas estão sendo usadas")
    print("   3. Execute: python testar_notificacao_tenant.py")

def listar_inquilinos_sem_tenant():
    """Lista inquilinos sem tenant para análise"""
    print("\n📋 INQUILINOS SEM TENANT:")
    inquilinos = Inquilino.objects.filter(tenant__isnull=True)[:10]  # Primeiros 10
    
    for inquilino in inquilinos:
        print(f"   👤 {inquilino.nome} (ID: {inquilino.id})")
        if hasattr(inquilino, 'email'):
            print(f"      📧 {inquilino.email}")
        if hasattr(inquilino, 'telefone'):
            print(f"      📞 {inquilino.telefone}")
    
    if Inquilino.objects.filter(tenant__isnull=True).count() > 10:
        print(f"   ... e mais {Inquilino.objects.filter(tenant__isnull=True).count() - 10} inquilinos")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--listar':
        listar_inquilinos_sem_tenant()
    else:
        corrigir_tenant_inquilinos()