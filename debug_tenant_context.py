#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug do contexto do tenant na view mapa_bancas_feira
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from saas.models import Tenant
from imoveis.models import LayoutFeira, BancaFeira
from imoveis.views import mapa_bancas_feira

def debug_tenant_context():
    print("🔍 DEBUG DO CONTEXTO DO TENANT")
    print("=" * 50)
    
    # Buscar dados
    tenant = Tenant.objects.get(nome_empresa="Y.L. EMPREENDIMENTOS")
    user = User.objects.get(username='alef')
    
    print(f"✓ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
    print(f"✓ Usuário: {user.username}")
    
    # Criar request factory
    factory = RequestFactory()
    request = factory.get('/imoveis/bancas/mapa/')
    
    # Configurar sessão
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Configurar autenticação
    auth_middleware = AuthenticationMiddleware(lambda req: None)
    auth_middleware.process_request(request)
    request.user = user
    
    # Configurar tenant manualmente
    request.tenant = tenant
    
    print(f"\n📋 CONTEXTO DA REQUEST:")
    print(f"  ✓ request.user: {request.user}")
    print(f"  ✓ request.user.is_authenticated: {request.user.is_authenticated}")
    print(f"  ✓ request.tenant: {getattr(request, 'tenant', 'Não definido')}")
    
    # Verificar dados no banco
    layouts = LayoutFeira.objects.filter(tenant=tenant, ativo=True)
    bancas = BancaFeira.objects.filter(tenant=tenant)
    
    print(f"\n📊 DADOS DO BANCO:")
    print(f"  ✓ Layouts ativos: {layouts.count()}")
    print(f"  ✓ Bancas: {bancas.count()}")
    
    if layouts.exists():
        layout = layouts.first()
        print(f"  ✓ Layout selecionado: {layout.nome} (Setor: {layout.setor})")
        print(f"  ✓ Dimensões: {layout.linhas}x{layout.colunas}")
        
        # Verificar bancas do setor
        bancas_setor = bancas.filter(setor=layout.setor)
        print(f"  ✓ Bancas do setor {layout.setor}: {bancas_setor.count()}")
    
    # Executar a view
    print(f"\n🎯 EXECUTANDO VIEW:")
    try:
        response = mapa_bancas_feira(request)
        print(f"  ✓ Status: {response.status_code}")
        
        # Verificar se o contexto tem mapa_dados
        if hasattr(response, 'context_data'):
            context = response.context_data
            mapa_dados = context.get('mapa_dados')
            print(f"  ✓ mapa_dados no contexto: {'Sim' if mapa_dados else 'Não'}")
            if mapa_dados:
                print(f"    - Layout: {mapa_dados.get('layout')}")
                print(f"    - Matriz: {len(mapa_dados.get('matriz', []))} linhas")
        else:
            print("  ⚠️ Contexto não disponível")
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")

if __name__ == "__main__":
    debug_tenant_context()