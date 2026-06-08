#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages import get_messages
from django.db import transaction
from core.views import cadastrar_inquilino
from core.forms import InquilinoForm
from core.models import Inquilino
from saas.models import Tenant

def debug_save():
    print("=== DEBUG ESPECÍFICO DO SAVE ===")
    
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
    print(f"Tenant: {tenant.nome_empresa} (ID: {tenant.id})")
    
    # Criar usuário de teste
    user, created = User.objects.get_or_create(
        username='teste_debug',
        defaults={'email': 'teste@debug.com'}
    )
    print(f"Usuário: {user.username}")
    
    # Dados de teste
    dados_post = {
        'nome': 'Debug Save Inquilino',
        'tipo': 'PF',
        'cpf_cnpj': '111.444.777-35',  # CPF válido
        'rg_ie': '12.345.678-9',
        'data_nascimento': '1990-01-01',
        'telefone': '(11) 99999-9999',
        'email': 'debug@save.com',
        'endereco': 'Rua Debug Save, 123',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cep': '01234-567',
        'observacoes': 'Teste de debug save'
    }
    
    # Limpar inquilinos existentes
    Inquilino.objects.filter(cpf_cnpj='111.444.777-35').delete()
    print("Inquilinos existentes removidos")
    
    print("\n1. Testando save direto do modelo...")
    try:
        inquilino_direto = Inquilino(
            nome='Debug Direto',
            tipo='PF',
            cpf_cnpj='111.444.777-35',
            rg_ie='12.345.678-9',
            data_nascimento='1990-01-01',
            telefone='(11) 99999-9999',
            email='debug@direto.com',
            endereco='Rua Debug Direto, 123',
            cidade='São Paulo',
            estado='SP',
            cep='01234-567',
            tenant=tenant
        )
        inquilino_direto.save()
        print(f"✓ Save direto funcionou: {inquilino_direto.nome} (ID: {inquilino_direto.id})")
        
        # Verificar se está no banco
        verificacao = Inquilino.objects.filter(id=inquilino_direto.id).first()
        if verificacao:
            print(f"✓ Confirmado no banco: {verificacao.nome}")
        else:
            print("❌ Não encontrado no banco após save direto")
            
        # Limpar
        inquilino_direto.delete()
        
    except Exception as e:
        print(f"❌ Erro no save direto: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testando save via formulário...")
    try:
        form = InquilinoForm(dados_post)
        if form.is_valid():
            print("✓ Formulário válido")
            
            # Interceptar o save
            inquilino = form.save(commit=False)
            print(f"✓ form.save(commit=False) executado: {inquilino.nome}")
            
            inquilino.tenant = tenant
            print(f"✓ Tenant definido: {inquilino.tenant}")
            
            # Verificar se há transação ativa
            print(f"Transação ativa: {transaction.get_connection().in_atomic_block}")
            
            inquilino.save()
            print(f"✓ inquilino.save() executado: ID {inquilino.id}")
            
            # Forçar commit
            transaction.commit()
            print("✓ transaction.commit() executado")
            
            # Verificar se está no banco
            verificacao = Inquilino.objects.filter(id=inquilino.id).first()
            if verificacao:
                print(f"✓ Confirmado no banco: {verificacao.nome}")
            else:
                print("❌ Não encontrado no banco após save via formulário")
                
        else:
            print(f"❌ Formulário inválido: {form.errors}")
            
    except Exception as e:
        print(f"❌ Erro no save via formulário: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n3. Testando a view completa com debug...")
    try:
        # Limpar novamente
        Inquilino.objects.filter(cpf_cnpj='111.444.777-35').delete()
        
        # Criar request POST
        request = factory.post('/dashboard/inquilinos/cadastrar/', dados_post)
        request.user = user
        request.tenant = tenant
        
        # Configurar sessão e mensagens
        request.session = SessionStore()
        request.session.create()
        request._messages = FallbackStorage(request)
        
        # Interceptar a view
        print("Chamando cadastrar_inquilino...")
        
        # Monkey patch para interceptar o save
        original_save = Inquilino.save
        
        def debug_save_method(self, *args, **kwargs):
            print(f"🔍 SAVE INTERCEPTADO: {self.nome}")
            print(f"   - Tenant: {self.tenant}")
            print(f"   - CPF: {self.cpf_cnpj}")
            print(f"   - Args: {args}")
            print(f"   - Kwargs: {kwargs}")
            
            result = original_save(self, *args, **kwargs)
            print(f"   - ID após save: {self.id}")
            
            # Verificar imediatamente se está no banco
            verificacao = Inquilino.objects.filter(id=self.id).first()
            print(f"   - Verificação imediata: {'✓' if verificacao else '❌'}")
            
            return result
        
        Inquilino.save = debug_save_method
        
        try:
            # Verificar antes da view
            antes_view = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').count()
            print(f"Inquilinos antes da view: {antes_view}")
            
            response = cadastrar_inquilino(request)
            print(f"Status da resposta: {response.status_code}")
            
            # Verificar imediatamente após a view
            apos_view = Inquilino.objects.filter(cpf_cnpj='111.444.777-35').count()
            print(f"Inquilinos imediatamente após view: {apos_view}")
            
            # Capturar mensagens
            messages = list(get_messages(request))
            if messages:
                print(f"Mensagens: {[str(m) for m in messages]}")
                
            # Verificar estado da transação
            print(f"Transação ativa após view: {transaction.get_connection().in_atomic_block}")
            
            # Forçar commit se necessário
            if transaction.get_connection().in_atomic_block:
                print("Forçando commit da transação...")
                transaction.commit()
                
        finally:
            # Restaurar método original
            Inquilino.save = original_save
        
        # Verificar final
        inquilinos_finais = Inquilino.objects.filter(cpf_cnpj='111.444.777-35')
        print(f"Inquilinos finais no banco: {inquilinos_finais.count()}")
        for inq in inquilinos_finais:
            print(f"  - {inq.nome} (ID: {inq.id}, Tenant: {inq.tenant})")
            
        # Debug adicional: verificar se há algum middleware interferindo
        print("\n4. Verificando configurações de transação...")
        from django.conf import settings
        print(f"ATOMIC_REQUESTS: {getattr(settings, 'ATOMIC_REQUESTS', False)}")
        print(f"AUTOCOMMIT: {transaction.get_autocommit()}")
        
        # Verificar se há algum middleware que pode estar interferindo
        print(f"MIDDLEWARE: {settings.MIDDLEWARE}")
            
    except Exception as e:
        print(f"❌ Erro na view: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_save()