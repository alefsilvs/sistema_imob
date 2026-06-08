from django.core.management.base import BaseCommand
from assinaturas.models import PlanoAssinatura, ConfiguracaoSistema
from decimal import Decimal

class Command(BaseCommand):
    help = 'Inicializa os planos de assinatura padrão'
    
    def handle(self, *args, **options):
        self.stdout.write('Inicializando planos de assinatura...')
        
        # Criar planos se não existirem
        planos_data = [
            {
                'nome': 'Básico',
                'descricao': 'Ideal para pequenas imobiliárias - Suporte por email, Relatórios básicos, Backup diário',
                'tipo': 'MENSAL',
                'preco': Decimal('49.90'),
                'duracao_dias': 30,
                'max_imoveis': 50,
                'max_contratos': 20,
                'max_usuarios': 1,
                'ativo': True
            },
            {
                'nome': 'Profissional',
                'descricao': 'Para imobiliárias em crescimento - Suporte prioritário, Relatórios avançados, Integração WhatsApp, Backup em tempo real, API completa',
                'tipo': 'MENSAL',
                'preco': Decimal('99.90'),
                'duracao_dias': 30,
                'max_imoveis': 200,
                'max_contratos': 100,
                'max_usuarios': 3,
                'ativo': True
            },
            {
                'nome': 'Empresarial',
                'descricao': 'Para grandes imobiliárias - Suporte 24/7, Relatórios personalizados, Múltiplas integrações, Gerente de conta dedicado, Treinamento personalizado',
                'tipo': 'MENSAL',
                'preco': Decimal('199.90'),
                'duracao_dias': 30,
                'max_imoveis': 1000,
                'max_contratos': 500,
                'max_usuarios': 10,
                'ativo': True
            },
            {
                'nome': 'Trial Gratuito',
                'descricao': 'Teste gratuito por 7 dias com acesso completo',
                'tipo': 'TRIAL',
                'preco': Decimal('0.00'),
                'duracao_dias': 7,
                'max_imoveis': 10,
                'max_contratos': 5,
                'max_usuarios': 1,
                'ativo': True
            }
        ]
        
        for plano_data in planos_data:
            plano, created = PlanoAssinatura.objects.get_or_create(
                nome=plano_data['nome'],
                defaults=plano_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Plano "{plano.nome}" criado com sucesso!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Plano "{plano.nome}" já existe.')
                )
        
        # Criar configuração do sistema
        config, created = ConfiguracaoSistema.objects.get_or_create(
            defaults={
                'trial_dias': 7,
                'permitir_trial': True,
                'bloquear_acesso_vencido': True,
                'dias_graca': 3,
                'email_cobranca': 'admin@imobilpro.com',
                'mensagem_bloqueio': 'Sua assinatura expirou. Renove para continuar usando o sistema.'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Configuração do sistema criada!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Configuração do sistema já existe.')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Inicialização concluída com sucesso!')
        )