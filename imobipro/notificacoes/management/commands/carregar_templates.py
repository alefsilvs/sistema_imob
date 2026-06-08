from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notificacoes.models import CategoriaTemplate, TemplateNotificacao
import json
import os

class Command(BaseCommand):
    help = 'Carrega templates iniciais de notificação'
    
    def handle(self, *args, **options):
        # Verifica se já existem templates
        if TemplateNotificacao.objects.exists():
            self.stdout.write(
                self.style.WARNING('Templates já existem. Use --force para sobrescrever.')
            )
            return
        
        # Busca o primeiro superusuário ou cria um usuário padrão
        try:
            usuario = User.objects.filter(is_superuser=True).first()
            if not usuario:
                usuario = User.objects.create_user(
                    username='admin_templates',
                    email='admin@exemplo.com',
                    password='temp123',
                    is_staff=True
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar usuário: {e}')
            )
            return
        
        # Criar categorias
        categorias_data = [
            {'nome': 'Financeiro', 'descricao': 'Templates relacionados a cobranças e pagamentos', 'cor': '#28a745'},
            {'nome': 'Contratos', 'descricao': 'Templates para gestão de contratos', 'cor': '#007bff'},
            {'nome': 'Manutenção', 'descricao': 'Templates para comunicados de manutenção', 'cor': '#ffc107'},
            {'nome': 'Comunicados', 'descricao': 'Templates para comunicados gerais', 'cor': '#17a2b8'},
        ]
        
        categorias = {}
        for cat_data in categorias_data:
            categoria, created = CategoriaTemplate.objects.get_or_create(
                nome=cat_data['nome'],
                defaults=cat_data
            )
            categorias[cat_data['nome']] = categoria
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Categoria criada: {categoria.nome}')
                )
        
        # Templates de exemplo
        templates_data = [
            {
                'nome': 'Cobrança de Aluguel',
                'categoria': 'Financeiro',
                'tipo': 'COBRANCA',
                'assunto_template': '🏠 Cobrança de Aluguel - {{imovel_endereco}} - Vencimento {{data_vencimento}}',
                'corpo_template': '''🏡 *Cobrança de Aluguel*

Olá *{{inquilino_nome}}*! 👋

Esperamos que esteja tudo bem! Este é um lembrete sobre o pagamento do aluguel.

📍 *Detalhes do Imóvel:*
• Endereço: {{imovel_endereco}}
• Valor: R$ {{valor_aluguel}}
• Vencimento: {{data_vencimento}}

💳 *Para efetuar o pagamento:*
{{link_pagamento}}

📞 *Dúvidas?*
Estamos à disposição para esclarecer qualquer questão sobre seu pagamento.

---
*Gestão Imobiliária* - Cuidando do seu patrimônio''',
                'variaveis_disponiveis': {
                    'inquilino_nome': 'Nome do inquilino',
                    'imovel_endereco': 'Endereço do imóvel',
                    'valor_aluguel': 'Valor do aluguel',
                    'data_vencimento': 'Data de vencimento',
                    'link_pagamento': 'Link para pagamento'
                },
                'preview_dados': {
                    'inquilino_nome': 'João Silva',
                    'imovel_endereco': 'Rua das Flores, 123',
                    'valor_aluguel': '1.500,00',
                    'data_vencimento': '10/01/2024',
                    'link_pagamento': 'https://exemplo.com/pagamento'
                }
            },
            {
                'nome': 'Boas-vindas Novo Inquilino',
                'categoria': 'Contratos',
                'tipo': 'BOAS_VINDAS',
                'assunto_template': '🎉 Bem-vindo(a) ao seu novo lar! - {{imovel_endereco}}',
                'corpo_template': '''🎉 *Bem-vindo(a) ao seu novo lar!*

Olá *{{inquilino_nome}}*! 👋

É com grande satisfação que damos as boas-vindas ao seu novo lar! Esperamos que você tenha momentos maravilhosos em seu novo imóvel.

🏡 *Detalhes do seu Imóvel:*
• Endereço: {{imovel_endereco}}
• Valor do Aluguel: R$ {{valor_aluguel}}

📋 *Informações Importantes:*
• Mantenha sempre seus dados atualizados
• Em caso de emergências, entre em contato conosco
• Dúvidas sobre pagamentos ou manutenção, estamos à disposição

Estamos aqui para ajudá-lo sempre que precisar. Seja muito bem-vindo(a)! 🏡

---
*Gestão Imobiliária* - Cuidando do seu patrimônio''',
                'variaveis_disponiveis': {
                    'inquilino_nome': 'Nome do inquilino',
                    'imovel_endereco': 'Endereço do imóvel',
                    'valor_aluguel': 'Valor do aluguel'
                },
                'preview_dados': {
                    'inquilino_nome': 'Maria Santos',
                    'imovel_endereco': 'Av. Principal, 456',
                    'valor_aluguel': '2.200,00'
                }
            }
        ]
        
        # Criar templates
        for template_data in templates_data:
            categoria = categorias[template_data['categoria']]
            
            template, created = TemplateNotificacao.objects.get_or_create(
                nome=template_data['nome'],
                defaults={
                    'categoria': categoria,
                    'tipo': template_data['tipo'],
                    'assunto_template': template_data['assunto_template'],
                    'corpo_template': template_data['corpo_template'],
                    'formato': 'TEXTO',
                    'variaveis_disponiveis': template_data['variaveis_disponiveis'],
                    'preview_dados': template_data['preview_dados'],
                    'ativo': True,
                    'padrao': True,
                    'usuario_criador': usuario
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Template criado: {template.nome}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Templates iniciais carregados com sucesso!')
        )
        self.stdout.write(
            self.style.SUCCESS('Acesse o admin Django para visualizar e editar os templates.')
        )