#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.conf import settings

print("=== TESTE DE RECUPERAÇÃO DE SENHA ===")
print()

# 1. Verificar usuário
user = User.objects.filter(username='cliente').first()
if not user:
    print("❌ Usuário 'cliente' não encontrado!")
    exit(1)

print(f"✅ Usuário encontrado: {user.username}")
print(f"📧 Email: {user.email}")
print(f"🔓 Ativo: {user.is_active}")
print()

# 2. Verificar configurações de email
print("=== CONFIGURAÇÕES DE EMAIL ===")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print()

# 3. Testar envio de email simples
print("=== TESTE DE ENVIO DE EMAIL SIMPLES ===")
try:
    send_mail(
        'Teste de Email - Sistema Imobiliário',
        'Este é um teste de envio de email do sistema.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    print("✅ Email de teste enviado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao enviar email de teste: {e}")
    print()

# 4. Testar formulário de recuperação de senha
print("=== TESTE DE FORMULÁRIO DE RECUPERAÇÃO ===")
try:
    form = PasswordResetForm({'email': user.email})
    if form.is_valid():
        print("✅ Formulário válido")
        # Simular envio do email de recuperação
        form.save(
            request=None,
            use_https=False,
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt'
        )
        print("✅ Email de recuperação de senha enviado!")
    else:
        print(f"❌ Formulário inválido: {form.errors}")
except Exception as e:
    print(f"❌ Erro no formulário de recuperação: {e}")

print()
print("=== TESTE CONCLUÍDO ===")