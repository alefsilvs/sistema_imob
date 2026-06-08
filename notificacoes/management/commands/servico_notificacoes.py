from django.core.management.base import BaseCommand
import time
import schedule
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Executa como serviço para processar notificações'
    
    def handle(self, *args, **options):
        # Agendar execução a cada 5 minutos
        schedule.every(5).minutes.do(self.processar_notificacoes)
        
        self.stdout.write('Serviço de notificações iniciado...')
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    
    def processar_notificacoes(self):
        try:
            call_command('processar_notificacoes')
            self.stdout.write(f'Processamento executado em {time.strftime("%Y-%m-%d %H:%M:%S")}')
        except Exception as e:
            self.stdout.write(f'Erro no processamento: {e}')