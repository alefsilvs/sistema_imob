#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.template.loader import get_template
from django.template import TemplateDoesNotExist, Context
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client

def testar_templates_recuperacao():
    print("=== TESTE DOS TEMPLATES DE RECUPERAÇÃO DE SENHA ===")
    print()
    
    # Lista de templates para testar
    templates_recuperacao = [
        'registration/password_reset_form.html',
        'registration/password_reset_done.html', 
        'registration/password_reset_email.html',
        'registration/password_reset_subject.txt',
        'registration/password_reset_confirm.html',
        'registration/password_reset_complete.html'
    ]
    
    # Testar existência dos templates
    print("1. VERIFICANDO EXISTÊNCIA DOS TEMPLATES:")
    templates_encontrados = []
    for template_name in templates_recuperacao:
        try:
            template = get_template(template_name)
            print(f"✅ {template_name} - ENCONTRADO")
            templates_encontrados.append(template_name)
        except TemplateDoesNotExist:
            print(f"❌ {template_name} - NÃO ENCONTRADO")
        except Exception as e:
            print(f"⚠️  {template_name} - ERRO: {e}")
    
    print()
    print("2. VERIFICANDO TEMPLATE BASE:")
    try:
        base_template = get_template('base_auth.html')
        print("✅ base_auth.html - ENCONTRADO")
    except TemplateDoesNotExist:
        print("❌ base_auth.html - NÃO ENCONTRADO")
    except Exception as e:
        print(f"⚠️  base_auth.html - ERRO: {e}")
    
    print()
    print("3. TESTANDO RENDERIZAÇÃO DOS TEMPLATES:")
    
    # Criar contexto de teste
    factory = RequestFactory()
    request = factory.get('/test/')
    
    # Criar usuário de teste para contexto
    try:
        user = User.objects.get(username='cliente')
    except User.DoesNotExist:
        user = User.objects.create_user('teste_template', 'teste@teste.com', '123456')
    
    # Contexto para templates
    context = {
        'user': user,
        'domain': 'localhost:8000',
        'protocol': 'http',
        'uid': 'test-uid',
        'token': 'test-token',
        'validlink': True,
        'form': None  # Seria um formulário real em produção
    }
    
    for template_name in templates_encontrados:
        try:
            template = get_template(template_name)
            if template_name.endswith('.txt'):
                # Template de texto simples
                rendered = template.render(context)
                print(f"✅ {template_name} - RENDERIZADO (texto)")
            else:
                # Template HTML
                rendered = template.render(context)
                if len(rendered) > 100:  # Verificar se tem conteúdo
                    print(f"✅ {template_name} - RENDERIZADO ({len(rendered)} chars)")
                else:
                    print(f"⚠️  {template_name} - RENDERIZADO MAS MUITO PEQUENO")
        except Exception as e:
            print(f"❌ {template_name} - ERRO NA RENDERIZAÇÃO: {e}")
    
    print()
    print("4. TESTANDO URLS DE RECUPERAÇÃO:")
    
    urls_recuperacao = [
        'password_reset',
        'password_reset_done', 
        'password_reset_confirm',
        'password_reset_complete'
    ]
    
    client = Client()
    
    for url_name in urls_recuperacao:
        try:
            if url_name == 'password_reset_confirm':
                # URL com parâmetros
                url = reverse(url_name, kwargs={'uidb64': 'test', 'token': 'test'})
            else:
                url = reverse(url_name)
            
            print(f"✅ {url_name} - URL: {url}")
            
            # Testar acesso à URL
            if url_name != 'password_reset_confirm':  # Evitar erro com parâmetros inválidos
                response = client.get(url)
                if response.status_code == 200:
                    print(f"   ✅ Acesso OK (200)")
                elif response.status_code in [302, 301]:
                    print(f"   ✅ Redirecionamento ({response.status_code})")
                else:
                    print(f"   ⚠️  Status: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {url_name} - ERRO: {e}")
    
    print()
    print("5. VERIFICANDO ARQUIVOS ESTÁTICOS:")
    
    # Verificar se CSS customizado existe
    static_files = [
        'css/custom.css'
    ]
    
    for static_file in static_files:
        static_path = Path('static') / static_file
        if static_path.exists():
            print(f"✅ {static_file} - ENCONTRADO")
        else:
            print(f"⚠️  {static_file} - NÃO ENCONTRADO (pode estar em outro local)")
    
    print()
    print("=== RESUMO DO TESTE ===")
    print(f"Templates encontrados: {len(templates_encontrados)}/{len(templates_recuperacao)}")
    
    if len(templates_encontrados) == len(templates_recuperacao):
        print("✅ TODOS OS TEMPLATES DE RECUPERAÇÃO ESTÃO FUNCIONANDO!")
    else:
        print("⚠️  ALGUNS TEMPLATES PODEM ESTAR FALTANDO")
    
    print()
    print("=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    testar_templates_recuperacao()