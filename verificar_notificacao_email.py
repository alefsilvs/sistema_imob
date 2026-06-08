import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao

# Buscar a notificação de email mais recente
notificacao = Notificacao.objects.filter(
    canal='EMAIL'
).order_by('-created_at').first()

if notificacao:
    print(f"=== NOTIFICAÇÃO DE EMAIL MAIS RECENTE ===")
    print(f"ID: {notificacao.id}")
    print(f"Destinatário: {notificacao.destinatario}")
    print(f"Canal: {notificacao.canal}")
    print(f"Assunto: {notificacao.assunto}")
    print(f"Status: {notificacao.status}")
    print(f"Data: {notificacao.created_at}")
    print(f"Template: {notificacao.template.nome if notificacao.template else 'N/A'}")
    print(f"\n=== CORPO COMPLETO ===")
    print(notificacao.corpo)
else:
    print("Nenhuma notificação de email encontrada.")