#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao

# Buscar template de vencimento
vencimento_template = TemplateNotificacao.objects.filter(tipo='VENCIMENTO').first()
if vencimento_template:
    print(f'=== TEMPLATE DE VENCIMENTO ATUAL ===')
    print(f'ID: {vencimento_template.id}')
    print(f'Nome: {vencimento_template.nome}')
    print(f'Tipo: {vencimento_template.tipo}')
    print(f'Corpo atual: {vencimento_template.corpo_template}')
    
    # Atualizar template com PIX
    novo_corpo = """⏰ *Lembrete de Vencimento*

Olá *{{inquilino_nome}}*! 👋

Este é um lembrete amigável de que o aluguel do seu imóvel vencerá em breve.

📅 *Informações do Pagamento:*
• Imóvel: {{imovel_endereco}}
• Valor: R$ {{valor_aluguel}}
• Vencimento: {{data_vencimento}}
• ⏰ Dias restantes: *{{dias_restantes}} dias*

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

✅ Pagando antecipadamente, você evita qualquer transtorno e garante a tranquilidade do seu lar.

---
{{empresa_nome}} - Gestão Imobiliária"""
    
    vencimento_template.corpo_template = novo_corpo
    vencimento_template.save()
    print('\n✅ Template de vencimento atualizado com informações do PIX!')
else:
    print('\n❌ Template de vencimento não encontrado')

# Verificar todos os templates
print('\n=== TODOS OS TEMPLATES ===')
templates = TemplateNotificacao.objects.all()
for template in templates:
    print(f'- {template.id}: {template.nome} - Tipo: {template.tipo}')