#!/usr/bin/env python3
"""
Script para testar acesso autenticado e verificar tags semânticas
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from saas.models import Tenant, PlanoComercial, VerificacaoEmail
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil
from django.utils import timezone
from datetime import timedelta
import requests
from bs4 import BeautifulSoup

def test_authenticated_access():
    print('=== TESTE DE ACESSO AUTENTICADO ===')
    
    # Criar cliente de teste
    client = Client()
    
    # Criar usuário de teste
    username = 'teste_html_tags'
    password = '123456'
    
    try:
        user = User.objects.get(username=username)
        print(f'✓ Usuário encontrado: {user.username}')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            email='teste@htmltags.com',
            password=password,
            first_name='Teste',
            last_name='HTML Tags'
        )
        print(f'✓ Usuário criado: {user.username}')
    
    # Verificar se usuário tem tenant
    tenant = None
    try:
        tenant = Tenant.objects.get(usuario_admin=user)
        print(f'✓ Tenant encontrado: {tenant.nome_empresa}')
    except Tenant.DoesNotExist:
        # Criar plano de teste
        plano, created = PlanoComercial.objects.get_or_create(
            nome='Plano Teste HTML',
            defaults={
                'preco_mensal': 0.00,
                'max_usuarios': 10,
                'max_imoveis': 100,
                'max_contratos': 50,
                'storage_gb': 5,
                'api_calls_mes': 1000,
                'ativo': True,
                'tipo': 'trial'
            }
        )
        
        # Criar tenant
        tenant = Tenant.objects.create(
            nome_empresa='Empresa Teste HTML Tags',
            slug='teste-html-tags',
            subdominio='teste-html-tags',
            usuario_admin=user,
            plano=plano,
            status='trial',
            trial_ate=timezone.now() + timedelta(days=30)
        )
        print(f'✓ Tenant criado: {tenant.nome_empresa}')
    
    # Criar ou obter perfil de usuário
    try:
        perfil = PerfilUsuario.objects.get(nome='Administrador Teste')
        print(f'✓ Perfil encontrado: {perfil.nome}')
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(
            nome='Administrador Teste',
            tipo='administrador',
            descricao='Perfil de administrador para testes',
            ativo=True
        )
        print(f'✓ Perfil criado: {perfil.nome}')
        
        # Criar abrangências (permissões) para o perfil
        modulos_acoes = [
            ('imoveis', 'visualizar'),
            ('imoveis', 'criar'),
            ('imoveis', 'editar'),
            ('bancas', 'visualizar'),
            ('bancas', 'criar'),
            ('bancas', 'editar'),
            ('configuracoes', 'visualizar'),
            ('configuracoes', 'editar'),
        ]
        
        for modulo, acao in modulos_acoes:
            AbrangenciaPerfil.objects.get_or_create(
                perfil=perfil,
                modulo=modulo,
                acao=acao,
                defaults={'permitido': True}
            )
        
        print(f'✓ Permissões criadas para o perfil {perfil.nome}')
    
    # Associar usuário ao perfil
    try:
        usuario_perfil = UsuarioPerfil.objects.get(usuario=user)
        print(f'✓ Usuário já possui perfil: {usuario_perfil.perfil.nome}')
    except UsuarioPerfil.DoesNotExist:
        usuario_perfil = UsuarioPerfil.objects.create(
            usuario=user,
            perfil=perfil,
            ativo=True,
            observacoes='Perfil criado para testes de HTML'
        )
        print(f'✓ Perfil associado ao usuário: {usuario_perfil.perfil.nome}')
    
    # Verificar/criar verificação de email
    try:
        verificacao = VerificacaoEmail.objects.get(usuario=user)
        if not verificacao.email_verificado:
            verificacao.email_verificado = True
            verificacao.data_verificacao = timezone.now()
            verificacao.save()
            print(f'✓ Email marcado como verificado')
        else:
            print(f'✓ Email já estava verificado')
    except VerificacaoEmail.DoesNotExist:
        verificacao = VerificacaoEmail.objects.create(
            usuario=user,
            email_verificado=True,
            data_verificacao=timezone.now()
        )
        print(f'✓ Verificação de email criada e marcada como verificada')
    
    # Fazer login
    login_success = client.login(username=username, password=password)
    
    if not login_success:
        print('❌ Falha no login')
        return
    
    print(f'✓ Login realizado com sucesso')
    
    # Configurar sessão com tenant_id
    session = client.session
    session['tenant_id'] = tenant.id
    session.save()
    print(f'✓ Sessão configurada com tenant_id: {tenant.id}')
    
    # Testar páginas com usuário autenticado
    pages_to_test = [
        ('/', 'Dashboard'),
        ('/imoveis/bancas/mapa/', 'Mapa das Bancas'),
        ('/imoveis/', 'Lista de Imóveis'),
    ]
    
    for path, name in pages_to_test:
        try:
            print(f'\n🔍 Testando {name}: {path}')
            
            response = client.get(path)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                print(f'   ✓ Status: {response.status_code}')
                
                # Verificar tags semânticas
                headers = soup.find_all('header')
                mains = soup.find_all('main')
                footers = soup.find_all('footer')
                
                print(f'   📊 HEADER tags: {len(headers)}')
                for i, header in enumerate(headers):
                    classes = header.get('class', [])
                    print(f'     #{i+1}: classes={classes}')
                
                print(f'   📊 MAIN tags: {len(mains)}')
                for i, main in enumerate(mains):
                    classes = main.get('class', [])
                    print(f'     #{i+1}: classes={classes}')
                
                print(f'   📊 FOOTER tags: {len(footers)}')
                for i, footer in enumerate(footers):
                    classes = footer.get('class', [])
                    print(f'     #{i+1}: classes={classes}')
                
                # Verificar se está usando o template base correto
                if 'sidebar' in content:
                    print(f'   ✅ Template base com sidebar detectado')
                else:
                    print(f'   ❌ Template base não detectado')
                
                # Verificar balanceamento de tags
                header_open = content.count('<header')
                header_close = content.count('</header>')
                main_open = content.count('<main')
                main_close = content.count('</main>')
                footer_open = content.count('<footer')
                footer_close = content.count('</footer>')
                
                problems = []
                if header_open != header_close:
                    problems.append(f'HEADER ({header_open} vs {header_close})')
                if main_open != main_close:
                    problems.append(f'MAIN ({main_open} vs {main_close})')
                if footer_open != footer_close:
                    problems.append(f'FOOTER ({footer_open} vs {footer_close})')
                
                if problems:
                    print(f'   ❌ Tags desbalanceadas: {", ".join(problems)}')
                else:
                    print(f'   ✅ Todas as tags estão balanceadas')
                
                # Salvar HTML para análise
                if name == 'Mapa das Bancas':
                    with open('debug_mapa_authenticated.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'   💾 HTML salvo em debug_mapa_authenticated.html')
                    
            elif response.status_code in [301, 302]:
                print(f'   ⚠️ Redirecionamento: {response.status_code}')
                if hasattr(response, 'url'):
                    print(f'   → Para: {response.url}')
            else:
                print(f'   ❌ Erro HTTP: {response.status_code}')
                
        except Exception as e:
            print(f'   ❌ Erro: {e}')
    
    print('\n=== FIM DO TESTE ===')

if __name__ == "__main__":
    test_authenticated_access()