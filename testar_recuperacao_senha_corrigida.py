#!/usr/bin/env python
"""
Script para testar a recuperação de senha com domínio correto
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django.core.mail import get_connection
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def testar_recuperacao_senha():
    print("=== TESTE DE RECUPERAÇÃO DE SENHA ===")
    
    # Verificar configuração do site
    try:
        site = Site.objects.get(id=settings.SITE_ID)
        print(f"✅ Site configurado: {site.domain} - {site.name}")
    except Site.DoesNotExist:
        print("❌ Site não configurado!")
        return
    
    # Verificar usuário de teste
    try:
        user = User.objects.get(username='alef')
        print(f"✅ Usuário encontrado: {user.username} ({user.email})")
    except User.DoesNotExist:
        print("❌ Usuário 'alef' não encontrado!")
        return
    
    # Gerar token de recuperação
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    print(f"\n=== DADOS DO TOKEN ===")
    print(f"UID: {uid}")
    print(f"Token: {token}")
    
    # Renderizar template de email
    context = {
        'email': user.email,
        'domain': site.domain,
        'site_name': site.name,
        'uid': uid,
        'user': user,
        'token': token,
        'protocol': 'http',
    }
    
    try:
        email_content = render_to_string('registration/password_reset_email.html', context)
        print(f"\n=== CONTEÚDO DO EMAIL ===")
        print(email_content)
        
        # Verificar se o link está correto
        if '127.0.0.1:8000' in email_content and 'example.com' not in email_content:
            print("\n✅ SUCESSO: Email contém domínio correto (127.0.0.1:8000)")
            print("✅ SUCESSO: Email NÃO contém domínio fictício (example.com)")
        else:
            print("\n❌ ERRO: Email ainda contém domínio incorreto")
            
    except Exception as e:
        print(f"❌ Erro ao renderizar template: {e}")
    
    # Testar formulário de recuperação
    print(f"\n=== TESTE DO FORMULÁRIO ===")
    form_data = {'email': user.email}
    form = PasswordResetForm(form_data)
    
    if form.is_valid():
        print("✅ Formulário válido")
        print(f"✅ Email configurado: {settings.DEFAULT_FROM_EMAIL}")
        print(f"✅ SITE_URL configurado: {settings.SITE_URL}")
    else:
        print(f"❌ Formulário inválido: {form.errors}")

if __name__ == '__main__':
    testar_recuperacao_senha()