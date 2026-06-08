from django.core.management.base import BaseCommand
from django.utils import timezone
from security.backup import backup_manager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Executa backup do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['database', 'media', 'logs', 'full'],
            default='full',
            help='Tipo de backup a ser executado (padrão: full)',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove backups antigos após criar o novo backup',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Envia notificação por email sobre o status do backup',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostra apenas o status dos backups sem executar backup',
        )
    
    def handle(self, *args, **options):
        backup_type = options['type']
        cleanup = options['cleanup']
        notify = options['notify']
        show_status = options['status']
        
        if show_status:
            self._show_backup_status()
            return
        
        self.stdout.write(f'Iniciando backup do tipo: {backup_type}')
        
        try:
            start_time = timezone.now()
            
            # Executar backup baseado no tipo
            if backup_type == 'database':
                result = backup_manager.create_database_backup()
            elif backup_type == 'media':
                result = backup_manager.create_media_backup()
            elif backup_type == 'logs':
                result = backup_manager.create_logs_backup()
            elif backup_type == 'full':
                result = backup_manager.create_full_backup()
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Backup {backup_type} concluído com sucesso!\n'
                        f'Arquivo: {result}\n'
                        f'Duração: {duration:.2f} segundos'
                    )
                )
                
                # Enviar notificação de sucesso
                if notify:
                    backup_manager.send_backup_notification(backup_type, success=True)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Backup {backup_type} não gerou arquivo de saída')
                )
            
            # Limpeza de backups antigos
            if cleanup:
                self.stdout.write('Executando limpeza de backups antigos...')
                backup_manager.cleanup_old_backups()
                self.stdout.write(self.style.SUCCESS('Limpeza concluída!'))
            
        except Exception as e:
            error_message = str(e)
            self.stdout.write(
                self.style.ERROR(f'Erro ao executar backup {backup_type}: {error_message}')
            )
            
            # Enviar notificação de erro
            if notify:
                backup_manager.send_backup_notification(
                    backup_type, 
                    success=False, 
                    error_message=error_message
                )
            
            # Re-raise para que o comando falhe
            raise
    
    def _show_backup_status(self):
        """Mostra status detalhado dos backups"""
        self.stdout.write(self.style.HTTP_INFO('=== STATUS DOS BACKUPS ==='))
        
        try:
            status = backup_manager.get_backup_status()
            
            if 'error' in status:
                self.stdout.write(self.style.ERROR(f'Erro ao obter status: {status["error"]}'))
                return
            
            self.stdout.write(f"Diretório de backup: {status['backup_directory']}")
            self.stdout.write(f"Total de backups: {status['total_backups']}")
            self.stdout.write(f"Máximo de backups: {status['max_backups']}")
            self.stdout.write(f"Uso de disco: {status['disk_usage']} MB")
            
            # Informações do último backup
            if status['last_backup']:
                last = status['last_backup']
                self.stdout.write("\n=== ÚLTIMO BACKUP ===")
                self.stdout.write(f"Timestamp: {last['timestamp']}")
                self.stdout.write(f"Criado em: {last['created_at']}")
                self.stdout.write(f"Tipo: {last['type']}")
                
                if last['files']:
                    self.stdout.write("Arquivos:")
                    for file_type, file_path in last['files'].items():
                        if file_path:
                            self.stdout.write(f"  - {file_type}: {file_path}")
                        else:
                            self.stdout.write(f"  - {file_type}: não criado")
            else:
                self.stdout.write("\nNenhum backup encontrado.")
            
            # Configurações de agendamento
            schedule = status.get('schedule', {})
            if schedule:
                self.stdout.write("\n=== CONFIGURAÇÃO DE AGENDAMENTO ===")
                self.stdout.write(f"Habilitado: {'Sim' if schedule.get('enabled') else 'Não'}")
                self.stdout.write(f"Frequência: {schedule.get('frequency', 'N/A')}")
                self.stdout.write(f"Horário: {schedule.get('time', 'N/A')}")
                self.stdout.write(f"Tipos: {', '.join(schedule.get('types', []))}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao mostrar status: {e}'))