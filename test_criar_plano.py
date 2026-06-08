#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from saas.models import PlanoComercial
from decimal import Decimal

def test_criar_plano():
    try:
        print("Testando criação de plano...")
        
        # Tentar criar um plano básico
        plano_basico = PlanoComercial.objects.create(
            nome='Plano Básico',
            tipo='basico',
            preco_mensal=Decimal('99.90'),
            max_usuarios=5,
            max_imoveis=200,
            max_contratos=100,
            storage_gb=10,
            api_calls_mes=2000,
            ativo=True
        )
        
        print(f"✅ Plano básico criado com sucesso: {plano_basico.nome}")
        print(f"   ID: {plano_basico.id}")
        print(f"   Preço: R$ {plano_basico.preco_mensal}")
        
        # Tentar criar um plano profissional
        plano_pro = PlanoComercial.objects.create(
            nome='Plano Profissional',
            tipo='profissional',
            preco_mensal=Decimal('199.90'),
            preco_anual=Decimal('1999.00'),
            max_usuarios=15,
            max_imoveis=500,
            max_contratos=300,
            storage_gb=25,
            api_calls_mes=5000,
            suporte_prioritario=True,
            backup_automatico=True,
            ativo=True
        )
        
        print(f"✅ Plano profissional criado com sucesso: {plano_pro.nome}")
        print(f"   ID: {plano_pro.id}")
        print(f"   Preço: R$ {plano_pro.preco_mensal}")
        
        # Listar todos os planos
        print("\n📋 Todos os planos:")
        planos = PlanoComercial.objects.all()
        for plano in planos:
            print(f"   - {plano.nome} ({plano.tipo}) - R$ {plano.preco_mensal}/mês")
            
    except Exception as e:
        print(f"❌ Erro ao criar plano: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_criar_plano()