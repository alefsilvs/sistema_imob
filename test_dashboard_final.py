#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from saas.models import Tenant

def test_dashboard_final():
    """Testa o dashboard seguindo todos os redirecionamentos até a página final"""
    
    print("=== TESTE FINAL DO DASHBOARD ===")
    
    try:
        user = User.objects.get(username='teste_header')
        tenant = Tenant.objects.filter(usuario_admin=user).first()
        
        if not tenant:
            print("❌ Tenant não encontrado")
            return
        
        print(f"✅ Usuário: {user.username}")
        print(f"✅ Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
        
        client = Client()
        
        # Login
        login_data = {'username': 'teste_header', 'password': '123456'}
        login_resp = client.post('/accounts/login/', login_data)
        print(f'Login status: {login_resp.status_code}')
        
        # Configurar tenant_id na sessão
        session = client.session
        session['tenant_id'] = tenant.id
        session.save()
        print(f'✅ tenant_id configurado na sessão: {tenant.id}')
        
        # Seguir redirecionamentos até a página final
        current_url = '/dashboard/'
        redirect_count = 0
        max_redirects = 10
        
        while redirect_count < max_redirects:
            print(f'\n🔄 Tentativa {redirect_count + 1}: Acessando {current_url}')
            resp = client.get(current_url)
            print(f'   Status: {resp.status_code}')
            
            if resp.status_code == 200:
                print('✅ Página carregada com sucesso!')
                
                content = resp.content.decode('utf-8')
                header_count = content.count('<header')
                div_count = content.count('<div')
                
                print(f'📊 Análise da página final:')
                print(f'   Headers encontrados: {header_count}')
                print(f'   Divs encontrados: {div_count}')
                print(f'   Tamanho do HTML: {len(content)} caracteres')
                
                # Verificar elementos específicos
                elements_found = []
                if 'class="header"' in content:
                    elements_found.append('class="header"')
                if 'id="header"' in content:
                    elements_found.append('id="header"')
                if '<header' in content:
                    elements_found.append('<header> tag')
                if 'navbar' in content.lower():
                    elements_found.append('navbar')
                
                if elements_found:
                    print(f'✅ Elementos encontrados: {", ".join(elements_found)}')
                else:
                    print('⚠️  Nenhum elemento header específico encontrado')
                
                # Salvar HTML completo para análise
                with open('dashboard_final.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print('📄 HTML completo salvo em dashboard_final.html')
                
                # Mostrar primeiras linhas com <header
                if '<header' in content:
                    print('\n📋 Elementos <header> encontrados:')
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if '<header' in line:
                            print(f'   Linha {i+1}: {line.strip()[:200]}...')
                
                # Verificar se há erros no HTML
                error_indicators = ['error', 'exception', 'traceback', 'django.template']
                errors_found = []
                for indicator in error_indicators:
                    if indicator in content.lower():
                        errors_found.append(indicator)
                
                if errors_found:
                    print(f'⚠️  Possíveis erros encontrados: {", ".join(errors_found)}')
                else:
                    print('✅ Sem erros aparentes no HTML')
                
                break
                
            elif resp.status_code == 302:
                redirect_url = resp.get('Location', '')
                print(f'   Redirecionamento para: {redirect_url}')
                current_url = redirect_url
                redirect_count += 1
            else:
                print(f'❌ Status inesperado: {resp.status_code}')
                break
        
        if redirect_count >= max_redirects:
            print(f'❌ Muitos redirecionamentos ({max_redirects}). Possível loop.')
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n=== FIM DO TESTE ===")

if __name__ == '__main__':
    test_dashboard_final()