#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao
from django.utils import timezone
from datetime import timedelta

# Verificar notificações
total = Notificacao.objects.count()
print(f'Total de notificações: {total}')

# Notificações das últimas 24 horas
ultimas_24h = timezone.now() - timedelta(hours=24)
recentes = Notificacao.objects.filter(created_at__gte=ultimas_24h).order_by('-created_at')

print(f'\nNotificações das últimas 24 horas: {recentes.count()}')
for n in recentes[:10]:
    print(f'- {n.id}: {n.canal} para {n.destinatario} - Status: {n.status} - Criada: {n.created_at}')

# Verificar notificações pendentes
pendentes = Notificacao.objects.filter(status='PENDENTE')
print(f'\nNotificações pendentes: {pendentes.count()}')
for n in pendentes[:5]:
    print(f'- {n.id}: {n.canal} para {n.destinatario} - Criada: {n.created_at}')