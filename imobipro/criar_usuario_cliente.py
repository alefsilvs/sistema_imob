#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User

# Verificar se o usuário 'cliente' já existe
user = User.objects.filter(username='cliente').first()

if user:
    print(f"Usuário 'cliente' já existe:")
    print(f"Email: {user.email}")
    print(f"Ativo: {user.is_active}")
    
    # Atualizar email se estiver vazio
    if not user.email:
        user.email = 'cliente@teste.com'
        user.save()
        print("Email atualizado para: cliente@teste.com")
else:
    # Criar novo usuário
    user = User.objects.create_user(
        username='cliente',
        email='cliente@teste.com',
        password='123456'
    )
    print("Usuário 'cliente' criado com sucesso!")
    print(f"Email: {user.email}")
    print(f"Ativo: {user.is_active}")

print("\nUsuário pronto para teste de recuperação de senha.")