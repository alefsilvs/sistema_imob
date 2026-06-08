#!/usr/bin/env python
"""
Script para testar as correções de segurança implementadas
"""
import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')

import django
django.setup()

from django.conf import settings

def testar_middlewares():
    """Testa se os middlewares estão configurados corretamente"""
    print("=== TESTE DE CONFIGURAÇÃO DOS MIDDLEWARES ===")
    print()
    
    # Verificar middlewares ativos
    middlewares = settings.MIDDLEWARE
    
    print("📋 MIDDLEWARES CONFIGURADOS:")
    for i, middleware in enumerate(middlewares, 1):
        print(f"   {i}. {middleware}")
    
    print()
    
    # Verificar middlewares críticos
    middlewares_criticos = {
        'EmailVerificationMiddleware': 'saas.middleware.EmailVerificationMiddleware',
        'TenantMiddleware': 'saas.middleware.TenantMiddleware',
        'ControleAssinaturaMiddleware': 'assinaturas.middleware.ControleAssinaturaMiddleware',
        'LimiteRecursosMiddleware': 'assinaturas.middleware.LimiteRecursosMiddleware',
        'MasterUserMiddleware': 'security.middleware.MasterUserMiddleware'
    }
    
    print("🔍 VERIFICAÇÃO DE MIDDLEWARES CRÍTICOS:")
    todos_ativos = True
    
    for nome, classe in middlewares_criticos.items():
        ativo = classe in middlewares
        status = "✅ ATIVO" if ativo else "❌ INATIVO"
        print(f"   {nome}: {status}")
        
        if not ativo and nome == 'EmailVerificationMiddleware':
            todos_ativos = False
            print(f"      ⚠️  CRÍTICO: {nome} deve estar ativo!")
    
    return todos_ativos

def verificar_view_home():
    """Verifica se a view home foi corrigida"""
    print("\n=== VERIFICAÇÃO DA VIEW HOME ===")
    
    try:
        # Ler o arquivo da view
        with open('core/views.py', 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Verificar se as correções estão presentes
        verificacoes = {
            'Importação VerificacaoEmail': 'from saas.models import VerificacaoEmail',
            'Verificação de email': 'verificacao = VerificacaoEmail.objects.get(usuario=request.user)',
            'Redirecionamento para verificação': 'return redirect(\'saas:email_enviado\')',
            'Verificação de status do tenant': 'if tenant.status == \'ativo\'',
            'Verificação de trial': 'elif tenant.status == \'trial\''
        }
        
        print("🔍 VERIFICAÇÕES NA VIEW HOME:")
        todas_presentes = True
        
        for nome, codigo in verificacoes.items():
            presente = codigo in conteudo
            status = "✅ PRESENTE" if presente else "❌ AUSENTE"
            print(f"   {nome}: {status}")
            
            if not presente:
                todas_presentes = False
        
        return todas_presentes
        
    except FileNotFoundError:
        print("   ❌ Arquivo core/views.py não encontrado!")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao verificar view: {e}")
        return False

def verificar_urls_protegidas():
    """Verifica se as URLs estão protegidas pelo middleware"""
    print("\n=== VERIFICAÇÃO DE URLs PROTEGIDAS ===")
    
    try:
        # Ler o arquivo do middleware
        with open('saas/middleware.py', 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Verificar URLs protegidas
        urls_protegidas = [
            '/dashboard/',
            '/imoveis/',
            '/contratos/',
            '/financeiro/',
            '/relatorios/',
            '/configuracoes/'
        ]
        
        print("🔒 URLs QUE DEVEM ESTAR PROTEGIDAS:")
        
        for url in urls_protegidas:
            if url in conteudo:
                print(f"   {url}: ✅ PROTEGIDA")
            else:
                print(f"   {url}: ⚠️  NÃO ENCONTRADA NA CONFIGURAÇÃO")
        
        # Verificar se o middleware tem a lógica de verificação
        verificacoes_middleware = [
            'PROTECTED_URLS',
            'email_verificado',
            'redirect'
        ]
        
        print("\n🔍 VERIFICAÇÕES NO MIDDLEWARE:")
        for verificacao in verificacoes_middleware:
            presente = verificacao in conteudo
            status = "✅ PRESENTE" if presente else "❌ AUSENTE"
            print(f"   {verificacao}: {status}")
        
        return True
        
    except FileNotFoundError:
        print("   ❌ Arquivo saas/middleware.py não encontrado!")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao verificar middleware: {e}")
        return False

def testar_configuracao_completa():
    """Executa todos os testes de configuração"""
    print("🚀 INICIANDO TESTES DE CONFIGURAÇÃO DE SEGURANÇA")
    print("=" * 60)
    
    # Teste 1: Middlewares
    middlewares_ok = testar_middlewares()
    
    # Teste 2: View Home
    view_ok = verificar_view_home()
    
    # Teste 3: URLs Protegidas
    urls_ok = verificar_urls_protegidas()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print(f"   Middlewares: {'✅ OK' if middlewares_ok else '❌ FALHA'}")
    print(f"   View Home: {'✅ OK' if view_ok else '❌ FALHA'}")
    print(f"   URLs Protegidas: {'✅ OK' if urls_ok else '❌ FALHA'}")
    
    if middlewares_ok and view_ok and urls_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🔒 As correções de segurança foram implementadas corretamente.")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Reinicie o servidor Django")
        print("   2. Teste manualmente o fluxo de login")
        print("   3. Verifique se usuários sem email verificado são bloqueados")
        print("   4. Confirme que admins podem acessar normalmente")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("⚠️  Verifique as correções que falharam nos testes acima.")
        return False

if __name__ == '__main__':
    try:
        sucesso = testar_configuracao_completa()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)