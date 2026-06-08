#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.middleware.csrf import get_token

def testar_middleware_auth():
    print("=== TESTE DE MIDDLEWARE E AUTENTICAÇÃO ===")
    print()
    
    # Verificar middlewares ativos
    print("1. MIDDLEWARES ATIVOS:")
    for i, middleware in enumerate(settings.MIDDLEWARE, 1):
        print(f"   {i}. {middleware}")
    
    print()
    print("2. TESTANDO ACESSO ÀS URLS DE AUTENTICAÇÃO:")
    
    client = Client()
    
    # URLs de autenticação para testar
    auth_urls = [
        ('login', '/accounts/login/'),
        ('password_reset', '/accounts/password_reset/'),
        ('password_reset_done', '/accounts/password_reset/done/'),
        ('password_reset_complete', '/accounts/reset/done/'),
    ]
    
    for url_name, url_path in auth_urls:
        try:
            print(f"\n   Testando {url_name} ({url_path}):")
            
            # Teste GET
            response = client.get(url_path)
            print(f"   ✅ GET: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Página carregada com sucesso")
                
                # Verificar se há conteúdo HTML
                content = response.content.decode('utf-8')
                if 'form' in content.lower():
                    print(f"   ✅ Formulário encontrado na página")
                else:
                    print(f"   ⚠️  Nenhum formulário encontrado")
                    
            elif response.status_code in [301, 302]:
                print(f"   ✅ Redirecionamento para: {response.get('Location', 'N/A')}")
            else:
                print(f"   ❌ Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro ao acessar {url_name}: {e}")
    
    print()
    print("3. TESTANDO FORMULÁRIO DE RECUPERAÇÃO DE SENHA:")
    
    try:
        # Obter página de recuperação
        response = client.get('/accounts/password_reset/')
        
        if response.status_code == 200:
            print("   ✅ Página de recuperação acessível")
            
            # Obter token CSRF
            csrf_token = get_token(client)
            
            # Testar envio do formulário
            form_data = {
                'email': 'cliente@teste.com',
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = client.post('/accounts/password_reset/', form_data)
            
            if response.status_code == 302:
                print("   ✅ Formulário enviado com sucesso (redirecionamento)")
                print(f"   ✅ Redirecionado para: {response.get('Location', 'N/A')}")
            elif response.status_code == 200:
                print("   ⚠️  Formulário retornou à mesma página (possível erro)")
                content = response.content.decode('utf-8')
                if 'error' in content.lower() or 'erro' in content.lower():
                    print("   ❌ Possível erro no formulário")
            else:
                print(f"   ❌ Status inesperado no POST: {response.status_code}")
                
        else:
            print(f"   ❌ Não foi possível acessar a página: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro no teste do formulário: {e}")
    
    print()
    print("4. VERIFICANDO MIDDLEWARES DE SEGURANÇA:")
    
    # Verificar se middlewares de segurança estão bloqueando
    security_middlewares = [
        'security.middleware.SecurityMiddleware',
        'security.middleware.LoginSecurityMiddleware', 
        'security.middleware.CSRFSecurityMiddleware',
        'security.middleware.MasterUserMiddleware'
    ]
    
    for middleware in security_middlewares:
        if middleware in settings.MIDDLEWARE:
            print(f"   ✅ {middleware} - ATIVO")
        else:
            print(f"   ❌ {middleware} - INATIVO")
    
    print()
    print("5. VERIFICANDO MIDDLEWARES DE TENANT/SAAS:")
    
    tenant_middlewares = [
        'saas.middleware.TenantMiddleware',
        'saas.middleware.TenantDatabaseMiddleware',
        'saas.middleware.TenantSecurityMiddleware'
    ]
    
    for middleware in tenant_middlewares:
        if middleware in settings.MIDDLEWARE:
            print(f"   ✅ {middleware} - ATIVO")
        else:
            print(f"   ❌ {middleware} - INATIVO")
    
    print()
    print("6. VERIFICANDO MIDDLEWARES DESABILITADOS:")
    
    disabled_middlewares = [
        'saas.middleware_pkg.trial_middleware.TrialMiddleware',
        'assinaturas.middleware.ControleAssinaturaMiddleware',
        'assinaturas.middleware.LimiteRecursosMiddleware'
    ]
    
    for middleware in disabled_middlewares:
        if middleware in settings.MIDDLEWARE:
            print(f"   ❌ {middleware} - ATIVO (deveria estar desabilitado)")
        else:
            print(f"   ✅ {middleware} - DESABILITADO")
    
    print()
    print("7. TESTANDO COM USUÁRIO AUTENTICADO:")
    
    try:
        # Criar/obter usuário de teste
        user, created = User.objects.get_or_create(
            username='teste_middleware',
            defaults={
                'email': 'teste@middleware.com',
                'is_active': True
            }
        )
        
        if created:
            user.set_password('123456')
            user.save()
            print(f"   ✅ Usuário de teste criado: {user.username}")
        else:
            print(f"   ✅ Usuário de teste encontrado: {user.username}")
        
        # Fazer login
        client.force_login(user)
        print(f"   ✅ Login realizado com sucesso")
        
        # Testar acesso a páginas protegidas
        protected_urls = [
            '/dashboard/',
            '/admin/',
        ]
        
        for url in protected_urls:
            try:
                response = client.get(url)
                print(f"   ✅ {url}: Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Erro ao acessar {url}: {e}")
                
    except Exception as e:
        print(f"   ❌ Erro no teste com usuário autenticado: {e}")
    
    print()
    print("=== RESUMO DO TESTE ===")
    
    # Verificar se há problemas conhecidos
    problemas = []
    
    # Verificar middlewares problemáticos
    if 'assinaturas.middleware.ControleAssinaturaMiddleware' in settings.MIDDLEWARE:
        problemas.append("ControleAssinaturaMiddleware está ativo (pode bloquear acesso)")
    
    if 'saas.middleware_pkg.trial_middleware.TrialMiddleware' in settings.MIDDLEWARE:
        problemas.append("TrialMiddleware está ativo (pode bloquear acesso)")
    
    if problemas:
        print("⚠️  PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   - {problema}")
    else:
        print("✅ NENHUM PROBLEMA CRÍTICO ENCONTRADO")
    
    print()
    print("=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    testar_middleware_auth()