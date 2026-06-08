from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notificacoes.models import CategoriaTemplate, TemplateNotificacao
import json

class Command(BaseCommand):
    help = 'Adiciona templates de notificação adicionais'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando criação de templates adicionais...'))

        # Obter ou criar usuário admin
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao obter usuário: {e}'))
            return

        # Obter ou criar categorias
        categoria_comunicado, _ = CategoriaTemplate.objects.get_or_create(
            nome='Comunicados',
            defaults={
                'descricao': 'Templates para comunicados gerais',
                'cor': '#2196f3'
            }
        )

        categoria_marketing, _ = CategoriaTemplate.objects.get_or_create(
            nome='Marketing',
            defaults={
                'descricao': 'Templates para campanhas de marketing',
                'cor': '#9c27b0'
            }
        )

        # Templates que não conflitam com a restrição unique_together
        templates_novos = [
            {
                'nome': 'Comunicado Geral - Informativo',
                'categoria': categoria_comunicado,
                'tipo': 'MANUTENCAO',  # Usando tipo que não tem conflito
                'assunto_template': 'Comunicado Importante - {{titulo}}',
                'corpo_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2196f3;">{{titulo}}</h2>
                    <p>Prezado(a) <strong>{{nome_destinatario}}</strong>,</p>
                    
                    <p>{{mensagem_principal}}</p>
                    
                    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Informações importantes:</strong></p>
                        <p>{{informacoes_adicionais}}</p>
                    </div>
                    
                    <p>Em caso de dúvidas, entre em contato conosco.</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>{{nome_empresa}}</strong><br>
                    {{contato_empresa}}</p>
                </div>
                ''',
                'variaveis_disponiveis': {
                    'titulo': 'Título do comunicado',
                    'nome_destinatario': 'Nome do destinatário',
                    'mensagem_principal': 'Mensagem principal',
                    'informacoes_adicionais': 'Informações adicionais',
                    'nome_empresa': 'Nome da empresa',
                    'contato_empresa': 'Contato da empresa'
                },
                'preview_dados': {
                    'titulo': 'Atualização de Procedimentos',
                    'nome_destinatario': 'João Silva',
                    'mensagem_principal': 'Informamos sobre as novas diretrizes da empresa.',
                    'informacoes_adicionais': 'As mudanças entram em vigor a partir do próximo mês.',
                    'nome_empresa': 'ImobilPro',
                    'contato_empresa': '(11) 99999-9999'
                },
                'padrao': False
            },
            {
                'nome': 'Newsletter - Dicas Imobiliárias',
                'categoria': categoria_marketing,
                'tipo': 'RENOVACAO',  # Usando tipo que não tem conflito
                'assunto_template': 'Newsletter {{mes}} - Dicas Imobiliárias',
                'corpo_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #9c27b0;">Newsletter {{mes}}</h2>
                    <p>Olá <strong>{{nome_cliente}}</strong>,</p>
                    
                    <p>Confira as principais dicas imobiliárias deste mês:</p>
                    
                    <div style="background-color: #f3e5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>Dica do Mês</h3>
                        <p>{{dica_principal}}</p>
                    </div>
                    
                    <h3>Outras Dicas:</h3>
                    <ul>
                        <li>{{dica_1}}</li>
                        <li>{{dica_2}}</li>
                        <li>{{dica_3}}</li>
                    </ul>
                    
                    <p>Continue acompanhando nossas novidades!</p>
                    
                    <p>Equipe <strong>{{nome_empresa}}</strong></p>
                </div>
                ''',
                'variaveis_disponiveis': {
                    'mes': 'Mês da newsletter',
                    'nome_cliente': 'Nome do cliente',
                    'dica_principal': 'Dica principal do mês',
                    'dica_1': 'Primeira dica adicional',
                    'dica_2': 'Segunda dica adicional',
                    'dica_3': 'Terceira dica adicional',
                    'nome_empresa': 'Nome da empresa'
                },
                'preview_dados': {
                    'mes': 'Janeiro',
                    'nome_cliente': 'Maria Santos',
                    'dica_principal': 'Mantenha sempre a documentação do imóvel atualizada.',
                    'dica_1': 'Faça vistorias regulares',
                    'dica_2': 'Negocie sempre com transparência',
                    'dica_3': 'Invista em melhorias que agregam valor',
                    'nome_empresa': 'ImobilPro'
                },
                'padrao': False
            }
        ]

        # Criar templates
        templates_criados = 0
        for template_data in templates_novos:
            if not TemplateNotificacao.objects.filter(nome=template_data['nome']).exists():
                try:
                    template = TemplateNotificacao.objects.create(
                        nome=template_data['nome'],
                        categoria=template_data['categoria'],
                        tipo=template_data['tipo'],
                        assunto_template=template_data['assunto_template'],
                        corpo_template=template_data['corpo_template'],
                        variaveis_disponiveis=template_data['variaveis_disponiveis'],
                        preview_dados=template_data['preview_dados'],
                        padrao=template_data['padrao'],
                        usuario_criador=user
                    )
                    templates_criados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Template criado: {template.nome}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erro ao criar template {template_data["nome"]}: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Template já existe: {template_data["nome"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Processo concluído! {templates_criados} templates adicionais criados.')
        )