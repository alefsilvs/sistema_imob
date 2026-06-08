#!/usr/bin/env python
import os
import sys
import django

# Configurar Django ANTES de importar qualquer coisa do Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from saas.models import Tenant, VerificacaoEmail
from core.models_perfil import UsuarioPerfil

def testar_dashboard_autenticado():
    try:
        # Configurar cliente de teste
        client = Client()
        
        # Buscar usuário
        usuario = User.objects.get(username='teste_header')
        print(f"Usuário: {usuario.username} (ID: {usuario.id})")
        
        # Verificar email
        try:
            verificacao = VerificacaoEmail.objects.get(usuario=usuario)
            if not verificacao.email_verificado:
                verificacao.email_verificado = True
                verificacao.data_verificacao = timezone.now()
                verificacao.save()
                print("Email marcado como verificado")
            else:
                print("Email já estava verificado")
        except VerificacaoEmail.DoesNotExist:
            print("Criando verificação de email...")
            VerificacaoEmail.objects.create(
                usuario=usuario,
                email_verificado=True,
                data_verificacao=timezone.now()
            )
        
        # Verificar tenant
        try:
            tenant = Tenant.objects.get(usuario_admin=usuario)
            print(f"Tenant encontrado: {tenant.nome_empresa} (ID: {tenant.id})")
        except Tenant.DoesNotExist:
            print("Tenant não encontrado - isso pode estar causando problemas")
            return False
        
        # Verificar perfil
        try:
            usuario_perfil = UsuarioPerfil.objects.get(usuario=usuario, ativo=True)
            print(f"Perfil encontrado: {usuario_perfil.perfil.nome}")
        except UsuarioPerfil.DoesNotExist:
            print("Perfil não encontrado - isso pode estar causando problemas")
            return False
        
        # FORÇAR LOGIN usando force_login (método mais confiável)
        client.force_login(usuario)
        print("Usuário autenticado via force_login")
        
        # Configurar tenant_id na sessão
        session = client.session
        session['tenant_id'] = tenant.id
        session.save()
        print(f"Tenant ID {tenant.id} configurado na sessão")
        
        # Testar acesso ao dashboard
        print("\n=== Testando Dashboard Autenticado ===")
        response = client.get('/dashboard/', follow=False)
        print(f"Dashboard inicial - Status: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.get('Location', '')
            print(f"Redirecionamento para: {redirect_url}")
            
            # Seguir redirecionamentos até encontrar página final
            max_redirects = 10
            current_url = '/dashboard/'
            
            for i in range(max_redirects):
                response = client.get(current_url, follow=False)
                print(f"Tentativa {i+1} - URL: {current_url} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✓ Página final alcançada: {current_url}")
                    
                    # Analisar conteúdo
                    content = response.content.decode('utf-8')
                    
                    # Contar elementos
                    header_count = content.count('<header')
                    div_count = content.count('<div')
                    nav_count = content.count('<nav')
                    
                    print(f"Elementos <header>: {header_count}")
                    print(f"Elementos <nav>: {nav_count}")
                    print(f"Elementos <div>: {div_count}")
                    
                    # Verificar indicadores específicos
                    has_header_class = 'class="header"' in content
                    has_header_id = 'id="header"' in content
                    has_navbar = 'navbar' in content.lower()
                    has_dashboard = 'dashboard' in content.lower()
                    
                    print(f"Tem class='header': {has_header_class}")
                    print(f"Tem id='header': {has_header_id}")
                    print(f"Tem navbar: {has_navbar}")
                    print(f"Tem dashboard: {has_dashboard}")
                    
                    # Salvar HTML para análise
                    with open('dashboard_authenticated.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("HTML salvo em dashboard_authenticated.html")
                    
                    # Verificar se há erros
                    if 'error' in content.lower() or 'erro' in content.lower():
                        print("⚠️ Possíveis erros encontrados no HTML")
                    
                    # Verificar se é realmente o dashboard ou página de login
                    if 'login' in content.lower() and 'password' in content.lower():
                        print("⚠️ Ainda está na página de login!")
                        return False
                    
                    return True
                    
                elif response.status_code == 302:
                    current_url = response.get('Location', '')
                    if not current_url.startswith('/'):
                        break
                else:
                    print(f"Status inesperado: {response.status_code}")
                    break
            
            print("✗ Muitos redirecionamentos ou loop detectado")
            return False
        
        elif response.status_code == 200:
            print("✓ Dashboard acessado diretamente")
            content = response.content.decode('utf-8')
            
            # Analisar conteúdo
            header_count = content.count('<header')
            div_count = content.count('<div')
            nav_count = content.count('<nav')
            
            print(f"Elementos <header>: {header_count}")
            print(f"Elementos <nav>: {nav_count}")
            print(f"Elementos <div>: {div_count}")
            
            # Salvar HTML
            with open('dashboard_authenticated.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("HTML salvo em dashboard_authenticated.html")
            
            return True
        
        else:
            print(f"Status inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=== Teste Dashboard com Autenticação Forçada ===")
    sucesso = testar_dashboard_autenticado()
    
    if sucesso:
        print("\n✓ Teste concluído com sucesso")
    else:
        print("\n✗ Teste falhou")