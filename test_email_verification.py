#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import VerificacaoEmail

def check_email_verification():
    """Verifica o status de verificação de email do usuário teste_header"""
    
    print("=== VERIFICAÇÃO DE EMAIL ===")
    
    try:
        user = User.objects.get(username='teste_header')
        print(f"Usuário encontrado: {user.username} ({user.email})")
        
        try:
            verificacao = VerificacaoEmail.objects.get(usuario=user)
            print(f"Status de verificação: {verificacao.email_verificado}")
            print(f"Data de criação: {verificacao.data_criacao}")
            print(f"Data de verificação: {verificacao.data_verificacao}")
            
            if not verificacao.email_verificado:
                print("\n⚠️  EMAIL NÃO VERIFICADO - Este é o problema!")
                print("   O middleware EmailVerificationMiddleware está redirecionando")
                print("   para /saas/email-enviado/ porque o email não foi verificado.")
                
                # Verificar se podemos marcar como verificado para teste
                print("\n🔧 Marcando email como verificado para teste...")
                verificacao.email_verificado = True
                verificacao.save()
                print("   ✅ Email marcado como verificado!")
            else:
                print("✅ Email já está verificado")
                
        except VerificacaoEmail.DoesNotExist:
            print("❌ Registro de verificação não encontrado")
            print("   Criando registro com email verificado...")
            
            verificacao = VerificacaoEmail.objects.create(
                usuario=user,
                email_verificado=True
            )
            print("   ✅ Registro criado com email verificado!")
            
    except User.DoesNotExist:
        print("❌ Usuário teste_header não encontrado")
    
    print("\n=== FIM DA VERIFICAÇÃO ===")

if __name__ == '__main__':
    check_email_verification()