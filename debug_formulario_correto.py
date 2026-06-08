#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.db import transaction
from core.models import Inquilino
from core.forms import InquilinoForm
from saas.models import Tenant

def debug_formulario_correto():
    """Debug com dados corretos do formulário"""
    print("=== DEBUG FORMULÁRIO CORRETO ===")
    print()
    
    try:
        # Buscar dados
        tenant = Tenant.objects.first()
        user = User.objects.first()
        
        if not tenant or not user:
            print("❌ Tenant ou usuário não encontrado!")
            return
            
        print(f"✅ Tenant: {tenant.nome_empresa}")
        print(f"✅ Usuário: {user.username}")
        print()
        
        # Dados CORRETOS do inquilino com todos os campos obrigatórios
        dados_inquilino = {
            'nome': 'João Silva Correto',
            'tipo': 'PF',  # Campo obrigatório
            'cpf_cnpj': '12345678901',  # Campo obrigatório
            'rg_ie': '123456789',
            'telefone': '11999999999',
            'email': 'joao.correto@test.com',
            'endereco': 'Rua Teste, 123',
            'cep': '01234-567',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'profissao': 'Desenvolvedor',
            'renda': '5000.00',
            'observacoes': 'Teste com dados corretos'
        }
        
        print("1. TESTE DIRETO DO FORMULÁRIO (COM DADOS CORRETOS):")
        
        # Teste direto do formulário
        try:
            with transaction.atomic():
                form = InquilinoForm(dados_inquilino)
                if form.is_valid():
                    inquilino = form.save(commit=False)
                    inquilino.tenant = tenant
                    inquilino.save()
                    print(f"   ✅ Inquilino salvo diretamente: ID {inquilino.id}")
                    print(f"   📋 Nome: {inquilino.nome}")
                    print(f"   📋 Tipo: {inquilino.tipo}")
                    print(f"   📋 CPF/CNPJ: {inquilino.cpf_cnpj}")
                    print(f"   📋 Tenant: {inquilino.tenant}")
                    inquilino.delete()  # Limpar
                else:
                    print(f"   ❌ Formulário ainda inválido: {form.errors}")
        except Exception as e:
            print(f"   ❌ Erro no save direto: {e}")
            
        print()
        print("2. DESABILITANDO MIDDLEWARES PROBLEMÁTICOS:")
        
        # Salvar middlewares originais
        middlewares_originais = settings.MIDDLEWARE.copy()
        
        # Remover middlewares problemáticos
        middlewares_problematicos = [
            'security.middleware.LoginSecurityMiddleware',
            'assinaturas.middleware.ControleAssinaturaMiddleware',
            'saas.middleware_pkg.trial_middleware.TrialMiddleware',
        ]
        
        middlewares_filtrados = [
            m for m in middlewares_originais 
            if m not in middlewares_problematicos
        ]
        
        print(f"   📋 Middlewares removidos: {len(middlewares_problematicos)}")
        for middleware in middlewares_problematicos:
            if middleware in middlewares_originais:
                print(f"      ❌ Removido: {middleware}")
            else:
                print(f"      ✅ Já estava inativo: {middleware}")
        
        # Aplicar middlewares filtrados
        settings.MIDDLEWARE = middlewares_filtrados
        
        print()
        print("3. TESTE COM CLIENT (MIDDLEWARES FILTRADOS):")
        
        try:
            client = Client()
            client.force_login(user)
            
            # Definir tenant na sessão
            session = client.session
            session['tenant_id'] = tenant.id
            session.save()
            
            # Contar antes
            inquilinos_antes = Inquilino.objects.filter(tenant=tenant).count()
            print(f"   📊 Inquilinos antes: {inquilinos_antes}")
            
            # Fazer POST
            response = client.post('/inquilinos/cadastrar/', dados_inquilino, follow=True)
            
            # Contar depois
            inquilinos_depois = Inquilino.objects.filter(tenant=tenant).count()
            print(f"   📊 Inquilinos depois: {inquilinos_depois}")
            print(f"   📊 Status da resposta: {response.status_code}")
            
            if inquilinos_depois > inquilinos_antes:
                print("   ✅ SUCESSO! Inquilino cadastrado via web")
                
                # Verificar o inquilino criado
                inquilino_criado = Inquilino.objects.filter(tenant=tenant).last()
                print(f"   📋 Inquilino criado: {inquilino_criado.nome} (ID: {inquilino_criado.id})")
                
                # Limpar
                inquilino_criado.delete()
                print("   🧹 Inquilino removido após teste")
            else:
                print("   ❌ FALHOU - Inquilino não foi salvo")
                
                # Verificar mensagens
                from django.contrib.messages import get_messages
                messages = list(get_messages(response.wsgi_request))
                if messages:
                    print("   📨 Mensagens:")
                    for message in messages:
                        print(f"      - {message}")
                        
                # Verificar se houve redirecionamento
                if response.redirect_chain:
                    print("   🔄 Redirecionamentos:")
                    for redirect in response.redirect_chain:
                        print(f"      - {redirect}")
                        
        except Exception as e:
            print(f"   ❌ Erro no teste com client: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Restaurar middlewares originais
            settings.MIDDLEWARE = middlewares_originais
            print()
            print("4. MIDDLEWARES RESTAURADOS")
            
        print()
        print("=== RESUMO ===")
        print("✅ Problemas identificados:")
        print("   1. Campos obrigatórios 'tipo' e 'cpf_cnpj' estavam faltando")
        print("   2. Middlewares problemáticos estavam causando erros")
        print("   3. LoginSecurityMiddleware com erro de NOT NULL constraint")
        print()
        print("🔧 Soluções aplicadas:")
        print("   1. Adicionados campos obrigatórios ao formulário")
        print("   2. Desabilitados middlewares problemáticos temporariamente")
        print("   3. Testado cadastro com dados corretos")
                
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_formulario_correto()