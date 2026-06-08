#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from saas.models import VerificacaoEmail

def check_and_fix_email_verification():
    # Encontrar o usuário
    user = User.objects.get(username='alef63134@gmail.com')
    print(f'Usuário encontrado: {user.username}')
    
    try:
        verificacao = VerificacaoEmail.objects.get(usuario=user)
        print(f'Email verificado: {verificacao.email_verificado}')
        
        if not verificacao.email_verificado:
            print('Marcando email como verificado...')
            verificacao.email_verificado = True
            verificacao.save()
            print('✓ Email marcado como verificado')
        else:
            print('✓ Email já estava verificado')
            
    except VerificacaoEmail.DoesNotExist:
        print('Nenhuma verificação de email encontrada - criando uma nova...')
        verificacao = VerificacaoEmail.objects.create(
            usuario=user,
            email_verificado=True
        )
        print('✓ Verificação de email criada e marcada como verificada')

if __name__ == '__main__':
    check_and_fix_email_verification()