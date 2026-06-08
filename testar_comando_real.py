#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from imoveis.models import ContratoBancaFeira
from notificacoes.management.commands.verificar_vencimentos_bancas import Command

def testar_comando_real():
    print("=== TESTANDO COMANDO REAL ===\n")
    
    # Criar instância do comando
    cmd = Command()
    
    # Obter template
    template = cmd.obter_template()
    print(f"Template obtido: {template.nome if template else 'Nenhum'}")
    print(f"Formato: {template.formato if template else 'N/A'}")
    print(f"Tipo: {template.tipo if template else 'N/A'}")
    
    # Buscar um contrato de teste
    data_limite = timezone.now().date() + timedelta(days=30)
    contrato = ContratoBancaFeira.objects.filter(
        status='ATIVO',
        data_fim__lte=data_limite,
        data_fim__gte=timezone.now().date()
    ).select_related('inquilino', 'banca_feira').first()
    
    if not contrato:
        print("Nenhum contrato encontrado para teste")
        return
    
    print(f"\nContrato de teste: {contrato.numero}")
    print(f"Inquilino: {contrato.inquilino.nome}")
    print(f"Banca: {contrato.banca_feira.codigo}")
    
    # Criar contexto usando o método do comando
    contexto = cmd.criar_contexto_banca(contrato)
    
    print(f"\nContexto criado:")
    for key, value in contexto.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"  {key}: {value[:100]}...")
        else:
            print(f"  {key}: {value}")
    
    # Renderizar template
    if template:
        try:
            assunto = template.renderizar_assunto(contexto)
            corpo = template.renderizar_corpo(contexto)
            
            print(f"\nAssunto renderizado: {assunto}")
            print(f"\nCorpo renderizado (primeiros 1000 chars):")
            print(corpo[:1000])
            
            # Verificar se há variáveis não substituídas
            import re
            variaveis_nao_substituidas = re.findall(r'\{\{[^}]+\}\}', corpo)
            if variaveis_nao_substituidas:
                print(f"\n❌ VARIÁVEIS NÃO SUBSTITUÍDAS ENCONTRADAS:")
                for var in set(variaveis_nao_substituidas):
                    print(f"  - {var}")
            else:
                print(f"\n✅ Todas as variáveis foram substituídas")
                
        except Exception as e:
            print(f"Erro na renderização: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_comando_real()