#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from saas.models import Tenant
import django.utils.timezone

def corrigir_sessao_tenant():
    print("=== CORRIGINDO SESSÃO DO TENANT ===")
    
    # Encontrar usuário e seu tenant
    user = User.objects.first()
    print(f"Usuário: {user.username}")
    
    try:
        tenant = Tenant.objects.get(usuario_admin=user)
        print(f"Tenant do usuário: ID {tenant.id}")
    except Tenant.DoesNotExist:
        print("❌ Usuário não tem tenant!")
        return False
    
    # Encontrar sessões ativas do usuário
    sessions_ativas = Session.objects.filter(expire_date__gt=django.utils.timezone.now())
    print(f"Sessões ativas: {sessions_ativas.count()}")
    
    sessoes_corrigidas = 0
    
    for session in sessions_ativas:
        data = session.get_decoded()
        
        # Debug: mostrar dados da sessão
        auth_user_id = data.get('_auth_user_id')
        current_tenant_id = data.get('tenant_id')
        print(f"Sessão: auth_user_id={auth_user_id}, tenant_id={current_tenant_id}")
        
        # Verificar se é sessão do usuário (comparar tanto string quanto int)
        is_user_session = False
        if auth_user_id:
            try:
                is_user_session = (auth_user_id == str(user.id)) or (int(auth_user_id) == user.id)
            except (ValueError, TypeError):
                is_user_session = (auth_user_id == str(user.id))
        
        if is_user_session:
            print(f"Encontrada sessão do usuário {user.username} (auth_user_id: {auth_user_id})")
            
            # Verificar se já tem tenant_id
            if current_tenant_id == tenant.id:
                print(f"  ✅ Sessão já tem tenant_id correto: {tenant.id}")
            else:
                print(f"  🔧 Adicionando tenant_id à sessão: {tenant.id} (atual: {current_tenant_id})")
                
                # Adicionar tenant_id à sessão
                data['tenant_id'] = tenant.id
                
                # Salvar sessão atualizada
                session.session_data = session.encode(data)
                session.save()
                
                sessoes_corrigidas += 1
                print(f"  ✅ Sessão corrigida!")
        else:
            print(f"  Sessão não é do usuário {user.username}")
    
    print(f"\n📊 RESULTADO:")
    print(f"  Sessões corrigidas: {sessoes_corrigidas}")
    
    if sessoes_corrigidas > 0:
        print("✅ Problema corrigido! Agora o mapa deve funcionar.")
        print("💡 Recarregue a página do mapa para ver as bancas.")
    else:
        print("ℹ️ Nenhuma sessão precisou ser corrigida.")
    
    return True

if __name__ == "__main__":
    corrigir_sessao_tenant()