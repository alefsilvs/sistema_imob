#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao
from django.utils import timezone
from datetime import timedelta

# Buscar notificações recentes (últimas 2 horas)
duas_horas_atras = timezone.now() - timedelta(hours=2)
notificacoes = Notificacao.objects.filter(
    created_at__gte=duas_horas_atras
).order_by('-created_at')

print(f'Notificações encontradas: {notificacoes.count()}')
for notif in notificacoes:
    print(f'\n--- Notificação ID: {notif.id} ---')
    print(f'Destinatário: {notif.destinatario}')
    print(f'Canal: {notif.canal}')
    print(f'Assunto: {notif.assunto}')
    print(f'Status: {notif.status}')
    print(f'Data: {notif.created_at}')
    print(f'Template: {notif.template.nome if notif.template else "Sem template"}')
    print(f'Corpo (primeiros 500 chars):\n{notif.corpo[:500]}...')