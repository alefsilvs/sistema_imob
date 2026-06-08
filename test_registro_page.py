#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
import traceback

def test_registro_page():
    print("=== TESTE DA PÁGINA DE REGISTRO ===")
    
    # Teste 1: Verificar se o template existe
    print("\n1. Verificando template...")
    try:
        template = get_template('saas/registro.html')
        print("✓ Template 'saas/registro.html' encontrado")
    except TemplateDoesNotExist as e:
        print(f"✗ Template não encontrado: {e}")
        return
    except Exception as e:
        print(f"✗ Erro ao carregar template: {e}")
        return
    
    # Teste 2: Verificar URL
    print("\n2. Verificando URL...")
    try:
        url = reverse('saas:registro')
        print(f"✓ URL de registro: {url}")
    except Exception as e:
        print(f"✗ Erro na URL: {e}")
        return
    
    # Teste 3: Testar requisição GET
    print("\n3. Testando requisição GET...")
    client = Client()
    try:
        response = client.get(url)
        print(f"✓ Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Página carregada com sucesso")
            print(f"✓ Content-Type: {response.get('Content-Type', 'N/A')}")
            
            # Verificar se há conteúdo HTML
            content = response.content.decode('utf-8')
            if '<html' in content.lower():
                print("✓ Conteúdo HTML válido encontrado")
            else:
                print("⚠ Conteúdo não parece ser HTML válido")
                
        elif response.status_code == 404:
            print("✗ Página não encontrada (404)")
        elif response.status_code == 500:
            print("✗ Erro interno do servidor (500)")
        else:
            print(f"⚠ Status code inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Erro na requisição: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return
    
    # Teste 4: Verificar dependências do template
    print("\n4. Verificando dependências...")
    try:
        from crispy_forms.templatetags.crispy_forms_tags import as_crispy_field
        print("✓ crispy_forms disponível")
    except ImportError as e:
        print(f"✗ crispy_forms não disponível: {e}")
    
    try:
        from saas.forms import RegistroEmpresaForm
        form = RegistroEmpresaForm()
        print("✓ RegistroEmpresaForm disponível")
        print(f"✓ Campos do formulário: {list(form.fields.keys())}")
    except Exception as e:
        print(f"✗ Erro no formulário: {e}")
    
    # Teste 5: Verificar contexto da view
    print("\n5. Verificando contexto da view...")
    try:
        from saas.views import RegistroView
        view = RegistroView()
        context = view.get_context_data()
        print(f"✓ Contexto base: {list(context.keys())}")
    except Exception as e:
        print(f"✗ Erro no contexto: {e}")
    
    print("\n=== FIM DO TESTE ===")

if __name__ == '__main__':
    test_registro_page()