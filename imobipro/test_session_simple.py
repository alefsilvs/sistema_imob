from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import requests

print('🔍 VERIFICANDO SESSÕES ATIVAS')
print('=' * 50)

# Verificar sessões ativas
sessions = Session.objects.filter(expire_date__gt=timezone.now())
print(f'📊 Total de sessões ativas: {sessions.count()}')

valid_session = None
for session in sessions:
    data = session.get_decoded()
    user_id = data.get('_auth_user_id')
    tenant_id = data.get('tenant_id')
    if user_id and tenant_id:
        try:
            user = User.objects.get(id=user_id)
            print(f'✓ Sessão válida: {session.session_key[:20]}...')
            print(f'  👤 Usuário: {user.username} (ID: {user_id})')
            print(f'  🏢 Tenant ID: {tenant_id}')
            valid_session = session.session_key
            break
        except User.DoesNotExist:
            continue

if valid_session:
    print(f'\n🌐 TESTANDO REQUISIÇÃO HTTP:')
    cookie = {settings.SESSION_COOKIE_NAME: valid_session}
    print(f'   Cookie name: {settings.SESSION_COOKIE_NAME}')
    print(f'   Session key: {valid_session[:20]}...')
    
    try:
        response = requests.get(
            'http://127.0.0.1:8000/imoveis/bancas/mapa/',
            cookies=cookie,
            timeout=10
        )
        print(f'   📊 Status: {response.status_code}')
        
        if response.status_code == 200:
            if 'Mapa das Bancas da Feira' in response.text:
                print('   ✅ SUCESSO! Página do mapa carregada!')
                with open('temp_mapa_sessao_valida.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print('   💾 Conteúdo salvo em temp_mapa_sessao_valida.html')
            else:
                print('   ❌ Redirecionado para login')
        elif response.status_code == 302:
            location = response.headers.get('Location', 'N/A')
            print(f'   🔄 Redirecionamento para: {location}')
        else:
            print(f'   ❌ Erro: {response.status_code}')
            
    except Exception as e:
        print(f'   ❌ Erro na requisição: {e}')
else:
    print('❌ Nenhuma sessão válida encontrada')

print('\n✅ TESTE CONCLUÍDO')