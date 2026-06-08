import os
import json
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.core.mail import send_mail
from django.utils import timezone
from .models import SystemSetting
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """
    Gerenciador de backup automático do sistema
    """
    
    def __init__(self):
        self.backup_dir = self._get_backup_directory()
        self.max_backups = self._get_max_backups()
        self.backup_types = ['database', 'media', 'logs', 'full']
        
    def _get_backup_directory(self):
        """Obtém diretório de backup das configurações"""
        try:
            setting = SystemSetting.objects.get(key='backup_directory')
            return Path(setting.value)
        except SystemSetting.DoesNotExist:
            # Diretório padrão
            default_dir = Path(settings.BASE_DIR) / 'backups'
            default_dir.mkdir(exist_ok=True)
            return default_dir
    
    def _get_max_backups(self):
        """Obtém número máximo de backups a manter"""
        try:
            setting = SystemSetting.objects.get(key='max_backups')
            return int(setting.value)
        except (SystemSetting.DoesNotExist, ValueError):
            return 30  # Padrão: 30 backups
    
    def _get_backup_schedule(self):
        """Obtém configuração de agendamento"""
        try:
            setting = SystemSetting.objects.get(key='backup_schedule')
            return json.loads(setting.value)
        except (SystemSetting.DoesNotExist, json.JSONDecodeError):
            return {
                'enabled': True,
                'frequency': 'daily',  # daily, weekly, monthly
                'time': '02:00',  # Horário para execução
                'types': ['database', 'media']  # Tipos de backup
            }
    
    def create_database_backup(self):
        """Cria backup do banco de dados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'database_backup_{timestamp}.json'
        
        try:
            logger.info(f"Iniciando backup do banco de dados: {backup_file}")
            
            # Usar dumpdata do Django para backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                call_command('dumpdata', 
                           '--natural-foreign', 
                           '--natural-primary',
                           '--exclude=contenttypes',
                           '--exclude=auth.permission',
                           '--exclude=sessions.session',
                           stdout=f)
            
            # Comprimir o arquivo
            compressed_file = backup_file.with_suffix('.json.gz')
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remover arquivo não comprimido
            backup_file.unlink()
            
            logger.info(f"Backup do banco de dados criado: {compressed_file}")
            return compressed_file
            
        except Exception as e:
            logger.error(f"Erro ao criar backup do banco de dados: {e}")
            if backup_file.exists():
                backup_file.unlink()
            raise
    
    def create_media_backup(self):
        """Cria backup dos arquivos de mídia"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'media_backup_{timestamp}.tar.gz'
        
        try:
            logger.info(f"Iniciando backup de mídia: {backup_file}")
            
            media_root = Path(settings.MEDIA_ROOT)
            if not media_root.exists():
                logger.warning("Diretório de mídia não existe")
                return None
            
            # Criar arquivo tar.gz
            import tarfile
            with tarfile.open(backup_file, 'w:gz') as tar:
                tar.add(media_root, arcname='media')
            
            logger.info(f"Backup de mídia criado: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de mídia: {e}")
            if backup_file.exists():
                backup_file.unlink()
            raise
    
    def create_logs_backup(self):
        """Cria backup dos logs do sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'logs_backup_{timestamp}.tar.gz'
        
        try:
            logger.info(f"Iniciando backup de logs: {backup_file}")
            
            # Diretórios de logs
            log_dirs = [
                Path(settings.BASE_DIR) / 'logs',
                Path('/var/log/django'),  # Log padrão do sistema
            ]
            
            import tarfile
            with tarfile.open(backup_file, 'w:gz') as tar:
                for log_dir in log_dirs:
                    if log_dir.exists():
                        tar.add(log_dir, arcname=f'logs/{log_dir.name}')
            
            logger.info(f"Backup de logs criado: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de logs: {e}")
            if backup_file.exists():
                backup_file.unlink()
            raise
    
    def create_full_backup(self):
        """Cria backup completo do sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backups = {
            'database': None,
            'media': None,
            'logs': None,
            'timestamp': timestamp
        }
        
        try:
            logger.info("Iniciando backup completo do sistema")
            
            # Criar backups individuais
            backups['database'] = self.create_database_backup()
            backups['media'] = self.create_media_backup()
            backups['logs'] = self.create_logs_backup()
            
            # Criar manifesto do backup
            manifest_file = self.backup_dir / f'backup_manifest_{timestamp}.json'
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': timestamp,
                    'created_at': timezone.now().isoformat(),
                    'type': 'full',
                    'files': {
                        'database': str(backups['database']) if backups['database'] else None,
                        'media': str(backups['media']) if backups['media'] else None,
                        'logs': str(backups['logs']) if backups['logs'] else None,
                    },
                    'system_info': {
                        'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
                        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                        'backup_version': '1.0'
                    }
                }, f, indent=2)
            
            logger.info(f"Backup completo criado com manifesto: {manifest_file}")
            return manifest_file
            
        except Exception as e:
            logger.error(f"Erro ao criar backup completo: {e}")
            raise
    
    def cleanup_old_backups(self):
        """Remove backups antigos baseado na configuração"""
        try:
            logger.info("Iniciando limpeza de backups antigos")
            
            # Listar todos os arquivos de backup
            backup_files = []
            for pattern in ['database_backup_*.json.gz', 'media_backup_*.tar.gz', 
                          'logs_backup_*.tar.gz', 'backup_manifest_*.json']:
                backup_files.extend(self.backup_dir.glob(pattern))
            
            # Ordenar por data de modificação (mais antigos primeiro)
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remover backups excedentes
            if len(backup_files) > self.max_backups:
                files_to_remove = backup_files[:-self.max_backups]
                for file_path in files_to_remove:
                    logger.info(f"Removendo backup antigo: {file_path}")
                    file_path.unlink()
            
            logger.info(f"Limpeza concluída. Mantidos {min(len(backup_files), self.max_backups)} backups")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
    
    def restore_database_backup(self, backup_file):
        """Restaura backup do banco de dados"""
        try:
            logger.info(f"Iniciando restauração do banco de dados: {backup_file}")
            
            backup_path = Path(backup_file)
            if not backup_path.exists():
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_file}")
            
            # Descomprimir se necessário
            if backup_path.suffix == '.gz':
                temp_file = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file = temp_file
            
            # Restaurar usando loaddata
            call_command('loaddata', str(backup_file))
            
            # Limpar arquivo temporário se foi criado
            if backup_path.suffix == '.gz' and temp_file.exists():
                temp_file.unlink()
            
            logger.info("Restauração do banco de dados concluída")
            
        except Exception as e:
            logger.error(f"Erro na restauração do banco de dados: {e}")
            raise
    
    def get_backup_status(self):
        """Retorna status dos backups"""
        try:
            backup_files = list(self.backup_dir.glob('backup_manifest_*.json'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            status = {
                'backup_directory': str(self.backup_dir),
                'total_backups': len(backup_files),
                'max_backups': self.max_backups,
                'last_backup': None,
                'disk_usage': self._get_backup_disk_usage(),
                'schedule': self._get_backup_schedule()
            }
            
            if backup_files:
                last_backup_file = backup_files[0]
                with open(last_backup_file, 'r', encoding='utf-8') as f:
                    last_backup_data = json.load(f)
                
                status['last_backup'] = {
                    'timestamp': last_backup_data.get('timestamp'),
                    'created_at': last_backup_data.get('created_at'),
                    'type': last_backup_data.get('type'),
                    'files': last_backup_data.get('files', {})
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao obter status dos backups: {e}")
            return {'error': str(e)}
    
    def _get_backup_disk_usage(self):
        """Calcula uso de disco dos backups"""
        try:
            total_size = 0
            for file_path in self.backup_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            # Converter para MB
            return round(total_size / (1024 * 1024), 2)
            
        except Exception:
            return 0
    
    def send_backup_notification(self, backup_type, success=True, error_message=None):
        """Envia notificação sobre status do backup"""
        try:
            # Verificar se notificações estão habilitadas
            try:
                notification_setting = SystemSetting.objects.get(key='backup_notifications')
                notification_config = json.loads(notification_setting.value)
                if not notification_config.get('enabled', False):
                    return
            except (SystemSetting.DoesNotExist, json.JSONDecodeError):
                return
            
            subject = f"Backup {backup_type} - {'Sucesso' if success else 'Falha'}"
            
            if success:
                message = f"O backup do tipo '{backup_type}' foi concluído com sucesso em {timezone.now().strftime('%d/%m/%Y às %H:%M')}."
            else:
                message = f"O backup do tipo '{backup_type}' falhou em {timezone.now().strftime('%d/%m/%Y às %H:%M')}.\n\nErro: {error_message}"
            
            # Obter emails para notificação
            recipient_emails = notification_config.get('emails', [])
            if recipient_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_emails,
                    fail_silently=True
                )
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de backup: {e}")


# Instância global do gerenciador de backup
backup_manager = BackupManager()