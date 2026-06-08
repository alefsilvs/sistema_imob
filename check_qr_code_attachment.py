#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import Notificacao
from django.utils import timezone
from datetime import timedelta

print('=== VERIFICANDO ANEXOS DE QR CODE ===')

# Buscar últimas notificações WhatsApp
ultima_hora = timezone.now() - timedelta(hours=1)
notificacoes = Notificacao.objects.filter(
    canal='WHATSAPP',
    created_at__gte=ultima_hora
).order_by('-created_at')[:5]

print(f'Encontradas {notificacoes.count()} notificações na última hora')

for notif in notificacoes:
    print(f'\n=== NOTIFICAÇÃO #{notif.id} ===')
    print(f'Destinatário: {notif.destinatario}')
    print(f'Status: {notif.status}')
    print(f'Data: {notif.created_at}')
    
    # Verificar se tem anexos
    if notif.anexos:
        print(f'✅ TEM ANEXOS: {len(notif.anexos)} anexo(s)')
        for i, anexo in enumerate(notif.anexos):
            print(f'  Anexo {i+1}: {anexo}')
    else:
        print('❌ SEM ANEXOS')
    
    # Verificar se tem dados PIX no corpo
    if 'PIX' in notif.corpo:
        print('✅ Contém dados PIX no corpo')
        
        # Extrair seção PIX
        linhas = notif.corpo.split('\n')
        pix_section = []
        in_pix_section = False
        
        for linha in linhas:
            if 'PIX:' in linha:
                in_pix_section = True
            if in_pix_section:
                pix_section.append(linha)
                if 'Sistema Imobiliário' in linha:
                    break
        
        print('=== SEÇÃO PIX ===')
        for linha in pix_section[:10]:  # Primeiras 10 linhas da seção PIX
            print(linha)
    else:
        print('❌ Não contém dados PIX')

print('\n=== RESUMO ===')
com_anexo = sum(1 for n in notificacoes if n.anexos)
com_pix = sum(1 for n in notificacoes if 'PIX' in n.corpo)

print(f'Notificações com anexo: {com_anexo}/{notificacoes.count()}')
print(f'Notificações com PIX: {com_pix}/{notificacoes.count()}')

if com_pix > 0 and com_anexo == 0:
    print('\n⚠️ PROBLEMA: Notificações têm dados PIX mas não têm anexos (QR Code)')
    print('O QR Code deveria estar sendo enviado como anexo.')
elif com_pix > 0 and com_anexo > 0:
    print('\n✅ TUDO OK: Notificações têm dados PIX e anexos (QR Code)')
else:
    print('\n❌ Nenhuma notificação com PIX encontrada')