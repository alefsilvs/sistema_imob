#!/usr/bin/env python
"""
Script para verificar layouts de feira e bancas existentes no sistema
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from imoveis.models import LayoutFeira, BancaFeira
from saas.models import Tenant

def verificar_layouts_bancas():
    """Verifica layouts e bancas existentes para o tenant Y.L. EMPREENDIMENTOS"""
    
    try:
        # Buscar o tenant
        tenant = Tenant.objects.get(nome_empresa="Y.L. EMPREENDIMENTOS")
        print(f"✓ Tenant encontrado: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Verificar layouts existentes
        layouts = LayoutFeira.objects.filter(tenant=tenant)
        print(f"\n📋 Layouts existentes para {tenant.nome_empresa}: {layouts.count()}")
        
        if layouts.exists():
            for layout in layouts:
                print(f"  - {layout.nome}")
                print(f"    Setor: {layout.setor}")
                print(f"    Dimensões: {layout.linhas}x{layout.colunas}")
                print(f"    Ativo: {'Sim' if layout.ativo else 'Não'}")
                print(f"    Criado em: {layout.created_at.strftime('%d/%m/%Y %H:%M')}")
                print()
        else:
            print("  ❌ Nenhum layout encontrado para este tenant.")
        
        # Verificar bancas existentes
        bancas = BancaFeira.objects.filter(tenant=tenant)
        print(f"🏪 Bancas existentes para {tenant.nome_empresa}: {bancas.count()}")
        
        if bancas.exists():
            setores = bancas.values_list('setor', flat=True).distinct()
            print(f"  Setores das bancas: {list(setores)}")
            
            # Mostrar algumas bancas como exemplo
            print("\n  Exemplos de bancas:")
            for banca in bancas[:5]:
                print(f"    - Banca {banca.numero_banca} (Código: {banca.codigo})")
                print(f"      Setor: {banca.setor}")
                print(f"      Posição: Linha {banca.posicao_linha}, Coluna {banca.posicao_coluna}")
                print(f"      Status: {banca.get_status_display()}")
                print()
        else:
            print("  ❌ Nenhuma banca encontrada para este tenant.")
        
        return layouts.count(), bancas.count()
        
    except Tenant.DoesNotExist:
        print("❌ Tenant 'Y.L. EMPREENDIMENTOS' não encontrado!")
        return 0, 0
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🔍 Verificando layouts e bancas de feira...")
    print("=" * 50)
    
    layouts_count, bancas_count = verificar_layouts_bancas()
    
    print("=" * 50)
    print("📊 RESUMO:")
    print(f"  Layouts encontrados: {layouts_count}")
    print(f"  Bancas encontradas: {bancas_count}")
    
    if layouts_count == 0:
        print("\n💡 RECOMENDAÇÃO:")
        print("  É necessário criar um layout de feira para visualizar o mapa.")
        print("  Acesse: /imoveis/layouts/criar/ para criar um novo layout.")