try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Mock decorator para quando Celery não estiver disponível
    def shared_task(bind=False, max_retries=3):
        def decorator(func):
            return func
        return decorator

from django.core.management import call_command
from django.utils import timezone
from .backup import backup_manager
from .models import SystemSetting
import json
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_scheduled_backup(self, backup_type='full'):
    """
    Task Celery para executar backup agendado
    """
    try:
        logger.info(f"Iniciando backup agendado do tipo: {backup_type}")
        
        # Executar backup baseado no tipo
        if backup_type == 'database':
            result = backup_manager.create_database_backup()
        elif backup_type == 'media':
            result = backup_manager.create_media_backup()
        elif backup_type == 'logs':
            result = backup_manager.create_logs_backup()
        elif backup_type == 'full':
            result = backup_manager.create_full_backup()
        else:
            raise ValueError(f"Tipo de backup inválido: {backup_type}")
        
        # Limpeza automática de backups antigos
        backup_manager.cleanup_old_backups()
        
        # Enviar notificação de sucesso
        backup_manager.send_backup_notification(backup_type, success=True)
        
        logger.info(f"Backup agendado {backup_type} concluído com sucesso: {result}")
        return f"Backup {backup_type} concluído: {result}"
        
    except Exception as exc:
        logger.error(f"Erro no backup agendado {backup_type}: {exc}")
        
        # Enviar notificação de erro
        backup_manager.send_backup_notification(
            backup_type, 
            success=False, 
            error_message=str(exc)
        )
        
        # Retry com backoff exponencial
        if self.request.retries < self.max_retries:
            logger.info(f"Tentativa {self.request.retries + 1} de {self.max_retries + 1}")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        raise exc

@shared_task
def cleanup_old_backups():
    """
    Task para limpeza de backups antigos
    """
    try:
        logger.info("Iniciando limpeza automática de backups antigos")
        backup_manager.cleanup_old_backups()
        logger.info("Limpeza de backups concluída")
        return "Limpeza de backups concluída"
        
    except Exception as exc:
        logger.error(f"Erro na limpeza de backups: {exc}")
        raise exc

@shared_task
def verify_backup_integrity():
    """
    Task para verificar integridade dos backups
    """
    try:
        logger.info("Iniciando verificação de integridade dos backups")
        
        status = backup_manager.get_backup_status()
        
        # Verificar se há backups recentes
        if status.get('total_backups', 0) == 0:
            logger.warning("Nenhum backup encontrado")
            return "Aviso: Nenhum backup encontrado"
        
        # Verificar último backup
        last_backup = status.get('last_backup')
        if last_backup:
            from datetime import datetime, timedelta
            
            # Converter string ISO para datetime
            created_at_str = last_backup.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    now = timezone.now()
                    
                    # Verificar se o último backup é muito antigo (mais de 7 dias)
                    if (now - created_at).days > 7:
                        logger.warning(f"Último backup é muito antigo: {created_at}")
                        return f"Aviso: Último backup é de {created_at.strftime('%d/%m/%Y')}"
                    
                except ValueError as e:
                    logger.error(f"Erro ao parsear data do backup: {e}")
        
        logger.info("Verificação de integridade concluída")
        return "Verificação de integridade concluída com sucesso"
        
    except Exception as exc:
        logger.error(f"Erro na verificação de integridade: {exc}")
        raise exc

def schedule_backup_tasks():
    """
    Função para agendar tasks de backup baseado nas configurações
    """
    try:
        # Obter configurações de agendamento
        try:
            setting = SystemSetting.objects.get(key='backup_schedule')
            schedule_config = json.loads(setting.value)
        except (SystemSetting.DoesNotExist, json.JSONDecodeError):
            logger.info("Configuração de agendamento não encontrada, usando padrões")
            return
        
        if not schedule_config.get('enabled', False):
            logger.info("Agendamento de backup está desabilitado")
            return
        
        frequency = schedule_config.get('frequency', 'daily')
        backup_types = schedule_config.get('types', ['full'])
        
        # Agendar tasks baseado na frequência
        from celery.schedules import crontab
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        
        # Remover tasks antigas
        PeriodicTask.objects.filter(name__startswith='backup_').delete()
        
        # Criar nova programação
        if frequency == 'daily':
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,  # 2:00 AM
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
            )
        elif frequency == 'weekly':
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,  # 2:00 AM
                day_of_week=1,  # Segunda-feira
                day_of_month='*',
                month_of_year='*',
            )
        elif frequency == 'monthly':
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=2,  # 2:00 AM
                day_of_week='*',
                day_of_month=1,  # Primeiro dia do mês
                month_of_year='*',
            )
        else:
            logger.error(f"Frequência de backup inválida: {frequency}")
            return
        
        # Criar task para cada tipo de backup
        for backup_type in backup_types:
            PeriodicTask.objects.create(
                crontab=schedule,
                name=f'backup_{backup_type}_{frequency}',
                task='security.tasks.execute_scheduled_backup',
                args=json.dumps([backup_type]),
                enabled=True,
            )
        
        # Agendar limpeza semanal
        cleanup_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=30,
            hour=3,  # 3:30 AM
            day_of_week=0,  # Domingo
            day_of_month='*',
            month_of_year='*',
        )
        
        PeriodicTask.objects.create(
            crontab=cleanup_schedule,
            name='backup_cleanup_weekly',
            task='security.tasks.cleanup_old_backups',
            enabled=True,
        )
        
        # Agendar verificação de integridade diária
        integrity_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=6,  # 6:00 AM
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        PeriodicTask.objects.create(
            crontab=integrity_schedule,
            name='backup_integrity_check_daily',
            task='security.tasks.verify_backup_integrity',
            enabled=True,
        )
        
        logger.info(f"Tasks de backup agendadas com frequência: {frequency}")
        
    except Exception as e:
        logger.error(f"Erro ao agendar tasks de backup: {e}")
        raise

# Função alternativa para sistemas sem Celery
def simple_backup_scheduler():
    """
    Agendador simples de backup para sistemas sem Celery
    Pode ser chamado via cron job do sistema operacional
    """
    try:
        logger.info("Executando backup via agendador simples")
        
        # Obter configurações
        try:
            setting = SystemSetting.objects.get(key='backup_schedule')
            schedule_config = json.loads(setting.value)
        except (SystemSetting.DoesNotExist, json.JSONDecodeError):
            schedule_config = {
                'enabled': True,
                'types': ['full']
            }
        
        if not schedule_config.get('enabled', False):
            logger.info("Backup agendado está desabilitado")
            return
        
        backup_types = schedule_config.get('types', ['full'])
        
        # Executar backups
        for backup_type in backup_types:
            try:
                if backup_type == 'database':
                    result = backup_manager.create_database_backup()
                elif backup_type == 'media':
                    result = backup_manager.create_media_backup()
                elif backup_type == 'logs':
                    result = backup_manager.create_logs_backup()
                elif backup_type == 'full':
                    result = backup_manager.create_full_backup()
                
                logger.info(f"Backup {backup_type} concluído: {result}")
                backup_manager.send_backup_notification(backup_type, success=True)
                
            except Exception as e:
                logger.error(f"Erro no backup {backup_type}: {e}")
                backup_manager.send_backup_notification(
                    backup_type, 
                    success=False, 
                    error_message=str(e)
                )
        
        # Limpeza
        backup_manager.cleanup_old_backups()
        
        logger.info("Backup agendado concluído")
        
    except Exception as e:
        logger.error(f"Erro no agendador simples de backup: {e}")
        raise