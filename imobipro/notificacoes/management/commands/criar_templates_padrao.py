from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notificacoes.models import CategoriaTemplate, TemplateNotificacao
import json


class Command(BaseCommand):
    help = 'Cria templates profissionais para notificações'

    def handle(self, *args, **options):
        # Buscar usuário admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        # Criar categorias se não existirem
        categorias_data = [
            {'nome': 'Cobrança', 'descricao': 'Templates para cobrança', 'cor': '#dc3545'},
            {'nome': 'Vencimento', 'descricao': 'Templates para vencimentos', 'cor': '#fd7e14'},
            {'nome': 'Boas-vindas', 'descricao': 'Templates de boas-vindas', 'cor': '#28a745'},
            {'nome': 'Manutenção', 'descricao': 'Templates de manutenção', 'cor': '#6f42c1'},
            {'nome': 'Comunicados', 'descricao': 'Templates de comunicados', 'cor': '#17a2b8'}
        ]

        categorias = {}
        for cat_data in categorias_data:
            categoria, created = CategoriaTemplate.objects.get_or_create(
                nome=cat_data['nome'],
                defaults={
                    'descricao': cat_data['descricao'],
                    'cor': cat_data['cor']
                }
            )
            categorias[cat_data['nome']] = categoria
            if created:
                self.stdout.write(f'✅ Categoria criada: {categoria.nome}')

        # Templates profissionais (não-padrão para evitar conflitos)
        templates_data = [
            {
                'nome': 'Template Profissional - Cobrança Premium',
                'categoria': 'Cobrança',
                'tipo': 'PERSONALIZADO',  # Usando tipo diferente para evitar conflito
                'assunto_template': '💰 Cobrança Premium - {{ mes_referencia }}',
                'corpo_template': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cobrança Premium</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background: #f8f9fa;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center;">
        <h1 style="margin: 0; font-size: 28px; font-weight: 300;">💰 Cobrança Premium</h1>
        <p style="margin: 15px 0 0 0; opacity: 0.9; font-size: 16px;">ImobiPro - Gestão Imobiliária</p>
    </div>
    
    <div style="background: #fff; padding: 40px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; margin-bottom: 25px; color: #495057;">Prezado(a) <strong>{{ inquilino_nome }}</strong>,</p>
        
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-left: 4px solid #ffc107; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #856404; margin: 0 0 15px 0; font-size: 20px;">⚠️ Pendência Identificada</h3>
            <p style="margin: 0; color: #856404; font-size: 16px;">Identificamos uma pendência no pagamento do aluguel referente ao mês de <strong>{{ mes_referencia }}</strong>.</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 12px; padding: 30px; margin: 30px 0; border: 1px solid #e9ecef;">
            <h3 style="color: #495057; margin: 0 0 20px 0; font-size: 22px; text-align: center;">📋 Detalhes da Cobrança</h3>
            <div style="display: grid; gap: 15px;">
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Imóvel:</span>
                    <span style="color: #6c757d;">{{ imovel_endereco }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Mês de Referência:</span>
                    <span style="color: #6c757d;">{{ mes_referencia }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Valor do Aluguel:</span>
                    <span style="color: #28a745; font-weight: bold;">R$ {{ valor_aluguel }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Data de Vencimento:</span>
                    <span style="color: #6c757d;">{{ data_vencimento }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Dias em Atraso:</span>
                    <span style="color: #dc3545; font-weight: bold;">{{ dias_atraso }} dias</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 15px 0; background: #e3f2fd; margin: 10px -15px -15px -15px; padding: 20px; border-radius: 0 0 8px 8px;">
                    <span style="font-weight: 700; color: #1976d2; font-size: 18px;">Valor Total:</span>
                    <span style="color: #dc3545; font-weight: bold; font-size: 24px;">R$ {{ valor_total }}</span>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="#" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block; font-size: 16px; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3); transition: all 0.3s ease;">💳 Pagar Agora</a>
        </div>
        
        <div style="background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%); border-left: 4px solid #17a2b8; border-radius: 8px; padding: 25px; margin: 30px 0;">
            <h4 style="color: #0c5460; margin: 0 0 15px 0; font-size: 18px;">💡 Formas de Pagamento Disponíveis</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
                <div style="color: #0c5460; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">🏦 PIX: {{ pix_chave }}</div>
                <div style="color: #0c5460; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">💳 Cartão de Crédito</div>
                <div style="color: #0c5460; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">🏧 Transferência</div>
                <div style="color: #0c5460; padding: 8px; background: rgba(255,255,255,0.5); border-radius: 6px;">📄 Boleto Bancário</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; padding: 25px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #6c757d;">
            <h4 style="margin: 0 0 15px 0; color: #495057;">📞 Precisa de Ajuda?</h4>
            <p style="margin: 0; color: #6c757d;">Nossa equipe está pronta para atendê-lo:</p>
            <div style="margin-top: 15px; line-height: 1.8;">
                <div>📞 <strong>Telefone:</strong> {{ telefone_contato }}</div>
                <div>📧 <strong>E-mail:</strong> {{ email_contato }}</div>
                <div>💬 <strong>WhatsApp:</strong> {{ whatsapp_contato }}</div>
            </div>
        </div>
    </div>
    
    <div style="background: #343a40; color: #fff; padding: 30px; text-align: center; border-radius: 0 0 12px 12px;">
        <p style="margin: 0; font-size: 16px; font-weight: 300;">
            <strong>ImobiPro</strong> - Gestão Imobiliária Profissional<br>
            <span style="opacity: 0.8; font-size: 14px;">Este é um e-mail automático, não responda diretamente.</span>
        </p>
    </div>
</body>
</html>''',
                'formato': 'HTML',
                'variaveis_disponiveis': json.dumps([
                    'inquilino_nome', 'mes_referencia', 'imovel_endereco', 
                    'valor_aluguel', 'data_vencimento', 'dias_atraso', 
                    'valor_total', 'pix_chave', 'telefone_contato', 
                    'email_contato', 'whatsapp_contato'
                ]),
                'preview_dados': json.dumps({
                    'inquilino_nome': 'João Silva',
                    'mes_referencia': 'Janeiro/2024',
                    'imovel_endereco': 'Rua das Flores, 123 - Centro',
                    'valor_aluguel': '1.500,00',
                    'data_vencimento': '05/01/2024',
                    'dias_atraso': '15',
                    'valor_total': '1.650,00',
                    'pix_chave': 'imobiliaria@email.com',
                    'telefone_contato': '(11) 99999-9999',
                    'email_contato': 'contato@imobiliaria.com',
                    'whatsapp_contato': '(11) 99999-9999'
                }),
                'ativo': True,
                'padrao': False
            },
            {
                'nome': 'Template Profissional - Aviso de Vencimento Premium',
                'categoria': 'Vencimento',
                'tipo': 'LEMBRETE',  # Usando tipo diferente
                'assunto_template': '⏰ Aviso Premium - Vencimento em {{ dias_para_vencimento }} dias',
                'corpo_template': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aviso de Vencimento Premium</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background: #f8f9fa;">
    <div style="background: linear-gradient(135deg, #fd7e14 0%, #e83e8c 100%); color: white; padding: 40px 30px; text-align: center;">
        <h1 style="margin: 0; font-size: 28px; font-weight: 300;">⏰ Aviso de Vencimento</h1>
        <p style="margin: 15px 0 0 0; opacity: 0.9; font-size: 16px;">ImobiPro - Gestão Imobiliária</p>
    </div>
    
    <div style="background: #fff; padding: 40px 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; margin-bottom: 25px; color: #495057;">Prezado(a) <strong>{{ inquilino_nome }}</strong>,</p>
        
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); border-left: 4px solid #ffc107; border-radius: 8px; padding: 25px; margin: 25px 0;">
            <h3 style="color: #856404; margin: 0 0 15px 0; font-size: 20px;">⏰ Lembrete Importante</h3>
            <p style="margin: 0; color: #856404; font-size: 16px;">O vencimento do seu aluguel está se aproximando. Faltam apenas <strong>{{ dias_para_vencimento }} dias</strong>!</p>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 12px; padding: 30px; margin: 30px 0; border: 1px solid #e9ecef;">
            <h3 style="color: #495057; margin: 0 0 20px 0; font-size: 22px; text-align: center;">📋 Informações do Pagamento</h3>
            <div style="display: grid; gap: 15px;">
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Imóvel:</span>
                    <span style="color: #6c757d;">{{ imovel_endereco }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Mês de Referência:</span>
                    <span style="color: #6c757d;">{{ mes_referencia }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 2px solid #dee2e6;">
                    <span style="font-weight: 600; color: #495057;">Data de Vencimento:</span>
                    <span style="color: #fd7e14; font-weight: bold;">{{ data_vencimento }}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 15px 0; background: #e3f2fd; margin: 10px -15px -15px -15px; padding: 20px; border-radius: 0 0 8px 8px;">
                    <span style="font-weight: 700; color: #1976d2; font-size: 18px;">Valor a Pagar:</span>
                    <span style="color: #28a745; font-weight: bold; font-size: 24px;">R$ {{ valor_aluguel }}</span>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 40px 0;">
            <a href="#" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block; font-size: 16px; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);">💳 Pagar Antecipadamente</a>
        </div>
        
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-left: 4px solid #28a745; border-radius: 8px; padding: 25px; margin: 30px 0;">
            <h4 style="color: #155724; margin: 0 0 15px 0; font-size: 18px;">💡 Vantagens do Pagamento Antecipado</h4>
            <ul style="margin: 0; padding-left: 20px; color: #155724;">
                <li>Evita multas e juros por atraso</li>
                <li>Mantém seu histórico em dia</li>
                <li>Facilita renovações futuras</li>
                <li>Demonstra responsabilidade financeira</li>
            </ul>
        </div>
    </div>
    
    <div style="background: #343a40; color: #fff; padding: 30px; text-align: center;">
        <p style="margin: 0; font-size: 16px; font-weight: 300;">
            <strong>ImobiPro</strong> - Gestão Imobiliária Profissional<br>
            <span style="opacity: 0.8; font-size: 14px;">Este é um e-mail automático, não responda diretamente.</span>
        </p>
    </div>
</body>
</html>''',
                'formato': 'HTML',
                'variaveis_disponiveis': json.dumps([
                    'inquilino_nome', 'dias_para_vencimento', 'imovel_endereco', 
                    'mes_referencia', 'data_vencimento', 'valor_aluguel'
                ]),
                'preview_dados': json.dumps({
                    'inquilino_nome': 'Maria Santos',
                    'dias_para_vencimento': '5',
                    'imovel_endereco': 'Av. Principal, 456 - Jardins',
                    'mes_referencia': 'Fevereiro/2024',
                    'data_vencimento': '05/02/2024',
                    'valor_aluguel': '2.200,00'
                }),
                'ativo': True,
                'padrao': False
            }
        ]

        # Criar apenas templates que não conflitem
        templates_adicionais = [
            {
                'nome': 'Aviso de Vencimento - 15 dias',
                'categoria': categorias['Vencimento'],
                'tipo': 'VENCIMENTO',
                'assunto_template': 'Lembrete: Vencimento em 15 dias - {{nome_inquilino}}',
                'corpo_template': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1976d2;">Aviso de Vencimento</h2>
                    <p>Prezado(a) <strong>{{nome_inquilino}}</strong>,</p>
                    
                    <p>Seu contrato vence em 15 dias. Entre em contato para renovação.</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>{{nome_imobiliaria}}</strong></p>
                </div>
                ''',
                'formato': 'HTML',
                'variaveis_disponiveis': json.dumps({
                    'nome_inquilino': 'Nome do inquilino',
                    'nome_imobiliaria': 'Nome da imobiliária'
                }),
                'preview_dados': json.dumps({
                    'nome_inquilino': 'Maria Santos',
                    'nome_imobiliaria': 'ImobilPro'
                }),
                'ativo': True,
                'padrao': True  # Será o novo padrão
            }
        ]

        # Primeiro, remover o status padrão dos templates existentes do tipo VENCIMENTO
        TemplateNotificacao.objects.filter(tipo='VENCIMENTO', padrao=True).update(padrao=False)
        
        # Criar novos templates
        templates_criados = 0
        for template_data in templates_adicionais:
            if not TemplateNotificacao.objects.filter(nome=template_data['nome']).exists():
                template = TemplateNotificacao.objects.create(
                    nome=template_data['nome'],
                    categoria=template_data['categoria'],
                    tipo=template_data['tipo'],
                    assunto_template=template_data['assunto_template'],
                    corpo_template=template_data['corpo_template'],
                    formato=template_data['formato'],
                    variaveis_disponiveis=template_data['variaveis_disponiveis'],
                    preview_dados=template_data['preview_dados'],
                    ativo=template_data['ativo'],
                    padrao=template_data['padrao'],
                    usuario_criador=admin_user
                )
                templates_criados += 1
                self.stdout.write(f'✅ Template criado: {template.nome}')
            else:
                self.stdout.write(f'⚠️ Template já existe: {template_data["nome"]}')

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Processo concluído! {templates_criados} templates adicionais criados.')
        )