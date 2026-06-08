#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User

# Verificar se já existe um superusuário
if User.objects.filter(is_superuser=True).exists():
    print("Já existe um superusuário no sistema.")
    superuser = User.objects.filter(is_superuser=True).first()
    print(f"Superusuário existente: {superuser.username}")
else:
    # Criar superusuário
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@teste.com',
            password='admin123'
        )
        print(f"Superusuário criado com sucesso!")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print("Senha: admin123")
    except Exception as e:
        print(f"Erro ao criar superusuário: {e}")

print(f"\nTotal de usuários no sistema: {User.objects.count()}")