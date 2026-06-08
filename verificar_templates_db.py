#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao

def verificar_templates():
    print("=== VERIFICANDO TEMPLATES NO BANCO DE DADOS ===\n")
    
    # Buscar todos os templates de banca
    templates_banca = TemplateNotificacao.objects.filter(
        nome__icontains='banca'
    ).order_by('id')
    
    print(f"Total de templates de banca encontrados: {templates_banca.count()}\n")
    
    for template in templates_banca:
        print(f"ID: {template.id}")
        print(f"Nome: {template.nome}")
        print(f"Tipo: {template.tipo}")
        print(f"Formato: {template.formato}")
        print(f"Ativo: {template.ativo}")
        print(f"Padrão: {template.padrao}")
        print(f"Categoria: {template.categoria.nome if template.categoria else 'N/A'}")
        print(f"Tamanho do corpo: {len(template.corpo_template)} caracteres")
        
        # Verificar se é HTML
        if template.formato == 'HTML':
            print("CORPO DO TEMPLATE HTML:")
            print("=" * 50)
            print(template.corpo_template)
            print("=" * 50)
        else:
            print(f"Primeiros 200 caracteres do corpo:")
            print(template.corpo_template[:200] + "...")
        
        print("\n" + "-" * 80 + "\n")
    
    # Verificar qual template seria selecionado pelo comando
    from notificacoes.management.commands.verificar_vencimentos_bancas import Command
    cmd = Command()
    template_selecionado = cmd.obter_template()
    
    if template_selecionado:
        print(f"TEMPLATE SELECIONADO PELO COMANDO:")
        print(f"ID: {template_selecionado.id}")
        print(f"Nome: {template_selecionado.nome}")
        print(f"Formato: {template_selecionado.formato}")
        print(f"Tipo: {template_selecionado.tipo}")
    else:
        print("NENHUM TEMPLATE SELECIONADO PELO COMANDO")

if __name__ == "__main__":
    verificar_templates()