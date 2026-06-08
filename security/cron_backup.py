#!/usr/bin/env python
"""
Script para execução de backups via cron jobs do sistema operacional.
Este script pode ser usado quando o Celery não está disponível.

Exemplos de uso no crontab:
# Backup completo diário às 2:00
0 2 * * * /path/to/python /path/to/projeto/security/cron_backup.py --type full

# Backup de banco de dados a cada 6 horas
0 */6 * * * /path/to/python /path/to/projeto/security/cron_backup.py --type database

# Limpeza de backups antigos semanalmente
0 3 * * 0 /path/to/python /path/to/projeto/security/cron_backup.py --cleanup
"""

import os
import sys
import django
import argparse
import logging
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from security.backup import BackupManager
from security.models import SystemSetting
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_cron.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_backup_config():
    """Obtém configurações de backup do banco de dados"""
    try:
        # Configurações de agendamento
        try:
            setting = SystemSetting.objects.get(key='backup_schedule')
            schedule_config = json.loads(setting.value)
        except (SystemSetting.DoesNotExist, json.JSONDecodeError):
            schedule_config = {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00',
                'types': ['full']
            }
        
        # Diretório de backup
        try:
            backup_dir = SystemSetting.objects.get(key='backup_directory').value
        except SystemSetting.DoesNotExist:
            backup_dir = 'backups'
        
        # Máximo de backups
        try:
            max_backups = int(SystemSetting.objects.get(key='max_backups').value)
        except (SystemSetting.DoesNotExist, ValueError):
            max_backups = 30
        
        # Configurações de notificação
        try:
            setting = SystemSetting.objects.get(key='backup_notifications')
            notification_config = json.loads(setting.value)
        except (SystemSetting.DoesNotExist, json.JSONDecodeError):
            notification_config = {'enabled': False, 'emails': []}
        
        return {
            'schedule': schedule_config,
            'backup_dir': backup_dir,
            'max_backups': max_backups,
            'notifications': notification_config
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter configurações: {e}")
        return {
            'schedule': {'enabled': True, 'types': ['full']},
            'backup_dir': 'backups',
            'max_backups': 30,
            'notifications': {'enabled': False, 'emails': []}
        }

def execute_backup(backup_type, config):
    """Executa backup do tipo especificado"""
    try:
        logger.info(f"Iniciando backup do tipo: {backup_type}")
        
        # Inicializar gerenciador de backup
        backup_manager = BackupManager()
        
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
        
        if result:
            logger.info(f"Backup concluído com sucesso: {result}")
            
            # Enviar notificação se configurado
            if config['notifications']['enabled']:
                send_notification(
                    config['notifications']['emails'],
                    f"Backup {backup_type} concluído",
                    f"Backup realizado com sucesso: {result}"
                )
        else:
            logger.error(f"Falha no backup: Nenhum arquivo criado")
            
            # Enviar notificação de erro se configurado
            if config['notifications']['enabled']:
                send_notification(
                    config['notifications']['emails'],
                    f"Falha no backup {backup_type}",
                    f"Erro durante o backup: Nenhum arquivo criado"
                )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro durante execução do backup: {e}")
        
        # Enviar notificação de erro se configurado
        if config['notifications']['enabled']:
            send_notification(
                config['notifications']['emails'],
                f"Erro crítico no backup {backup_type}",
                f"Erro crítico durante o backup: {str(e)}"
            )
        
        return {'success': False, 'error': str(e)}

def cleanup_old_backups(config):
    """Remove backups antigos"""
    try:
        logger.info("Iniciando limpeza de backups antigos")
        
        backup_manager = BackupManager()
        
        backup_manager.cleanup_old_backups()
        
        logger.info("Limpeza de backups concluída")
        
        if config['notifications']['enabled']:
            send_notification(
                config['notifications']['emails'],
                "Limpeza de backups concluída",
                "Limpeza de backups antigos executada com sucesso"
            )
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Erro durante limpeza de backups: {e}")
        return {'success': False, 'error': str(e)}

def send_notification(emails, subject, message):
    """Envia notificação por email"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        if not emails:
            return
        
        send_mail(
            subject=f"[Sistema Imobiliário] {subject}",
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'sistema@exemplo.com'),
            recipient_list=emails,
            fail_silently=False
        )
        
        logger.info(f"Notificação enviada para: {', '.join(emails)}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {e}")

def get_backup_status(config):
    """Obtém status dos backups"""
    try:
        backup_manager = BackupManager()
        
        status = backup_manager.get_backup_status()
        
        print("=== STATUS DOS BACKUPS ===")
        print(f"Diretório: {status['backup_directory']}")
        print(f"Total de backups: {status['total_backups']}")
        print(f"Máximo de backups: {status['max_backups']}")
        print(f"Espaço usado: {status['disk_usage']:.2f} MB")
        
        if status['last_backup']:
            print("\nÚltimo backup:")
            print(f"  Tipo: {status['last_backup']['type']}")
            print(f"  Data: {status['last_backup']['timestamp']}")
            if status['last_backup']['files']:
                print("  Arquivos:")
                for file_type, file_path in status['last_backup']['files'].items():
                    print(f"    {file_type}: {file_path}")
        else:
            print("\nNenhum backup encontrado")
            
        if status.get('schedule'):
            schedule = status['schedule']
            print(f"\nAgendamento:")
            print(f"  Habilitado: {schedule.get('enabled', False)}")
            print(f"  Frequência: {schedule.get('frequency', 'N/A')}")
            print(f"  Horário: {schedule.get('time', 'N/A')}")
            print(f"  Tipo: {schedule.get('backup_type', 'N/A')}")
        
        return status
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return None

def generate_crontab_examples():
    """Gera exemplos de configuração para crontab"""
    script_path = Path(__file__).absolute()
    python_path = sys.executable
    
    examples = f"""
# Exemplos de configuração para crontab
# Edite com: crontab -e

# Backup completo diário às 2:00
0 2 * * * {python_path} {script_path} --type full

# Backup de banco de dados a cada 6 horas
0 */6 * * * {python_path} {script_path} --type database

# Backup de mídia diário às 3:00
0 3 * * * {python_path} {script_path} --type media

# Backup de logs diário às 4:00
0 4 * * * {python_path} {script_path} --type logs

# Limpeza de backups antigos semanalmente (domingo às 5:00)
0 5 * * 0 {python_path} {script_path} --cleanup

# Verificação de status diária às 6:00
0 6 * * * {python_path} {script_path} --status

# Para redirecionar logs para arquivo:
0 2 * * * {python_path} {script_path} --type full >> /var/log/backup_cron.log 2>&1
"""
    
    print(examples)
    return examples

def main():
    parser = argparse.ArgumentParser(
        description='Script de backup para execução via cron',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python cron_backup.py --type full
  python cron_backup.py --type database
  python cron_backup.py --cleanup
  python cron_backup.py --status
  python cron_backup.py --crontab-examples
        '''
    )
    
    parser.add_argument(
        '--type',
        choices=['database', 'media', 'logs', 'full'],
        help='Tipo de backup a executar'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Remove backups antigos'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Mostra status dos backups'
    )
    
    parser.add_argument(
        '--crontab-examples',
        action='store_true',
        help='Mostra exemplos de configuração para crontab'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Força execução mesmo se agendamento estiver desabilitado'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Execução silenciosa (apenas logs de erro)'
    )
    
    args = parser.parse_args()
    
    # Configurar nível de log
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Mostrar exemplos de crontab
    if args.crontab_examples:
        generate_crontab_examples()
        return 0
    
    # Obter configurações
    config = get_backup_config()
    
    # Verificar se agendamento está habilitado (a menos que --force seja usado)
    if not args.force and not config['schedule'].get('enabled', False):
        logger.warning("Agendamento de backups está desabilitado. Use --force para executar mesmo assim.")
        return 1
    
    # Executar ação solicitada
    if args.status:
        get_backup_status(config)
        return 0
    
    if args.cleanup:
        result = cleanup_old_backups(config)
        return 0 if result['success'] else 1
    
    if args.type:
        result = execute_backup(args.type, config)
        return 0 if result else 1
    
    # Se nenhuma ação específica foi solicitada, executar backups configurados
    backup_types = config['schedule'].get('types', ['full'])
    
    success_count = 0
    total_count = len(backup_types)
    
    for backup_type in backup_types:
        result = execute_backup(backup_type, config)
        if result:
            success_count += 1
    
    logger.info(f"Execução concluída: {success_count}/{total_count} backups bem-sucedidos")
    
    return 0 if success_count == total_count else 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        sys.exit(1)