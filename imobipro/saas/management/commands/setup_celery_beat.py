from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Configura as tarefas periódicas do Celery para o sistema de trial'

    def handle(self, *args, **options):
        self.stdout.write('Configurando tarefas periódicas do Celery...')
        
        # Criar schedule para verificação diária (a cada 24 horas)
        schedule_diario, created = IntervalSchedule.objects.get_or_create(
            every=24,
            period=IntervalSchedule.HOURS,
        )
        
        # Criar schedule para verificação a cada 6 horas
        schedule_6h, created = IntervalSchedule.objects.get_or_create(
            every=6,
            period=IntervalSchedule.HOURS,
        )
        
        # Criar schedule para verificação a cada hora
        schedule_1h, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )
        
        # Tarefa para verificar trials expirando (a cada 6 horas)
        task_verificar_trials, created = PeriodicTask.objects.get_or_create(
            name='Verificar trials expirando',
            defaults={
                'task': 'saas.tasks.verificar_trials_expirando',
                'interval': schedule_6h,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Tarefa "Verificar trials expirando" criada'))
        else:
            self.stdout.write('• Tarefa "Verificar trials expirando" já existe')
        
        # Tarefa para suspender trials expirados (a cada hora)
        task_suspender_trials, created = PeriodicTask.objects.get_or_create(
            name='Suspender trials expirados',
            defaults={
                'task': 'saas.tasks.suspender_trials_expirados',
                'interval': schedule_1h,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Tarefa "Suspender trials expirados" criada'))
        else:
            self.stdout.write('• Tarefa "Suspender trials expirados" já existe')
        
        # Tarefa para relatório diário (todo dia às 9h - aproximadamente)
        task_relatorio, created = PeriodicTask.objects.get_or_create(
            name='Relatório diário de trials',
            defaults={
                'task': 'saas.tasks.relatorio_diario_trials',
                'interval': schedule_diario,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Tarefa "Relatório diário de trials" criada'))
        else:
            self.stdout.write('• Tarefa "Relatório diário de trials" já existe')
        
        # Tarefa para limpeza de dados antigos (semanal)
        schedule_semanal, created = IntervalSchedule.objects.get_or_create(
            every=7,
            period=IntervalSchedule.DAYS,
        )
        
        task_limpeza, created = PeriodicTask.objects.get_or_create(
            name='Limpeza de dados antigos',
            defaults={
                'task': 'saas.tasks.limpeza_dados_antigos',
                'interval': schedule_semanal,
                'enabled': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Tarefa "Limpeza de dados antigos" criada'))
        else:
            self.stdout.write('• Tarefa "Limpeza de dados antigos" já existe')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Configuração das tarefas periódicas concluída!'))
        self.stdout.write('\nTarefas configuradas:')
        self.stdout.write('• Verificar trials expirando: a cada 6 horas')
        self.stdout.write('• Suspender trials expirados: a cada 1 hora')
        self.stdout.write('• Relatório diário de trials: a cada 24 horas')
        self.stdout.write('• Limpeza de dados antigos: a cada 7 dias')
        self.stdout.write('\nPara iniciar o Celery Beat, execute:')
        self.stdout.write('celery -A sistema_imobiliario beat -l info')