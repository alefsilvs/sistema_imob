#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import PlanoComercial, Tenant
from saas.admin_utils import is_system_admin, get_admin_tenant_for_user, bypass_tenant_restrictions

def testar_sistema_admin():
    print("=== TESTE DO SISTEMA DE ACESSO GRATUITO PARA ADMINS ===")
    print()
    
    # Testar emails de admin
    emails_admin = ['alef63134@gmail.com', 'yousefhilal@hotmail.com']
    emails_normais = ['usuario@teste.com', 'cliente@exemplo.com']
    
    print("1. Testando verificação de emails de admin:")
    for email in emails_admin:
        resultado = is_system_admin(email)
        print(f"   {email}: {'✓ É ADMIN' if resultado else '✗ Não é admin'}")
    
    print("\n2. Testando emails de usuários normais:")
    for email in emails_normais:
        resultado = is_system_admin(email)
        print(f"   {email}: {'✓ É ADMIN' if resultado else '✗ Não é admin'}")
    
    # Testar com usuários existentes
    print("\n3. Testando usuários existentes no banco:")
    usuarios = User.objects.all()[:5]  # Pegar os primeiros 5 usuários
    
    if not usuarios.exists():
        print("   Nenhum usuário encontrado no banco de dados.")
    else:
        for user in usuarios:
            is_admin = is_system_admin(user)
            bypass = bypass_tenant_restrictions(user)
            admin_config = get_admin_tenant_for_user(user)
            
            print(f"   Usuário: {user.username} ({user.email})")
            print(f"     - É admin: {'✓ SIM' if is_admin else '✗ NÃO'}")
            print(f"     - Bypass restrições: {'✓ SIM' if bypass else '✗ NÃO'}")
            print(f"     - Config admin: {'✓ ATIVA' if admin_config else '✗ INATIVA'}")
            print()
    
    # Testar planos disponíveis
    print("4. Planos disponíveis no sistema:")
    planos = PlanoComercial.objects.filter(ativo=True)
    
    if not planos.exists():
        print("   Nenhum plano ativo encontrado.")
    else:
        for plano in planos:
            print(f"   - {plano.nome} ({plano.tipo}): R$ {plano.preco_mensal}/mês")
    
    # Testar tenants existentes
    print("\n5. Tenants existentes:")
    tenants = Tenant.objects.all()[:5]
    
    if not tenants.exists():
        print("   Nenhum tenant encontrado.")
    else:
        for tenant in tenants:
            admin_email = tenant.usuario_admin.email
            is_admin = is_system_admin(admin_email)
            print(f"   - {tenant.nome_empresa} ({tenant.subdominio})")
            print(f"     Admin: {admin_email} {'(ADMIN DO SISTEMA)' if is_admin else '(usuário normal)'}")
            print(f"     Status: {tenant.status}")
            print(f"     Plano: {tenant.plano.nome if tenant.plano else 'Sem plano'}")
            print()
    
    print("=== TESTE CONCLUÍDO ===")
    print("\nResumo das funcionalidades implementadas:")
    print("✓ Verificação de emails de admin (alef63134@gmail.com e yousefhilal@hotmail.com)")
    print("✓ Bypass de restrições de tenant para admins")
    print("✓ Configurações especiais de tenant para admins")
    print("✓ Middleware atualizado para detectar admins")
    print("✓ Views de planos e registro atualizadas")
    print("✓ Template de planos com mensagem especial para admins")
    print("\nOs administradores agora têm acesso gratuito a todos os recursos!")

if __name__ == '__main__':
    testar_sistema_admin()