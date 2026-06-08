#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao
from django.utils import timezone
from datetime import timedelta

print('=== ÚLTIMAS NOTIFICAÇÕES WHATSAPP ===')

# Buscar as últimas 5 notificações WhatsApp
notificacoes = Notificacao.objects.filter(
    canal='WHATSAPP',
    created_at__gte=timezone.now() - timedelta(hours=1)
).order_by('-created_at')[:5]

for i, notificacao in enumerate(notificacoes, 1):
    print(f'\n=== NOTIFICAÇÃO #{notificacao.id} ===')
    print(f'Destinatário: {notificacao.destinatario}')
    print(f'Status: {notificacao.status}')
    print(f'Data: {notificacao.created_at}')
    print(f'Assunto: {notificacao.assunto}')
    
    # Verificar se tem dados PIX no corpo
    if 'PIX' in notificacao.corpo:
        print('✅ Contém dados PIX')
    else:
        print('❌ Não contém dados PIX')
    
    # Mostrar parte do corpo
    print(f'\n=== CORPO DA MENSAGEM (primeiros 300 chars) ===')
    print(notificacao.corpo[:300])
    print('...')
    
    if i >= 3:  # Mostrar apenas as 3 mais recentes
        break

print('\n=== VERIFICANDO NOTIFICAÇÕES COM PIX ===')
notificacoes_com_pix = Notificacao.objects.filter(
    canal='WHATSAPP',
    corpo__icontains='PIX',
    created_at__gte=timezone.now() - timedelta(hours=1)
).order_by('-created_at')

print(f'Encontradas {notificacoes_com_pix.count()} notificações com PIX na última hora')

for notificacao in notificacoes_com_pix[:2]:
    print(f'\n=== NOTIFICAÇÃO COM PIX #{notificacao.id} ===')
    print(f'Destinatário: {notificacao.destinatario}')
    print(f'Inquilino: {notificacao.inquilino.nome}')
    print(f'Contrato: {notificacao.contrato.numero}')
    print(f'Status: {notificacao.status}')
    print(f'Data: {notificacao.created_at}')
    
    # Buscar seção PIX no corpo
    corpo_lines = notificacao.corpo.split('\n')
    pix_section = []
    in_pix_section = False
    
    for line in corpo_lines:
        if 'PIX' in line:
            in_pix_section = True
        if in_pix_section:
            pix_section.append(line)
        if in_pix_section and ('Link de Pagamento' in line or len(pix_section) > 5):
            break
    
    print('\n=== SEÇÃO PIX ===')
    for line in pix_section:
        print(line)