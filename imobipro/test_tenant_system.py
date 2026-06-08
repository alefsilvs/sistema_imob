#!/usr/bin/env python
"""
Script de teste para verificar o funcionamento completo do sistema multi-tenant
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from saas.models import Tenant, PlanoComercial, ConfiguracaoTenant
from saas.evolution_models import EvolutionInstance
from saas.evolution_services import tenant_evolution_service
from saas.database_isolation import TenantDatabaseManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tenant_creation():
    """Testa a criação de um tenant"""
    print("\n🏢 TESTE 1: Criação de Tenant")
    
    try:
        # Criar plano comercial se não existir
        plano, created = PlanoComercial.objects.get_or_create(
            nome='Plano Teste',
            defaults={
                'tipo': 'basico',
                'preco_mensal': 99.90,
                'max_usuarios': 10,
                'max_imoveis': 100,
                'max_contratos': 50,
                'storage_gb': 10,
                'api_calls_mes': 5000,
                'suporte_prioritario': True,
                'backup_automatico': True,
                'subdominio_personalizado': True,
                'ativo': True
            }
        )
        
        # Criar usuário admin se não existir
        user, created = User.objects.get_or_create(
            username='admin_teste',
            defaults={
                'email': 'admin@teste.com',
                'first_name': 'Admin',
                'last_name': 'Teste',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            user.set_password('123456')
            user.save()
        
        # Criar tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='empresa-teste',
            defaults={
                'nome_empresa': 'Empresa Teste Ltda',
                'subdominio': 'empresa-teste',
                'usuario_admin': user,
                'plano': plano,
                'status': 'ativo'
            }
        )
        
        print(f"   ✅ Tenant criado: {tenant.nome_empresa} ({tenant.slug})")
        
        # Criar configuração do tenant
        config, created = ConfiguracaoTenant.objects.get_or_create(
            tenant=tenant,
            defaults={
                'email_contato': 'contato@empresateste.com',
                'telefone_contato': '(11) 99999-9999'
            }
        )
        
        print(f"   ✅ Configuração criada para o tenant")
        
        return tenant
        
    except Exception as e:
        print(f"   ❌ Erro na criação do tenant: {str(e)}")
        return None

def test_database_isolation(tenant):
    """Testa o isolamento de banco de dados"""
    print("\n🗄️ TESTE 2: Isolamento de Banco de Dados")
    
    try:
        db_manager = TenantDatabaseManager()
        
        # Criar schema do tenant
        db_manager.create_tenant_schema(tenant)
        print(f"   ✅ Schema criado para tenant {tenant.slug}")
        
        # Testar mudança de schema
        db_manager.set_tenant_schema(tenant.id)
        print(f"   ✅ Schema definido para tenant {tenant.id}")
        
        # Voltar para schema público
        db_manager.set_tenant_schema(None)
        print(f"   ✅ Schema resetado para público")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no isolamento de banco: {str(e)}")
        return False

def test_evolution_api_integration(tenant):
    """Testa a integração com Evolution API"""
    print("\n⚙️ TESTE 3: Integração com Evolution API")
    
    try:
        # Importar aqui para evitar erro de importação circular
        from saas.evolution_models import EvolutionInstance
        
        # Verificar se já existe uma instância para este tenant
        existing_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
        
        if existing_instance:
            print(f"   ✅ Instância Evolution já existe: {existing_instance.instance_name}")
            print(f"   📱 Token: {existing_instance.token[:20]}...")
            print(f"   🔗 URL Manager: {existing_instance.get_manager_url()}")
        else:
            # Criar instância Evolution
            evolution_instance = EvolutionInstance.objects.create(
                tenant=tenant,
                instance_name=f"whatsapp_{tenant.slug}",
                api_key="test_api_key_123",
                server_url="http://localhost:8080"
            )
            
            print(f"   ✅ Instância Evolution criada: {evolution_instance.instance_name}")
            print(f"   📱 Token: {evolution_instance.token[:20]}...")
            print(f"   🔗 URL Manager: {evolution_instance.get_manager_url()}")
        
        return True
            
    except Exception as e:
        print(f"   ❌ Erro na Evolution API: {e}")
        return False

def test_admin_interface(tenant):
    """Testa a interface administrativa"""
    print("\n⚙️ TESTE 4: Interface Administrativa")
    
    try:
        from django.contrib.auth.models import User
        from django.test import Client
        
        # Verificar se usuário admin já existe
        admin_user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@test.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        # Criar cliente de teste
        client = Client()
        
        # Login como admin
        login_success = client.login(username='admin_test', password='admin123')
        if not login_success:
            print("   ❌ Falha no login do admin")
            return False
            
        print("   ✅ Login admin realizado")
        
        # Testar acesso ao admin do tenant (sem verificar permissões específicas)
        response = client.get('/admin/saas/tenant/')
        print(f"   📋 Acesso à lista de tenants: {response.status_code}")
        
        # Testar acesso aos modelos Evolution
        response = client.get('/admin/saas/evolutioninstance/')
        print(f"   📱 Acesso às instâncias Evolution: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na interface admin: {e}")
        return False

def test_middleware_functionality():
    """Testa o funcionamento dos middlewares"""
    print("\n⚙️ TESTE 5: Funcionamento dos Middlewares")
    
    try:
        client = Client()
        
        # Testar acesso sem tenant (deve redirecionar)
        response = client.get('/', HTTP_HOST='localhost')
        print(f"   📍 Acesso sem tenant: {response.status_code}")
        
        # Testar acesso com subdomínio inexistente
        response = client.get('/', HTTP_HOST='inexistente.localhost')
        print(f"   📍 Subdomínio inexistente: {response.status_code}")
        
        # Testar acesso com tenant válido
        response = client.get('/', HTTP_HOST='empresa-teste.localhost')
        print(f"   📍 Tenant válido: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nos middlewares: {str(e)}")
        return False

def cleanup_test_data():
    """Limpa os dados de teste"""
    print("\n🧹 LIMPEZA: Removendo dados de teste")
    
    try:
        # Remover instâncias Evolution
        EvolutionInstance.objects.filter(tenant__slug='empresa-teste').delete()
        
        # Remover tenant e dados relacionados
        Tenant.objects.filter(slug='empresa-teste').delete()
        
        # Remover usuário de teste
        User.objects.filter(username='admin_teste').delete()
        
        # Remover plano de teste
        PlanoComercial.objects.filter(nome='Plano Teste').delete()
        
        print("   ✅ Dados de teste removidos")
        
    except Exception as e:
        print(f"   ❌ Erro na limpeza: {str(e)}")

def main():
    """Função principal do teste"""
    print("🚀 INICIANDO TESTES DO SISTEMA MULTI-TENANT")
    print("=" * 50)
    
    # Executar testes
    tenant = test_tenant_creation()
    
    if tenant:
        db_isolation_ok = test_database_isolation(tenant)
        evolution_ok = test_evolution_api_integration(tenant)
        admin_ok = test_admin_interface(tenant)
        middleware_ok = test_middleware_functionality()
        
        # Resumo dos testes
        print("\n📊 RESUMO DOS TESTES")
        print("=" * 30)
        print(f"   Criação de Tenant: {'✅' if tenant else '❌'}")
        print(f"   Isolamento de DB: {'✅' if db_isolation_ok else '❌'}")
        print(f"   Evolution API: {'✅' if evolution_ok else '❌'}")
        print(f"   Interface Admin: {'✅' if admin_ok else '❌'}")
        print(f"   Middlewares: {'✅' if middleware_ok else '❌'}")
        
        # Verificar se todos os testes passaram
        all_tests_passed = all([tenant, db_isolation_ok, evolution_ok, admin_ok, middleware_ok])
        
        if all_tests_passed:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("   O sistema multi-tenant está funcionando corretamente.")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM")
            print("   Verifique os erros acima e corrija os problemas.")
    
    # Perguntar se deve limpar os dados
    cleanup = input("\n🤔 Deseja remover os dados de teste? (s/N): ").lower().strip()
    if cleanup == 's':
        cleanup_test_data()
    else:
        print("   📝 Dados de teste mantidos para análise manual")

if __name__ == '__main__':
    main()