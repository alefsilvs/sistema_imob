#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao
import re

def investigar_template():
    """Investiga o template para encontrar o problema do QR Code"""
    
    try:
        template = TemplateNotificacao.objects.get(nome='Cobrança Banca de Feira - Email')
        print(f"Template encontrado: {template.nome}")
        print(f"Formato: {template.formato}")
        print("-" * 50)
        
        corpo = template.corpo_template
        
        # Procurar por referências ao PIX
        print("Procurando por referências ao PIX...")
        pix_matches = re.findall(r'.*pix\.qr_code_base64.*', corpo, re.IGNORECASE)
        for i, match in enumerate(pix_matches):
            print(f"Linha {i+1} com pix.qr_code_base64:")
            print(match.strip())
            print("-" * 30)
        
        # Procurar por tags img com data:image
        print("\nProcurando por tags img com data:image...")
        img_pattern = r'<img[^>]*src=["\']?data:image[^>]*>'
        img_matches = re.findall(img_pattern, corpo, re.IGNORECASE | re.DOTALL)
        for i, match in enumerate(img_matches):
            print(f"Tag img {i+1}:")
            print(match)
            print("-" * 30)
        
        # Procurar por qualquer referência a qr_code_base64
        print("\nProcurando por qualquer referência a qr_code_base64...")
        qr_matches = re.findall(r'.*qr_code_base64.*', corpo, re.IGNORECASE)
        for i, match in enumerate(qr_matches):
            print(f"Linha {i+1} com qr_code_base64:")
            print(match.strip())
            print("-" * 30)
        
        # Verificar se há problemas de sintaxe no template
        print("\nVerificando sintaxe do template...")
        if '{{pix.qr_code_base64}}' in corpo:
            print("❌ PROBLEMA ENCONTRADO: Variável {{pix.qr_code_base64}} sem prefixo data:image/png;base64,")
        elif 'data:image/png;base64,{{pix.qr_code_base64}}' in corpo:
            print("✅ Sintaxe correta encontrada")
        else:
            print("⚠️ Não foi possível determinar o problema")
        
        # Salvar o template completo para análise
        with open('template_completo.html', 'w', encoding='utf-8') as f:
            f.write(corpo)
        print("\n📄 Template completo salvo em 'template_completo.html'")
        
    except TemplateNotificacao.DoesNotExist:
        print("❌ Template 'Cobrança Banca de Feira - Email' não encontrado")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    investigar_template()