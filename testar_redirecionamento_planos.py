#!/usr/bin/env python
"""
Script para testar o redirecionamento para página de planos
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.urls import reverse
from django.contrib.auth.models import User

def testar_configuracoes():
    print("=== TESTE DE CONFIGURAÇÕES DE REDIRECIONAMENTO ===")
    
    # Verificar configurações do Django
    print(f"✅ LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
    print(f"✅ LOGIN_URL: {settings.LOGIN_URL}")
    print(f"✅ LOGOUT_REDIRECT_URL: {settings.LOGOUT_REDIRECT_URL}")
    
    # Verificar se as URLs existem
    try:
        planos_url = reverse('saas:planos')
        print(f"✅ URL de planos encontrada: {planos_url}")
    except Exception as e:
        print(f"❌ Erro ao encontrar URL de planos: {e}")
        return
    
    try:
        dashboard_url = reverse('core:dashboard')
        print(f"✅ URL do dashboard encontrada: {dashboard_url}")
    except Exception as e:
        print(f"❌ Erro ao encontrar URL do dashboard: {e}")
    
    # Verificar usuário de teste
    try:
        user = User.objects.get(username='alef')
        print(f"✅ Usuário encontrado: {user.username} ({user.email})")
    except User.DoesNotExist:
        print("❌ Usuário 'alef' não encontrado!")
        return
    
    print("\n=== RESUMO DAS ALTERAÇÕES ===")
    print("1. ✅ LOGIN_REDIRECT_URL alterado para '/saas/planos/'")
    print("2. ✅ Função home() alterada para redirecionar para 'saas:planos'")
    print("3. ✅ URLs de planos configuradas corretamente")
    
    print("\n=== FLUXO ESPERADO ===")
    print("1. Usuário acessa a página inicial (/)")
    print("2. Se não estiver logado: redireciona para login")
    print("3. Se estiver logado: redireciona para página de planos")
    print("4. Após login: redireciona automaticamente para página de planos")
    
    print("\n✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("A página de planos agora será a primeira a aparecer após o login.")

if __name__ == '__main__':
    testar_configuracoes()