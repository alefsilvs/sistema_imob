from django.core.management.base import BaseCommand
from saas.models import PlanoComercial

class Command(BaseCommand):
    help = 'Cria o plano de trial gratuito de 30 dias'
    
    def handle(self, *args, **options):
        # Verificar se já existe um plano de trial
        trial_plan, created = PlanoComercial.objects.get_or_create(
            tipo='trial',
            defaults={
                'nome': 'Trial Gratuito - 7 dias',
                'preco_mensal': 0,
                'preco_anual': 0,
                'max_usuarios': 2,
                'max_imoveis': 50,
                'max_contratos': 25,
                'storage_gb': 2,
                'api_calls_mes': 500,
                'suporte_prioritario': False,
                'backup_automatico': False,
                'subdominio_personalizado': False,
                'is_trial': True,
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Plano de trial criado com sucesso: {trial_plan.nome}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Plano de trial já existe: {trial_plan.nome}'
                )
            )
            
        # Atualizar plano existente se necessário
        if not trial_plan.is_trial:
            trial_plan.is_trial = True
            trial_plan.save()
            self.stdout.write(
                self.style.SUCCESS(
                    'Plano de trial atualizado com flag is_trial=True'
                )
            )