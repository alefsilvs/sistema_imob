#!/usr/bin/env python
"""
Script para testar o isolamento de dados entre tenants
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import Tenant, PlanoComercial
from core.models import Proprietario, Inquilino
from imoveis.models import Imovel
from contratos.models import Contrato
from django.utils import timezone
from datetime import timedelta

def criar_plano_teste():
    """Cria um plano de teste se não existir"""
    plano, created = PlanoComercial.objects.get_or_create(
        nome='Teste',
        defaults={
            'tipo': 'trial',
            'preco_mensal': 0.00,
            'max_imoveis': 100,
            'max_usuarios': 5,
            'is_trial': True
        }
    )
    return plano

def criar_tenant_teste(nome, subdominio):
    """Cria um tenant de teste"""
    # Criar usuário admin para o tenant
    user, created = User.objects.get_or_create(
        username=f'admin_{subdominio}',
        defaults={
            'email': f'admin@{subdominio}.com',
            'first_name': 'Admin',
            'last_name': nome
        }
    )
    
    if created:
        user.set_password('123456')
        user.save()
    
    # Criar tenant
    plano = criar_plano_teste()
    tenant, created = Tenant.objects.get_or_create(
        subdominio=subdominio,
        defaults={
            'nome_empresa': nome,
            'slug': subdominio,
            'usuario_admin': user,
            'plano': plano,
            'status': 'ativo',
            'trial_ate': timezone.now() + timedelta(days=30)
        }
    )
    
    return tenant

def criar_dados_teste(tenant, sufixo):
    """Cria dados de teste para um tenant"""
    print(f"Criando dados para tenant: {tenant.nome_empresa}")
    
    # Criar proprietário
    proprietario = Proprietario.objects.create(
        nome=f'Proprietário {sufixo}',
        cpf_cnpj=f'123.456.789-{sufixo:02d}',
        email=f'proprietario{sufixo}@teste.com',
        telefone=f'(11) 9999-{sufixo:04d}',
        tenant=tenant
    )
    
    # Criar inquilino
    inquilino = Inquilino.objects.create(
        nome=f'Inquilino {sufixo}',
        cpf_cnpj=f'987.654.321-{sufixo:02d}',
        email=f'inquilino{sufixo}@teste.com',
        telefone=f'(11) 8888-{sufixo:04d}',
        tenant=tenant
    )
    
    # Criar imóvel
    imovel = Imovel.objects.create(
        codigo=f'IM{sufixo:03d}',
        proprietario=proprietario,
        tipo='APARTAMENTO',
        finalidade='RESIDENCIAL',
        endereco=f'Rua Teste {sufixo}',
        numero=f'{sufixo}',
        bairro=f'Bairro {sufixo}',
        cidade='São Paulo',
        estado='SP',
        cep=f'{sufixo:05d}-000',
        valor_aluguel=1000.00 + (sufixo * 100),
        tenant=tenant
    )
    
    # Criar contrato
    contrato = Contrato.objects.create(
        numero=f'CT{sufixo:03d}',
        imovel=imovel,
        inquilino=inquilino,
        data_inicio=timezone.now().date(),
        data_fim=timezone.now().date() + timedelta(days=365),
        valor_aluguel=imovel.valor_aluguel,
        dia_vencimento=10,
        status='ATIVO',
        tenant=tenant
    )
    
    print(f"  - Proprietário: {proprietario.nome}")
    print(f"  - Inquilino: {inquilino.nome}")
    print(f"  - Imóvel: {imovel.codigo}")
    print(f"  - Contrato: {contrato.numero}")
    
    return proprietario, inquilino, imovel, contrato

def verificar_isolamento():
    """Verifica se os dados estão isolados por tenant"""
    print("\n=== VERIFICANDO ISOLAMENTO DE DADOS ===")
    
    tenants = Tenant.objects.filter(subdominio__in=['empresa1', 'empresa2'])
    
    for tenant in tenants:
        print(f"\nTenant: {tenant.nome_empresa} ({tenant.subdominio})")
        
        proprietarios = Proprietario.objects.filter(tenant=tenant)
        inquilinos = Inquilino.objects.filter(tenant=tenant)
        imoveis = Imovel.objects.filter(tenant=tenant)
        contratos = Contrato.objects.filter(tenant=tenant)
        
        print(f"  - Proprietários: {proprietarios.count()}")
        print(f"  - Inquilinos: {inquilinos.count()}")
        print(f"  - Imóveis: {imoveis.count()}")
        print(f"  - Contratos: {contratos.count()}")
        
        if proprietarios.exists():
            print(f"    Proprietário exemplo: {proprietarios.first().nome}")
        if inquilinos.exists():
            print(f"    Inquilino exemplo: {inquilinos.first().nome}")
        if imoveis.exists():
            print(f"    Imóvel exemplo: {imoveis.first().codigo}")
        if contratos.exists():
            print(f"    Contrato exemplo: {contratos.first().numero}")

def verificar_vazamento_dados():
    """Verifica se há vazamento de dados entre tenants"""
    print("\n=== VERIFICANDO VAZAMENTO DE DADOS ===")
    
    tenant1 = Tenant.objects.filter(subdominio='empresa1').first()
    tenant2 = Tenant.objects.filter(subdominio='empresa2').first()
    
    if not tenant1 or not tenant2:
        print("Tenants de teste não encontrados!")
        return
    
    # Verificar se dados do tenant1 aparecem no tenant2
    proprietarios_t1_em_t2 = Proprietario.objects.filter(tenant=tenant2, nome__contains='1')
    inquilinos_t1_em_t2 = Inquilino.objects.filter(tenant=tenant2, nome__contains='1')
    imoveis_t1_em_t2 = Imovel.objects.filter(tenant=tenant2, codigo__contains='1')
    contratos_t1_em_t2 = Contrato.objects.filter(tenant=tenant2, numero__contains='1')
    
    vazamentos = [
        ("Proprietários", proprietarios_t1_em_t2.count()),
        ("Inquilinos", inquilinos_t1_em_t2.count()),
        ("Imóveis", imoveis_t1_em_t2.count()),
        ("Contratos", contratos_t1_em_t2.count())
    ]
    
    vazamento_detectado = False
    for tipo, count in vazamentos:
        if count > 0:
            print(f"⚠️  VAZAMENTO DETECTADO: {count} {tipo} do Tenant 1 encontrados no Tenant 2")
            vazamento_detectado = True
    
    if not vazamento_detectado:
        print("✅ Nenhum vazamento de dados detectado!")

def main():
    print("=== TESTE DE ISOLAMENTO DE TENANTS ===")
    
    # Criar tenants de teste
    print("\nCriando tenants de teste...")
    tenant1 = criar_tenant_teste('Empresa 1 Ltda', 'empresa1')
    tenant2 = criar_tenant_teste('Empresa 2 Ltda', 'empresa2')
    
    # Criar dados de teste para cada tenant
    print("\nCriando dados de teste...")
    criar_dados_teste(tenant1, 1)
    criar_dados_teste(tenant2, 2)
    
    # Verificar isolamento
    verificar_isolamento()
    
    # Verificar vazamentos
    verificar_vazamento_dados()
    
    print("\n=== TESTE CONCLUÍDO ===")
    print("\nPara testar via navegador:")
    print(f"- Tenant 1: http://empresa1.localhost:8000")
    print(f"- Tenant 2: http://empresa2.localhost:8000")
    print("\nCredenciais:")
    print("- Usuário: admin_empresa1 / admin_empresa2")
    print("- Senha: 123456")

if __name__ == '__main__':
    main()