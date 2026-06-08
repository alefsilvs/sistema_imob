#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar tags semânticas HTML5 no sistema
"""

import os
import sys
import django

# Configurar Django ANTES de importar qualquer coisa do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from bs4 import BeautifulSoup
import re

from saas.models import Tenant, VerificacaoEmail
from core.models_perfil import PerfilUsuario, UsuarioPerfil

def verificar_tags_semanticas():
    """Verifica se as tags semânticas HTML5 estão sendo renderizadas corretamente"""
    
    print("🔍 VERIFICAÇÃO DE TAGS SEMÂNTICAS HTML5")
    print("=" * 50)
    
    # Criar cliente de teste
    client = Client()
    
    # Usar usuário de teste existente
    try:
        user = User.objects.get(username='teste_html_tags')
        tenant = Tenant.objects.get(usuario_admin=user)
        
        # Fazer login
        login_success = client.login(username='teste_html_tags', password='123456')
        if not login_success:
            print("❌ Falha no login")
            return
        
        # Configurar sessão
        session = client.session
        session['tenant_id'] = tenant.id
        session.save()
        
        print(f"✅ Login realizado como: {user.username}")
        print(f"✅ Tenant configurado: {tenant.nome_empresa}")
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return
    
    # Testar página do mapa
    print("\n📍 Testando página: /imoveis/bancas/mapa/")
    
    response = client.get('/imoveis/bancas/mapa/', follow=True)
    
    if response.status_code != 200:
        print(f"❌ Status: {response.status_code}")
        if response.redirect_chain:
            print(f"   Redirecionamentos: {response.redirect_chain}")
        return
    
    print(f"✅ Status: {response.status_code}")
    
    # Analisar HTML
    html_content = response.content.decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Verificar tags semânticas
    print("\n🏷️  ANÁLISE DAS TAGS SEMÂNTICAS:")
    print("-" * 30)
    
    # HEADER
    headers = soup.find_all('header')
    print(f"📋 HEADER tags encontradas: {len(headers)}")
    for i, header in enumerate(headers, 1):
        classes = header.get('class', [])
        id_attr = header.get('id', '')
        print(f"   #{i}: classes={classes}, id='{id_attr}'")
        
        # Verificar conteúdo
        text_content = header.get_text(strip=True)[:50]
        if text_content:
            print(f"       Conteúdo: {text_content}...")
    
    # MAIN
    mains = soup.find_all('main')
    print(f"\n📋 MAIN tags encontradas: {len(mains)}")
    for i, main in enumerate(mains, 1):
        classes = main.get('class', [])
        id_attr = main.get('id', '')
        print(f"   #{i}: classes={classes}, id='{id_attr}'")
    
    # FOOTER
    footers = soup.find_all('footer')
    print(f"\n📋 FOOTER tags encontradas: {len(footers)}")
    for i, footer in enumerate(footers, 1):
        classes = footer.get('class', [])
        id_attr = footer.get('id', '')
        print(f"   #{i}: classes={classes}, id='{id_attr}'")
        
        # Verificar conteúdo
        text_content = footer.get_text(strip=True)[:50]
        if text_content:
            print(f"       Conteúdo: {text_content}...")
    
    # Verificar balanceamento
    print("\n⚖️  VERIFICAÇÃO DE BALANCEAMENTO:")
    print("-" * 30)
    
    header_open = html_content.count('<header')
    header_close = html_content.count('</header>')
    main_open = html_content.count('<main')
    main_close = html_content.count('</main>')
    footer_open = html_content.count('<footer')
    footer_close = html_content.count('</footer>')
    
    print(f"HEADER: {header_open} aberturas ↔ {header_close} fechamentos")
    print(f"MAIN:   {main_open} aberturas ↔ {main_close} fechamentos")
    print(f"FOOTER: {footer_open} aberturas ↔ {footer_close} fechamentos")
    
    # Verificar problemas
    problemas = []
    
    if header_open != header_close:
        problemas.append(f"❌ Tags HEADER desbalanceadas ({header_open} ≠ {header_close})")
    
    if main_open != main_close:
        problemas.append(f"❌ Tags MAIN desbalanceadas ({main_open} ≠ {main_close})")
    
    if footer_open != footer_close:
        problemas.append(f"❌ Tags FOOTER desbalanceadas ({footer_open} ≠ {footer_close})")
    
    if len(headers) == 0:
        problemas.append("❌ Nenhuma tag HEADER encontrada")
    
    if len(mains) == 0:
        problemas.append("❌ Nenhuma tag MAIN encontrada")
    
    if len(footers) == 0:
        problemas.append("❌ Nenhuma tag FOOTER encontrada")
    
    # Resultado final
    print("\n🎯 RESULTADO FINAL:")
    print("=" * 30)
    
    if problemas:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   {problema}")
    else:
        print("✅ TODAS AS TAGS SEMÂNTICAS ESTÃO CORRETAS!")
        print(f"   • {len(headers)} tag(s) HEADER")
        print(f"   • {len(mains)} tag(s) MAIN")
        print(f"   • {len(footers)} tag(s) FOOTER")
        print("   • Todas as tags estão balanceadas")
    
    # Salvar HTML para análise
    with open('debug_tags_semanticas.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n💾 HTML salvo em: debug_tags_semanticas.html")
    
    return len(problemas) == 0

if __name__ == '__main__':
    sucesso = verificar_tags_semanticas()
    exit(0 if sucesso else 1)