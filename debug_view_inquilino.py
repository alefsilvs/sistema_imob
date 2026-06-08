#!/usr/bin/env python
import os
import sys
import django

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages import get_messages
from core.views import cadastrar_inquilino
from core.forms import InquilinoForm
from saas.models import Tenant

def debug_view():
    print("=== DEBUG DA VIEW CADASTRAR_INQUILINO ===")
    
    # Criar factory para requests
    factory = RequestFactory()
    
    # Criar tenant de teste
    tenant, created = Tenant.objects.get_or_create(
        subdominio='teste',
        defaults={
            'nome_empresa': 'Empresa Teste',
            'status': 'ativo'
        }
    )
    print(f"Tenant criado/encontrado: {tenant.nome_empresa} (ID: {tenant.id})")
    
    # Criar usuário de teste
    user, created = User.objects.get_or_create(
        username='teste_debug',
        defaults={'email': 'teste@debug.com'}
    )
    print(f"Usuário criado/encontrado: {user.username}")
    
    # Dados de teste
    dados_post = {
        'nome': 'Debug Inquilino',
        'tipo': 'PF',
        'cpf_cnpj': '111.444.777-35',  # CPF válido
        'rg_ie': '12.345.678-9',
        'data_nascimento': '1990-01-01',
        'telefone': '(11) 99999-9999',
        'email': 'debug@inquilino.com',
        'endereco': 'Rua Debug, 123',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cep': '01234-567',
        'observacoes': 'Teste de debug'
    }
    
    # Criar request POST
    request = factory.post('/dashboard/inquilinos/cadastrar/', dados_post)
    request.user = user
    request.tenant = tenant  # Simular middleware
    
    # Configurar sessão e mensagens
    request.session = SessionStore()
    request.session.create()
    request._messages = FallbackStorage(request)
    
    print("\n1. Testando formulário diretamente...")
    form = InquilinoForm(dados_post)
    print(f"Formulário válido: {form.is_valid()}")
    if not form.is_valid():
        print(f"Erros: {form.errors}")
        return
    
    print("\n2. Testando salvamento com tenant...")
    inquilino = form.save(commit=False)
    inquilino.tenant = tenant
    inquilino.save()
    print(f"Inquilino salvo: {inquilino.nome} (ID: {inquilino.id})")
    
    print("\n3. Testando a view completa...")
    
    # Limpar inquilinos existentes com esse CPF
    from core.models import Inquilino
    inquilinos_antes = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').count()
    print(f"Inquilinos com CPF antes do delete: {inquilinos_antes}")
    
    deleted_count, _ = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').delete()
    print(f"Inquilinos deletados: {deleted_count}")
    
    inquilinos_depois = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').count()
    print(f"Inquilinos com CPF após delete: {inquilinos_depois}")
    
    try:
        # Verificar se request tem tenant
        print(f"Request tem tenant: {hasattr(request, 'tenant')}")
        print(f"Tenant do request: {getattr(request, 'tenant', None)}")
        
        response = cadastrar_inquilino(request)
        print(f"Status da resposta: {response.status_code}")
        
        # Capturar mensagens
        messages = list(get_messages(request))
        if messages:
            print(f"Mensagens: {[str(m) for m in messages]}")
        
        # Forçar commit da transação
        from django.db import transaction
        transaction.commit()
        
        # Verificar se foi salvo (buscar o mais recente)
        inquilino_salvo = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').order_by('-id').first()
        if inquilino_salvo:
            print(f"✓ Inquilino encontrado no banco: {inquilino_salvo.nome}")
            print(f"  Tenant: {inquilino_salvo.tenant}")
            print(f"  ID: {inquilino_salvo.id}")
        else:
            print("❌ Inquilino não foi salvo pela view")
            
        # Verificar todos os inquilinos com esse CPF
        todos_inquilinos = Inquilino.objects.filter(cpf_cnpj='111.444.777-35')
        print(f"Total de inquilinos com esse CPF: {todos_inquilinos.count()}")
        for inq in todos_inquilinos:
            print(f"  - ID: {inq.id}, Nome: {inq.nome}, Tenant: {inq.tenant}")
            
            # Debug adicional: verificar todos os inquilinos
            todos_inquilinos = Inquilino.objects.all()
            print(f"Total de inquilinos no banco: {todos_inquilinos.count()}")
            for inq in todos_inquilinos.order_by('-id')[:3]:
                print(f"  - {inq.nome} (CPF: {inq.cpf_cnpj}, Tenant: {inq.tenant})")
            
    except Exception as e:
        print(f"❌ Erro na view: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_view()