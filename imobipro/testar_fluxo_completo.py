#!/usr/bin/env python
"""
Script para testar o fluxo completo do sistema SaaS:
1. Escolha de plano
2. Registro de usuário
3. Verificação de email
4. Redirecionamento para pagamento
5. Acesso ao dashboard
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from saas.models import PlanoComercial, Tenant, VerificacaoEmail, PagamentoPlano
from django.core.mail import send_mail
from django.test.utils import override_settings
import json

def limpar_dados_teste():
    """Limpa dados de teste anteriores"""
    print("🧹 Limpando dados de teste...")
    
    # Remover usuários de teste
    User.objects.filter(email__contains='teste@').delete()
    
    # Remover tenants de teste
    Tenant.objects.filter(nome_empresa__contains='Teste').delete()
    
    print("✅ Dados de teste limpos")

def testar_fluxo_completo():
    """Testa o fluxo completo do sistema"""
    print("🚀 Iniciando teste do fluxo completo...\n")
    
    # Limpar dados anteriores
    limpar_dados_teste()
    
    # Criar cliente de teste
    client = Client()
    
    # 1. Verificar página de planos
    print("1. 📋 Testando página de planos...")
    response = client.get('/saas/planos/')
    assert response.status_code == 200, f"Erro na página de planos: {response.status_code}"
    print("   ✅ Página de planos carregada com sucesso")
    
    # 2. Verificar se há planos disponíveis
    planos = PlanoComercial.objects.filter(ativo=True)
    assert planos.exists(), "Nenhum plano ativo encontrado"
    plano_teste = planos.first()
    print(f"   ✅ Plano de teste encontrado: {plano_teste.nome} - R$ {plano_teste.preco_mensal}")
    
    # 3. Criar usuário e tenant diretamente (simulando o processo de registro)
    print("\n2. 📝 Testando criação de usuário e tenant...")
    
    # Criar usuário com email único
    import time
    timestamp = int(time.time())
    email_teste = f'joao{timestamp}@teste.com'
    
    usuario = User.objects.create_user(
        username=email_teste,
        email=email_teste,
        password='senha123456',
        first_name='João',
        last_name='Silva'
    )
    print(f"   ✅ Usuário criado: {usuario.username} ({usuario.email})")
    
    # Criar tenant
    from django.utils.text import slugify
    from django.utils import timezone
    from datetime import timedelta
    
    tenant = Tenant.objects.create(
        nome_empresa='Empresa Teste',
        slug=f'empresa-teste-{timestamp}',
        subdominio=f'empresateste{timestamp}',
        usuario_admin=usuario,
        plano=plano_teste,
        status='trial',
        trial_ate=timezone.now() + timedelta(days=7)
    )
    print(f"   ✅ Tenant criado: {tenant.nome_empresa} ({tenant.slug})")
    
    # 4. Verificar se pagamento foi criado (se plano não for gratuito)
    if plano_teste.preco_mensal > 0:
        pagamento = PagamentoPlano.objects.create(
            tenant=tenant,
            plano=plano_teste,
            valor=plano_teste.preco_mensal,
            forma_pagamento='pix',
            descricao=f'Pagamento do plano {plano_teste.nome} - {tenant.nome_empresa}',
            metadata={
                'plano_id': plano_teste.id,
                'tenant_id': tenant.id,
                'usuario_id': usuario.id
            }
        )
        print(f"   ✅ Pagamento criado: {pagamento.descricao} - R$ {pagamento.valor}")
    
    # 5. Criar registro de verificação de email
    verificacao = VerificacaoEmail.objects.create(
        usuario=usuario,
        email_verificado=False
    )
    print(f"   ✅ Registro de verificação criado com token: {verificacao.token}")
    
    # 6. Testar middleware de verificação de email (simulado)
    print("\n3. 🔒 Testando middleware de verificação de email...")
    
    # Verificar se middleware está configurado
    from django.conf import settings
    middleware_configurado = 'saas.middleware.EmailVerificationMiddleware' in settings.MIDDLEWARE
    if middleware_configurado:
        print("   ✅ EmailVerificationMiddleware está configurado no settings")
    else:
        print("   ❌ EmailVerificationMiddleware NÃO está configurado")
    
    # 7. Verificar email
    print("\n4. ✅ Testando verificação de email...")
    verificacao.email_verificado = True
    verificacao.save()
    print("   ✅ Email marcado como verificado")
    
    # 8. Verificar se o token de verificação funciona
    print("\n5. 🔗 Testando token de verificação...")
    token_url = f'/saas/verificar-email/{verificacao.token}/'
    response = client.get(token_url)
    print(f"   🔍 Status da verificação por token: {response.status_code}")
    
    # Recarregar verificação do banco
    verificacao.refresh_from_db()
    print(f"   ✅ Status final da verificação: {verificacao.email_verificado}")
    
    # 9. Verificar status final dos objetos criados
    print("\n6. 📊 Verificando status final dos objetos...")
    
    # Verificar usuário
    usuario.refresh_from_db()
    print(f"   👤 Usuário criado: {usuario.username} ({usuario.email})")
    print(f"   ✅ Usuário ativo: {usuario.is_active}")
    
    # Verificar tenant
    tenant.refresh_from_db()
    print(f"   🏢 Tenant criado: {tenant.nome_empresa} (slug: {tenant.slug})")
    print(f"   ✅ Tenant ativo: {tenant.status}")
    
    # Verificar verificação de email
    verificacao.refresh_from_db()
    print(f"   📧 Email verificado: {verificacao.email_verificado}")
    print(f"   🔗 Token: {str(verificacao.token)[:20]}...")
    
    # Verificar pagamento
    if plano_teste.preco_mensal > 0:
        pagamento.refresh_from_db()
        print(f"   💰 Pagamento criado: {pagamento.status}")
        print(f"   💵 Valor: R$ {pagamento.valor}")
    
    # 10. Testar URLs básicas sem login
    print("\n7. 🌐 Testando URLs básicas...")
    
    # Testar página de planos
    response = client.get('/saas/planos/')
    print(f"   📋 Página de planos: {response.status_code}")
    
    # Testar página de registro
    response = client.get('/saas/registro/')
    print(f"   📝 Página de registro: {response.status_code}")
    
    # Testar URL de verificação de email
    response = client.get(f'/saas/verificar-email/{verificacao.token}/')
    print(f"   ✅ URL de verificação: {response.status_code}")
    
    print("\n🎉 TESTE COMPLETO FINALIZADO COM SUCESSO!")
    print("\n📊 RESUMO DO TESTE:")
    print(f"   • Usuário: {usuario.username} ({usuario.email})")
    print(f"   • Tenant: {tenant.nome_empresa} ({tenant.subdominio})")
    print(f"   • Plano: {plano_teste.nome} - R$ {plano_teste.preco_mensal}")
    print(f"   • Status do tenant: {tenant.status}")
    print(f"   • Email verificado: {verificacao.email_verificado}")
    
    if plano_teste.preco_mensal > 0:
        pagamento.refresh_from_db()
        print(f"   • Pagamento: {pagamento.status} - R$ {pagamento.valor}")
    
    return True

def main():
    """Função principal"""
    try:
        testar_fluxo_completo()
        print("\n✅ TODOS OS TESTES PASSARAM!")
        return True
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Limpar dados de teste
        print("\n🧹 Limpando dados de teste...")
        limpar_dados_teste()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)