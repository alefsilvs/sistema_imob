#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import PlanoComercial, Tenant
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

def test_registro_tenant():
    try:
        print("Testando registro de tenant...")
        
        # Dados de teste
        dados_empresa = {
            'nome_empresa': 'Empresa Teste LTDA',
            'email': 'admin@empresateste.com',
            'senha': 'senha123',
            'nome_responsavel': 'João Silva'
        }
        
        # Criar usuário
        print("1. Criando usuário...")
        user = User.objects.create_user(
            username=dados_empresa['email'],
            email=dados_empresa['email'],
            password=dados_empresa['senha'],
            first_name=dados_empresa['nome_responsavel'].split()[0],
            last_name=' '.join(dados_empresa['nome_responsavel'].split()[1:]) if len(dados_empresa['nome_responsavel'].split()) > 1 else ''
        )
        print(f"   ✅ Usuário criado: {user.username}")
        
        # Obter plano trial
        print("2. Obtendo plano trial...")
        plano = PlanoComercial.objects.filter(tipo='trial', ativo=True).first()
        if not plano:
            plano = PlanoComercial.objects.filter(tipo='basico', ativo=True).first()
        print(f"   ✅ Plano selecionado: {plano.nome}")
        
        # Criar slug único
        print("3. Criando slug único...")
        base_slug = slugify(dados_empresa['nome_empresa'])
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        print(f"   ✅ Slug criado: {slug}")
        
        # Criar subdomínio único
        print("4. Criando subdomínio único...")
        base_subdominio = slugify(dados_empresa['nome_empresa']).replace('-', '')
        subdominio = base_subdominio
        counter = 1
        while Tenant.objects.filter(subdominio=subdominio).exists():
            subdominio = f"{base_subdominio}{counter}"
            counter += 1
        print(f"   ✅ Subdomínio criado: {subdominio}")
        
        # Criar tenant
        print("5. Criando tenant...")
        tenant = Tenant.objects.create(
            nome_empresa=dados_empresa['nome_empresa'],
            slug=slug,
            subdominio=subdominio,
            usuario_admin=user,
            plano=plano,
            status='trial',
            trial_ate=timezone.now() + timedelta(days=30)
        )
        print(f"   ✅ Tenant criado: {tenant.nome_empresa}")
        print(f"   ID: {tenant.id}")
        print(f"   Slug: {tenant.slug}")
        print(f"   Subdomínio: {tenant.subdominio}")
        print(f"   Status: {tenant.status}")
        print(f"   Trial até: {tenant.trial_ate}")
        
        # Verificar se o tenant foi salvo corretamente
        tenant_verificacao = Tenant.objects.get(id=tenant.id)
        print(f"   ✅ Tenant verificado no banco: {tenant_verificacao.nome_empresa}")
        
        print("\n🎉 Registro de tenant concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao registrar tenant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_registro_tenant()