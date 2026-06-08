#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao

# Verificar templates existentes
print('=== TEMPLATES EXISTENTES ===')
templates = TemplateNotificacao.objects.all()
print(f'Total de templates: {templates.count()}')

for template in templates:
    print(f'- {template.id}: {template.nome} - Tipo: {template.tipo}')

# Buscar template de cobrança
cobranca_template = TemplateNotificacao.objects.filter(nome__icontains='Cobrança').first()
if cobranca_template:
    print(f'\n=== TEMPLATE DE COBRANÇA ATUAL ===')
    print(f'ID: {cobranca_template.id}')
    print(f'Nome: {cobranca_template.nome}')
    print(f'Tipo: {cobranca_template.tipo}')
    print(f'Corpo (primeiros 200 chars): {cobranca_template.corpo_template[:200]}...')
    
    # Atualizar template com PIX
    novo_corpo = """💰 *Cobrança de Aluguel*

Olá *{{inquilino_nome}}*! 👋

Este é um lembrete sobre o pagamento do seu aluguel.

📅 *Informações do Pagamento:*
• Imóvel: {{imovel_endereco}}
• Valor: R$ {{valor_aluguel}}
• Vencimento: {{data_vencimento}}
• Status: {{status_pagamento}}

💰 *Formas de Pagamento:*
{% if pix.disponivel %}
🔸 *PIX:* Código PIX anexado na imagem acima
{% endif %}
🔸 *Link de Pagamento:* {{link_pagamento}}

{% if pix.disponivel %}
📱 *Como pagar via PIX:*
1. Abra o app do seu banco
2. Escaneie o QR Code anexado
3. Confirme o pagamento

*Código PIX (copie e cole):*
`{{pix.codigo_pix}}`
{% endif %}

⚠️ *Importante:* Após o pagamento, envie o comprovante para confirmação.

---
{{empresa_nome}} - Gestão Imobiliária"""
    
    cobranca_template.corpo_template = novo_corpo
    cobranca_template.save()
    print('\n✅ Template de cobrança atualizado com informações do PIX!')
else:
    print('\n❌ Template de cobrança não encontrado')