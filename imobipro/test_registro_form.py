#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from saas.models import Tenant

def test_registro_form():
    print("=== TESTE DO FORMULÁRIO DE REGISTRO ===")
    
    # Criar cliente de teste
    client = Client()
    
    # Testar GET da página de registro
    print("\n1. Testando GET /saas/registro/")
    response = client.get('/saas/registro/')
    print(f"   Status: {response.status_code}")
    print(f"   CSRF Token presente: {'csrfmiddlewaretoken' in str(response.content)}")
    
    if response.status_code != 200:
        print(f"   ERRO: Página não carregou corretamente")
        return
    
    # Obter CSRF token
    csrf_token = None
    if 'csrftoken' in client.cookies:
        csrf_token = client.cookies['csrftoken'].value
        print(f"   CSRF Token obtido: {csrf_token[:20]}...")
    
    # Testar POST com dados válidos
    print("\n2. Testando POST com dados válidos")
    
    # Verificar se email já existe
    test_email = 'teste_registro@exemplo.com'
    if User.objects.filter(email=test_email).exists():
        User.objects.filter(email=test_email).delete()
        print(f"   Email {test_email} removido para teste")
    
    data = {
        'nome_empresa': 'Empresa Teste',
        'nome_responsavel': 'João da Silva',
        'email': test_email,
        'telefone': '11999999999',
        'senha': 'senha123456',
        'confirmar_senha': 'senha123456',
        'aceitar_termos': True
    }
    
    if csrf_token:
        data['csrfmiddlewaretoken'] = csrf_token
    
    response = client.post('/saas/registro/', data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"   ✅ Redirecionamento para: {response.url}")
        
        # Verificar se usuário foi criado
        user_exists = User.objects.filter(email=test_email).exists()
        print(f"   Usuário criado: {user_exists}")
        
        # Verificar se tenant foi criado
        if user_exists:
            user = User.objects.get(email=test_email)
            tenant_exists = Tenant.objects.filter(usuario_admin=user).exists()
            print(f"   Tenant criado: {tenant_exists}")
            
    elif response.status_code == 200:
        print(f"   ⚠️  Formulário retornou para a mesma página (possível erro de validação)")
        content_str = response.content.decode('utf-8')
        if 'error' in content_str.lower() or 'erro' in content_str.lower():
            print(f"   Possível erro no formulário detectado")
    else:
        print(f"   ❌ Erro inesperado: {response.status_code}")
        print(f"   Conteúdo: {response.content[:200]}")
    
    # Testar POST sem CSRF token
    print("\n3. Testando POST sem CSRF token")
    data_no_csrf = {
        'nome_empresa': 'Empresa Teste 2',
        'nome_responsavel': 'Maria Silva',
        'email': 'teste2@exemplo.com',
        'telefone': '11888888888',
        'senha': 'senha123456',
        'confirmar_senha': 'senha123456',
        'aceitar_termos': True
    }
    
    response = client.post('/saas/registro/', data_no_csrf)
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print(f"   ✅ CSRF protection funcionando (403 Forbidden)")
    else:
        print(f"   ⚠️  CSRF protection pode não estar funcionando")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_registro_form()