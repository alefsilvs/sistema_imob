#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from core.forms import InquilinoForm
from core.models import Inquilino
from saas.models import Tenant
from saas.middleware import TenantMiddleware
from django.contrib.auth import signals
from security.signals import log_successful_login

def testar_cadastro_inquilino():
    print("=== TESTE DE CADASTRO DE INQUILINO ===")
    
    # Dados de teste
    dados_inquilino = {
        'nome': 'João da Silva Teste',
        'tipo': 'PF',
        'cpf_cnpj': '111.444.777-35',  # CPF válido para teste
        'rg_ie': '12.345.678-9',
        'data_nascimento': '1990-01-01',
        'profissao': 'Engenheiro',
        'telefone': '(11) 99999-9999',
        'email': 'joao.teste@email.com',
        'endereco': 'Rua Teste, 123',
        'cep': '01234-567',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'renda': '5000.00',
        'renda_comprovada': '4500.00',
        'observacoes': 'Teste de cadastro'
    }
    
    print("1. Testando validação do formulário...")
    form = InquilinoForm(data=dados_inquilino)
    
    if form.is_valid():
        print("✓ Formulário válido")
        
        # Verificar se já existe um inquilino com este CPF
        cpf_existente = Inquilino.objects.filter(cpf_cnpj=dados_inquilino['cpf_cnpj']).first()
        if cpf_existente:
            print(f"⚠ Já existe um inquilino com CPF {dados_inquilino['cpf_cnpj']}: {cpf_existente.nome}")
            print("Removendo inquilino existente para o teste...")
            cpf_existente.delete()
        
        print("2. Testando salvamento do inquilino...")
        try:
            # Obter tenant de teste
            tenant = Tenant.objects.first()
            if not tenant:
                print("❌ Nenhum tenant encontrado. Criando tenant de teste...")
                tenant = Tenant.objects.create(
                    nome='Teste',
                    dominio='teste.localhost',
                    ativo=True
                )
            
            inquilino = form.save(commit=False)
            inquilino.tenant = tenant
            inquilino.save()
            
            print(f"✓ Inquilino salvo com sucesso: {inquilino.nome} (ID: {inquilino.id})")
            
            # Verificar se foi realmente salvo
            inquilino_verificacao = Inquilino.objects.get(id=inquilino.id)
            print(f"✓ Verificação: Inquilino encontrado no banco: {inquilino_verificacao.nome}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar inquilino: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ Formulário inválido")
        for field, errors in form.errors.items():
            print(f"  - {field}: {errors}")
        return False

def testar_view_cadastro():
    print("\n=== TESTE DA VIEW DE CADASTRO ===")
    
    # Desabilitar signals temporariamente para evitar problemas com LoginAttempt
    from django.db import models
    from django.contrib.auth.signals import user_logged_in
    from security.signals import log_successful_login
    
    # Desconectar o signal temporariamente
    user_logged_in.disconnect(log_successful_login)
    
    try:
        # Desconectar o signal temporariamente
        signals.user_logged_in.disconnect(log_successful_login, sender=User)
        
        # Criar ou obter tenant de teste
        tenant, created = Tenant.objects.get_or_create(
            subdominio='teste',
            defaults={
                'nome_empresa': 'Empresa Teste',
                'status': 'ativo'
            }
        )
        
        # Criar cliente de teste
        client = Client()
        
        # Criar usuário de teste
        user = User.objects.create_user(username='teste', password='teste123')
        client.force_login(user)
        
        # Dados para POST
        dados_post = {
            'nome': 'Maria da Silva Teste',
            'tipo': 'PF',
            'cpf_cnpj': '222.333.444-87',  # CPF válido para teste
            'rg_ie': '98.765.432-1',
            'data_nascimento': '1985-05-15',
            'profissao': 'Professora',
            'telefone': '(11) 88888-8888',
            'email': 'maria.teste@email.com',
            'endereco': 'Rua Teste 2, 456',
            'cep': '09876-543',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'renda': '3000.00',
            'renda_comprovada': '2800.00',
            'observacoes': 'Teste via view'
        }
    # Teste GET na view
        print("1. Testando GET na view de cadastro...")
        response = client.get('/dashboard/inquilinos/cadastrar/', HTTP_HOST='teste.localhost')
        print(f"Status GET: {response.status_code}")
        
        # Debug: verificar se há mensagens de erro
        if hasattr(response, 'context') and response.context:
            messages = list(response.context.get('messages', []))
            if messages:
                print(f"Mensagens: {[str(m) for m in messages]}")
        
        print("2. Testando POST na view de cadastro...")
        
        # Verificar se já existe inquilino com mesmo CPF e remover
        cpf_existente = Inquilino.objects.filter(cpf_cnpj='222.333.444-87').first()
        if cpf_existente:
            cpf_existente.delete()
        
        response = client.post('/dashboard/inquilinos/cadastrar/', dados_post, follow=True, HTTP_HOST='teste.localhost')
        print(f"Status POST: {response.status_code}")
        
        # Debug: verificar mensagens após POST (agora com follow=True)
        if hasattr(response, 'context') and response.context:
            messages = list(response.context.get('messages', []))
            if messages:
                print(f"Mensagens POST: {[str(m) for m in messages]}")
        
        # Verificar mensagens na sessão
        from django.contrib.messages import get_messages
        from django.contrib.sessions.models import Session
        
        # Tentar obter mensagens da sessão
        try:
            session = client.session
            storage = get_messages(type('MockRequest', (), {'session': session})())
            messages_list = [str(message) for message in storage]
            if messages_list:
                print(f"Mensagens da sessão: {messages_list}")
        except Exception as e:
            print(f"Erro ao obter mensagens: {e}")
        
        if response.status_code == 200:
            print("✓ Página carregada após POST")
            # Verificar se há erros no formulário
            content = response.content.decode('utf-8')
            if 'errorlist' in content:
                print("❌ Erros encontrados no formulário:")
                # Extrair erros básicos
                import re
                errors = re.findall(r'<li[^>]*>(.*?)</li>', content)
                for error in errors[:5]:  # Mostrar apenas os primeiros 5 erros
                    print(f"  - {error}")
            
            # Verificar se foi salvo
            inquilino_salvo = Inquilino.objects.filter(cpf_cnpj=dados_post['cpf_cnpj']).first()
            if inquilino_salvo:
                print(f"✓ Inquilino encontrado no banco: {inquilino_salvo.nome}")
                return True
            else:
                print("❌ Inquilino não foi salvo no banco")
                return False
        else:
            print(f"❌ Erro na view. Status: {response.status_code}")
            if hasattr(response, 'content'):
                print("Conteúdo da resposta:")
                print(response.content.decode('utf-8')[:500])
            return False
    
    finally:
        # Reconectar o signal
        user_logged_in.connect(log_successful_login)

if __name__ == '__main__':
    print("Iniciando testes de cadastro de inquilino...\n")
    
    # Teste 1: Formulário direto
    sucesso_form = testar_cadastro_inquilino()
    
    # Teste 2: Via view
    sucesso_view = testar_view_cadastro()
    
    print(f"\n=== RESUMO DOS TESTES ===")
    print(f"Teste do formulário: {'✓ PASSOU' if sucesso_form else '❌ FALHOU'}")
    print(f"Teste da view: {'✓ PASSOU' if sucesso_view else '❌ FALHOU'}")
    
    if not sucesso_form or not sucesso_view:
        print("\n❌ Problemas identificados no cadastro de inquilinos!")
    else:
        print("\n✓ Todos os testes passaram!")