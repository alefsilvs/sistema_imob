from django.core.management.base import BaseCommand
from security.models import SystemSetting
import json
import logging

try:
    from security.tasks import schedule_backup_tasks
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def schedule_backup_tasks():
        raise ImportError("Celery não está disponível")

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Configura agendamento automático de backups'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Habilita o agendamento de backups',
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Desabilita o agendamento de backups',
        )
        parser.add_argument(
            '--frequency',
            choices=['daily', 'weekly', 'monthly'],
            help='Frequência dos backups (daily, weekly, monthly)',
        )
        parser.add_argument(
            '--time',
            help='Horário para execução (formato HH:MM, ex: 02:00)',
        )
        parser.add_argument(
            '--types',
            nargs='+',
            choices=['database', 'media', 'logs', 'full'],
            help='Tipos de backup a executar',
        )
        parser.add_argument(
            '--max-backups',
            type=int,
            help='Número máximo de backups a manter',
        )
        parser.add_argument(
            '--backup-dir',
            help='Diretório para armazenar backups',
        )
        parser.add_argument(
            '--notification-emails',
            nargs='+',
            help='Emails para receber notificações de backup',
        )
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Mostra configuração atual',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reseta configurações para os valores padrão',
        )
    
    def handle(self, *args, **options):
        if options['show_config']:
            self._show_current_config()
            return
        
        if options['reset']:
            self._reset_config()
            return
        
        # Atualizar configurações
        self._update_backup_schedule(options)
        self._update_backup_settings(options)
        self._update_notification_settings(options)
        
        # Aplicar agendamento se Celery estiver disponível
        if CELERY_AVAILABLE:
            try:
                schedule_backup_tasks()
                self.stdout.write(
                    self.style.SUCCESS('Agendamento de backups configurado com sucesso!')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Configurações salvas, mas erro ao agendar tasks: {e}\n'
                        'Você pode usar cron jobs do sistema operacional como alternativa.'
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Configurações salvas. Celery não está disponível.\n'
                    'Use cron jobs do sistema operacional para agendamento automático.\n'
                    'Execute: python security/cron_backup.py --crontab-examples'
                )
            )
        
        # Mostrar configuração final
        self.stdout.write('\n=== CONFIGURAÇÃO ATUAL ===')
        self._show_current_config()
    
    def _update_backup_schedule(self, options):
        """Atualiza configurações de agendamento"""
        try:
            # Obter configuração atual
            try:
                setting = SystemSetting.objects.get(key='backup_schedule')
                config = json.loads(setting.value)
            except (SystemSetting.DoesNotExist, json.JSONDecodeError):
                config = {
                    'enabled': False,
                    'frequency': 'daily',
                    'time': '02:00',
                    'types': ['full']
                }
            
            # Atualizar com novos valores
            if options['enable']:
                config['enabled'] = True
                self.stdout.write('Agendamento de backups habilitado')
            
            if options['disable']:
                config['enabled'] = False
                self.stdout.write('Agendamento de backups desabilitado')
            
            if options['frequency']:
                config['frequency'] = options['frequency']
                self.stdout.write(f'Frequência definida para: {options["frequency"]}')
            
            if options['time']:
                # Validar formato de horário
                try:
                    hour, minute = options['time'].split(':')
                    hour, minute = int(hour), int(minute)
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        config['time'] = options['time']
                        self.stdout.write(f'Horário definido para: {options["time"]}')
                    else:
                        raise ValueError("Horário inválido")
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR('Formato de horário inválido. Use HH:MM (ex: 02:00)')
                    )
                    return
            
            if options['types']:
                config['types'] = options['types']
                self.stdout.write(f'Tipos de backup: {', '.join(options["types"])}')
            
            # Salvar configuração
            setting, created = SystemSetting.objects.get_or_create(
                key='backup_schedule',
                defaults={'description': 'Configurações de agendamento de backup'}
            )
            setting.value = json.dumps(config)
            setting.save()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao atualizar configurações de agendamento: {e}')
            )
    
    def _update_backup_settings(self, options):
        """Atualiza configurações gerais de backup"""
        try:
            if options['max_backups']:
                setting, created = SystemSetting.objects.get_or_create(
                    key='max_backups',
                    defaults={'description': 'Número máximo de backups a manter'}
                )
                setting.value = str(options['max_backups'])
                setting.save()
                self.stdout.write(f'Máximo de backups definido para: {options["max_backups"]}')
            
            if options['backup_dir']:
                from pathlib import Path
                backup_dir = Path(options['backup_dir'])
                
                # Criar diretório se não existir
                try:
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    
                    setting, created = SystemSetting.objects.get_or_create(
                        key='backup_directory',
                        defaults={'description': 'Diretório para armazenar backups'}
                    )
                    setting.value = str(backup_dir.absolute())
                    setting.save()
                    self.stdout.write(f'Diretório de backup definido para: {backup_dir.absolute()}')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Erro ao criar diretório de backup: {e}')
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao atualizar configurações de backup: {e}')
            )
    
    def _update_notification_settings(self, options):
        """Atualiza configurações de notificação"""
        try:
            if options['notification_emails']:
                # Validar emails
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                
                valid_emails = []
                for email in options['notification_emails']:
                    try:
                        validate_email(email)
                        valid_emails.append(email)
                    except ValidationError:
                        self.stdout.write(
                            self.style.WARNING(f'Email inválido ignorado: {email}')
                        )
                
                if valid_emails:
                    config = {
                        'enabled': True,
                        'emails': valid_emails
                    }
                    
                    setting, created = SystemSetting.objects.get_or_create(
                        key='backup_notifications',
                        defaults={'description': 'Configurações de notificação de backup'}
                    )
                    setting.value = json.dumps(config)
                    setting.save()
                    
                    self.stdout.write(
                        f'Notificações configuradas para: {', '.join(valid_emails)}'
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Nenhum email válido fornecido')
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao atualizar configurações de notificação: {e}')
            )
    
    def _show_current_config(self):
        """Mostra configuração atual"""
        try:
            # Configurações de agendamento
            try:
                setting = SystemSetting.objects.get(key='backup_schedule')
                schedule_config = json.loads(setting.value)
            except (SystemSetting.DoesNotExist, json.JSONDecodeError):
                schedule_config = {'enabled': False}
            
            self.stdout.write("AGENDAMENTO:")
            self.stdout.write(f"  Habilitado: {'Sim' if schedule_config.get('enabled') else 'Não'}")
            self.stdout.write(f"  Frequência: {schedule_config.get('frequency', 'N/A')}")
            self.stdout.write(f"  Horário: {schedule_config.get('time', 'N/A')}")
            self.stdout.write(f"  Tipos: {', '.join(schedule_config.get('types', []))}")
            
            # Configurações gerais
            try:
                max_backups = SystemSetting.objects.get(key='max_backups').value
            except SystemSetting.DoesNotExist:
                max_backups = '30 (padrão)'
            
            try:
                backup_dir = SystemSetting.objects.get(key='backup_directory').value
            except SystemSetting.DoesNotExist:
                backup_dir = 'backups/ (padrão)'
            
            self.stdout.write("\nCONFIGURAÇÕES GERAIS:")
            self.stdout.write(f"  Máximo de backups: {max_backups}")
            self.stdout.write(f"  Diretório: {backup_dir}")
            
            # Configurações de notificação
            try:
                setting = SystemSetting.objects.get(key='backup_notifications')
                notification_config = json.loads(setting.value)
                
                self.stdout.write("\nNOTIFICAÇÕES:")
                self.stdout.write(f"  Habilitadas: {'Sim' if notification_config.get('enabled') else 'Não'}")
                emails = notification_config.get('emails', [])
                if emails:
                    self.stdout.write(f"  Emails: {', '.join(emails)}")
                else:
                    self.stdout.write("  Emails: Nenhum configurado")
                    
            except (SystemSetting.DoesNotExist, json.JSONDecodeError):
                self.stdout.write("\nNOTIFICAÇÕES: Não configuradas")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao mostrar configuração: {e}')
            )
    
    def _reset_config(self):
        """Reseta configurações para valores padrão"""
        try:
            self.stdout.write('Resetando configurações de backup...')
            
            # Remover configurações existentes
            SystemSetting.objects.filter(
                key__in=['backup_schedule', 'max_backups', 'backup_directory', 'backup_notifications']
            ).delete()
            
            # Criar configurações padrão
            default_schedule = {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00',
                'types': ['full']
            }
            
            SystemSetting.objects.create(
                key='backup_schedule',
                value=json.dumps(default_schedule),
                description='Configurações de agendamento de backup'
            )
            
            SystemSetting.objects.create(
                key='max_backups',
                value='30',
                description='Número máximo de backups a manter'
            )
            
            self.stdout.write(
                self.style.SUCCESS('Configurações resetadas para valores padrão')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao resetar configurações: {e}')
            )