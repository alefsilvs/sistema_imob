#!/usr/bin/env python
"""
Script para fazer login programaticamente e testar elementos header e div
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from saas.models import Tenant, VerificacaoEmail
from core.models_perfil import PerfilUsuario, UsuarioPerfil

def criar_usuario_teste():
    """Criar usuário de teste se não existir"""
    username = 'teste_html'
    email = 'teste@html.com'
    password = 'senha123'
    
    try:
        user = User.objects.get(username=username)
        print(f'✓ Usuário {username} já existe')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Teste',
            last_name='HTML'
        )
        print(f'✓ Usuário {username} criado')
    
    # Verificar/criar plano comercial
    from saas.models import PlanoComercial
    try:
        plano = PlanoComercial.objects.first()
        if not plano:
            plano = PlanoComercial.objects.create(
                nome='Plano Teste',
                preco_mensal=50.00,
                max_usuarios=10,
                max_imoveis=100,
                ativo=True
            )
            print(f'✓ Plano comercial criado: {plano.nome}')
        else:
            print(f'✓ Usando plano existente: {plano.nome}')
    except Exception as e:
        print(f'❌ Erro ao criar/buscar plano: {e}')
        return None, None, None
    
    # Verificar/criar tenant
    try:
        tenant = Tenant.objects.get(nome_empresa='Teste HTML')
        print(f'✓ Tenant já existe: {tenant.nome_empresa}')
    except Tenant.DoesNotExist:
        try:
            tenant = Tenant.objects.create(
                nome_empresa='Teste HTML',
                slug='teste-html',
                subdominio='teste-html',
                usuario_admin=user,
                plano=plano,
                status='ativo'
            )
            print(f'✓ Tenant criado: {tenant.nome_empresa}')
        except Exception as e:
            print(f'❌ Erro ao criar tenant: {e}')
            return None, None, None
    
    # Verificar/criar perfil
    try:
        perfil = PerfilUsuario.objects.get(nome='Administrador')
    except PerfilUsuario.DoesNotExist:
        perfil = PerfilUsuario.objects.create(
            nome='Administrador',
            descricao='Perfil de administrador para testes',
            ativo=True
        )
        print(f'✓ Perfil criado: {perfil.nome}')
    
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
    
    return user, tenant, password

def testar_com_django_client():
    """Testar usando Django Test Client"""
    print("\n=== TESTE COM DJANGO CLIENT ===")
    
    user, tenant, password = criar_usuario_teste()
    
    # Criar cliente Django
    client = Client()
    
    # Fazer login
    login_success = client.login(username=user.username, password=password)
    
    if not login_success:
        print('❌ Falha no login com Django Client')
        return
    
    print(f'✓ Login realizado com sucesso')
    
    # Configurar sessão com tenant_id
    session = client.session
    session['tenant_id'] = tenant.id
    session.save()
    
    # Testar URLs
    urls_para_testar = [
        ('/', 'Página inicial'),
        ('/dashboard/', 'Dashboard'),
        ('/core/dashboard/', 'Core Dashboard'),
    ]
    
    for url, nome in urls_para_testar:
        print(f"\n--- Testando {nome} ({url}) ---")
        try:
            response = client.get(url)
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                
                # Verificar título
                title = soup.find('title')
                if title:
                    print(f'Título: {title.get_text().strip()}')
                
                # Contar elementos
                headers = soup.find_all('header')
                asides = soup.find_all('aside')
                navs = soup.find_all('nav')
                
                print(f'Elementos <header>: {len(headers)}')
                print(f'Elementos <aside>: {len(asides)}')
                print(f'Elementos <nav>: {len(navs)}')
                
                # Verificar divs específicas
                sidebar_divs = soup.find_all('div', class_=lambda x: x and 'sidebar' in x)
                main_divs = soup.find_all('div', class_=lambda x: x and 'main' in x)
                content_divs = soup.find_all('div', class_=lambda x: x and 'content' in x)
                
                print(f'Divs com classe "sidebar": {len(sidebar_divs)}')
                print(f'Divs com classe "main": {len(main_divs)}')
                print(f'Divs com classe "content": {len(content_divs)}')
                
                # Mostrar detalhes dos elementos encontrados
                if headers:
                    for i, header in enumerate(headers):
                        classes = header.get('class', [])
                        print(f'  Header {i+1}: classes={classes}')
                
                if asides:
                    for i, aside in enumerate(asides):
                        classes = aside.get('class', [])
                        print(f'  Aside {i+1}: classes={classes}')
                
                # Verificar se está usando base.html
                if 'sidebar' in content.lower() or 'navbar' in content.lower():
                    print('✓ Parece estar usando template base.html')
                else:
                    print('❌ Não parece estar usando template base.html')
                    
                # Mostrar primeiros 500 caracteres do body
                body = soup.find('body')
                if body:
                    body_text = str(body)[:500]
                    print(f'Início do body: {body_text}...')
                
            elif response.status_code == 302:
                print(f'Redirecionamento para: {response.get("Location", "N/A")}')
            else:
                print(f'❌ Status inesperado: {response.status_code}')
                
        except Exception as e:
            print(f'❌ Erro ao testar {url}: {e}')

if __name__ == '__main__':
    testar_com_django_client()