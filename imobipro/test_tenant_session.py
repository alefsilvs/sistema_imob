#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from saas.models import Tenant

def configure_tenant_session():
    """Configura tenant_id na sessão para o usuário teste_header"""
    
    print("=== CONFIGURAÇÃO DE TENANT NA SESSÃO ===")
    
    try:
        user = User.objects.get(username='teste_header')
        print(f"Usuário encontrado: {user.username}")
        
        # Buscar ou criar um tenant para o usuário
        tenant = Tenant.objects.filter(usuario_admin=user).first()
        
        if not tenant:
            print("❌ Usuário não possui tenant associado")
            print("🔧 Criando tenant para o usuário...")
            
            # Buscar um plano para associar ao tenant
            from saas.models import PlanoComercial
            plano = PlanoComercial.objects.filter(is_trial=True).first()
            if not plano:
                plano = PlanoComercial.objects.first()
            
            tenant = Tenant.objects.create(
                usuario_admin=user,
                nome_empresa="Empresa Teste Header",
                slug="teste-header",
                subdominio="teste-header",
                plano=plano
            )
            print(f"   ✅ Tenant criado: {tenant.nome_empresa} (ID: {tenant.id})")
        else:
            print(f"✅ Tenant encontrado: {tenant.nome_empresa} (ID: {tenant.id})")
        
        # Testar login com configuração de sessão
        client = Client()
        
        # Login
        login_data = {'username': 'teste_header', 'password': '123456'}
        login_resp = client.post('/accounts/login/', login_data)
        print(f'Login status: {login_resp.status_code}')
        
        # Configurar tenant_id na sessão manualmente
        session = client.session
        session['tenant_id'] = tenant.id
        session.save()
        print(f'✅ tenant_id configurado na sessão: {tenant.id}')
        
        # Testar acesso ao dashboard
        resp = client.get('/dashboard/')
        print(f'Dashboard status: {resp.status_code}')
        
        if resp.status_code == 200:
            content = resp.content.decode('utf-8')
            header_count = content.count('<header')
            div_count = content.count('<div')
            print(f'✅ Headers encontrados: {header_count}')
            print(f'✅ Divs encontrados: {div_count}')
            
            # Salvar amostra do HTML
            with open('dashboard_sample.html', 'w', encoding='utf-8') as f:
                f.write(content[:5000])  # Primeiros 5000 caracteres
            print('📄 Amostra do HTML salva em dashboard_sample.html')
            
            # Verificar elementos header específicos
            if '<header' in content:
                print('\n📋 Análise de elementos <header>:')
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '<header' in line:
                        print(f'   Linha {i+1}: {line.strip()[:150]}...')
                        
        elif resp.status_code == 302:
            redirect_url = resp.get('Location', 'Desconhecido')
            print(f'Dashboard ainda redirecionou para: {redirect_url}')
        
    except User.DoesNotExist:
        print("❌ Usuário teste_header não encontrado")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n=== FIM DA CONFIGURAÇÃO ===")

if __name__ == '__main__':
    configure_tenant_session()