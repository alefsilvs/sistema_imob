#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao

# Buscar a última notificação WhatsApp enviada
notificacao = Notificacao.objects.filter(canal='WHATSAPP', status='ENVIADA').order_by('-created_at').first()

if notificacao:
    print(f'=== NOTIFICAÇÃO WHATSAPP #{notificacao.id} ===')
    print(f'Destinatário: {notificacao.destinatario}')
    print(f'Status: {notificacao.status}')
    print(f'Data: {notificacao.created_at}')
    print(f'Assunto: {notificacao.assunto}')
    print('\n=== CORPO DA MENSAGEM ===')
    print(notificacao.corpo)
    print('\n=== ANEXOS ===')
    if notificacao.anexos:
        print(f'Anexos: {notificacao.anexos}')
    else:
        print('Nenhum anexo')
else:
    print('Nenhuma notificação WhatsApp encontrada')