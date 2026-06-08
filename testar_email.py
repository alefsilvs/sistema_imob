#!/usr/bin/env python
"""
Script para testar configuração de email SMTP
"""

import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

def testar_configuracao_email():
    """
    Testa se as configurações de email estão funcionando
    """
    print("=" * 60)
    print("TESTE DE CONFIGURAÇÃO DE EMAIL")
    print("=" * 60)
    
    # Verificar configurações
    print("\n1. VERIFICANDO CONFIGURAÇÕES:")
    print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NÃO CONFIGURADO'}")
    print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Verificar se as credenciais estão configuradas
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERRO: Credenciais de email não configuradas!")
        print("\nPara configurar:")
        print("1. Edite o arquivo .env")
        print("2. Configure EMAIL_HOST_USER, EMAIL_HOST_PASSWORD e DEFAULT_FROM_EMAIL")
        print("3. Para Gmail, use uma senha de app (não sua senha normal)")
        return False
    
    if settings.EMAIL_HOST_USER == 'seu-email@gmail.com':
        print("\n⚠️  AVISO: Você ainda está usando o email de exemplo!")
        print("   Substitua 'seu-email@gmail.com' pelo seu email real no arquivo .env")
        return False
    
    # Solicitar email de destino para teste
    print("\n2. TESTE DE ENVIO:")
    email_destino = input("Digite um email para teste (ou pressione Enter para usar o email configurado): ").strip()
    
    if not email_destino:
        email_destino = settings.EMAIL_HOST_USER
    
    print(f"   Enviando email de teste para: {email_destino}")
    
    try:
        # Tentar enviar email de teste
        assunto = "[Sistema Imobiliário] Teste de Configuração de Email"
        mensagem = f"""
Olá!

Este é um email de teste do Sistema Imobiliário.

Se você recebeu esta mensagem, significa que a configuração de email está funcionando corretamente!

Detalhes do teste:
- Data/Hora: {timezone.now().strftime('%d/%m/%Y às %H:%M:%S')}
- Servidor SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- Email de origem: {settings.DEFAULT_FROM_EMAIL}

Atenciosamente,
Sistema Imobiliário
"""
        
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_destino],
            fail_silently=False
        )
        
        print("\n✅ EMAIL ENVIADO COM SUCESSO!")
        print(f"   Verifique a caixa de entrada de: {email_destino}")
        print("   (Não esqueça de verificar a pasta de spam também)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO AO ENVIAR EMAIL: {str(e)}")
        
        # Diagnóstico do erro
        error_str = str(e).lower()
        
        if '530' in error_str and 'authentication' in error_str:
            print("\n🔍 DIAGNÓSTICO:")
            print("   Erro de autenticação SMTP")
            print("\n💡 SOLUÇÕES:")
            print("   1. Para Gmail:")
            print("      - Ative a autenticação de 2 fatores")
            print("      - Gere uma 'Senha de App' específica")
            print("      - Use a senha de app no EMAIL_HOST_PASSWORD")
            print("   2. Para outros provedores:")
            print("      - Verifique se as credenciais estão corretas")
            print("      - Confirme se o SMTP está habilitado")
            
        elif 'connection' in error_str or 'timeout' in error_str:
            print("\n🔍 DIAGNÓSTICO:")
            print("   Problema de conexão com o servidor SMTP")
            print("\n💡 SOLUÇÕES:")
            print("   1. Verifique sua conexão com a internet")
            print("   2. Confirme se o firewall não está bloqueando a porta 587")
            print("   3. Tente usar porta 465 com SSL")
            
        elif 'recipient' in error_str:
            print("\n🔍 DIAGNÓSTICO:")
            print("   Problema com o email de destino")
            print("\n💡 SOLUÇÕES:")
            print("   1. Verifique se o email de destino está correto")
            print("   2. Tente com outro email")
            
        else:
            print("\n🔍 DIAGNÓSTICO:")
            print("   Erro não identificado")
            print("\n💡 SOLUÇÕES:")
            print("   1. Verifique todas as configurações no .env")
            print("   2. Consulte a documentação do seu provedor de email")
            print("   3. Tente com outro provedor de email")
        
        return False

def main():
    """
    Função principal
    """
    try:
        sucesso = testar_configuracao_email()
        
        print("\n" + "=" * 60)
        if sucesso:
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("\nO sistema de email está configurado e funcionando.")
            print("Agora você pode enviar notificações por email normalmente.")
        else:
            print("❌ TESTE FALHOU!")
            print("\nO sistema de email precisa ser configurado.")
            print("Consulte o arquivo CONFIGURACAO_EMAIL.md para instruções detalhadas.")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTeste cancelado pelo usuário.")
    except Exception as e:
        print(f"\n\nErro inesperado: {e}")

if __name__ == '__main__':
    main()