from django.core.management.base import BaseCommand
from django.core.management import call_command
from security.backup import backup_manager
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Restaura backup do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            nargs='?',
            help='Caminho para o arquivo de backup ou manifesto',
        )
        parser.add_argument(
            '--type',
            choices=['database', 'media', 'logs', 'full'],
            help='Tipo específico de backup a restaurar (apenas para backups completos)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a restauração sem prompt interativo',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista backups disponíveis',
        )
    
    def handle(self, *args, **options):
        if options['list']:
            self._list_available_backups()
            return
        
        if not options['backup_file']:
            self.stdout.write(
                self.style.ERROR('Erro: backup_file é obrigatório quando --list não é usado')
            )
            return
        
        backup_file = options['backup_file']
        restore_type = options['type']
        confirm = options['confirm']
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Arquivo de backup não encontrado: {backup_file}')
            )
            return
        
        # Verificar se é um manifesto de backup completo
        if backup_path.name.startswith('backup_manifest_'):
            self._restore_from_manifest(backup_path, restore_type, confirm)
        else:
            self._restore_single_backup(backup_path, confirm)
    
    def _restore_from_manifest(self, manifest_path, restore_type, confirm):
        """Restaura backup usando arquivo de manifesto"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            self.stdout.write(self.style.HTTP_INFO('=== INFORMAÇÕES DO BACKUP ==='))
            self.stdout.write(f"Timestamp: {manifest.get('timestamp')}")
            self.stdout.write(f"Criado em: {manifest.get('created_at')}")
            self.stdout.write(f"Tipo: {manifest.get('type')}")
            
            files = manifest.get('files', {})
            self.stdout.write("\nArquivos disponíveis:")
            for file_type, file_path in files.items():
                if file_path and Path(file_path).exists():
                    self.stdout.write(f"  ✓ {file_type}: {file_path}")
                else:
                    self.stdout.write(f"  ✗ {file_type}: arquivo não encontrado")
            
            # Determinar quais tipos restaurar
            types_to_restore = []
            if restore_type:
                if restore_type in files and files[restore_type]:
                    types_to_restore = [restore_type]
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Tipo {restore_type} não disponível neste backup')
                    )
                    return
            else:
                # Restaurar todos os tipos disponíveis
                types_to_restore = [t for t, f in files.items() if f and Path(f).exists()]
            
            if not types_to_restore:
                self.stdout.write(self.style.ERROR('Nenhum arquivo válido para restaurar'))
                return
            
            # Confirmação
            if not confirm:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nVocê está prestes a restaurar: {', '.join(types_to_restore)}\n"
                        "ATENÇÃO: Esta operação pode sobrescrever dados existentes!"
                    )
                )
                response = input("Deseja continuar? (sim/não): ")
                if response.lower() not in ['sim', 's', 'yes', 'y']:
                    self.stdout.write("Operação cancelada.")
                    return
            
            # Executar restauração
            for restore_type in types_to_restore:
                file_path = files[restore_type]
                self.stdout.write(f"\nRestaurando {restore_type}...")
                
                try:
                    if restore_type == 'database':
                        backup_manager.restore_database_backup(file_path)
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ {restore_type} restaurado com sucesso")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Restauração de {restore_type} deve ser feita manualmente\n"
                                f"Arquivo: {file_path}"
                            )
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Erro ao restaurar {restore_type}: {e}")
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao processar manifesto: {e}')
            )
    
    def _restore_single_backup(self, backup_path, confirm):
        """Restaura um único arquivo de backup"""
        # Determinar tipo baseado no nome do arquivo
        filename = backup_path.name
        
        if 'database_backup_' in filename:
            backup_type = 'database'
        elif 'media_backup_' in filename:
            backup_type = 'media'
        elif 'logs_backup_' in filename:
            backup_type = 'logs'
        else:
            self.stdout.write(
                self.style.ERROR('Não foi possível determinar o tipo do backup')
            )
            return
        
        self.stdout.write(f"Tipo de backup detectado: {backup_type}")
        self.stdout.write(f"Arquivo: {backup_path}")
        
        # Confirmação
        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    f"\nVocê está prestes a restaurar um backup do tipo '{backup_type}'\n"
                    "ATENÇÃO: Esta operação pode sobrescrever dados existentes!"
                )
            )
            response = input("Deseja continuar? (sim/não): ")
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write("Operação cancelada.")
                return
        
        # Executar restauração
        try:
            if backup_type == 'database':
                backup_manager.restore_database_backup(backup_path)
                self.stdout.write(
                    self.style.SUCCESS("Backup do banco de dados restaurado com sucesso!")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Restauração de {backup_type} deve ser feita manualmente\n"
                        f"Arquivo: {backup_path}"
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro na restauração: {e}')
            )
    
    def _list_available_backups(self):
        """Lista backups disponíveis"""
        try:
            status = backup_manager.get_backup_status()
            backup_dir = Path(status['backup_directory'])
            
            self.stdout.write(self.style.HTTP_INFO('=== BACKUPS DISPONÍVEIS ==='))
            self.stdout.write(f"Diretório: {backup_dir}\n")
            
            # Listar manifestos de backup completo
            manifests = list(backup_dir.glob('backup_manifest_*.json'))
            manifests.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if manifests:
                self.stdout.write("BACKUPS COMPLETOS:")
                for manifest in manifests:
                    try:
                        with open(manifest, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        self.stdout.write(
                            f"  📦 {manifest.name}\n"
                            f"     Criado: {data.get('created_at', 'N/A')}\n"
                            f"     Tipo: {data.get('type', 'N/A')}"
                        )
                        
                        files = data.get('files', {})
                        for file_type, file_path in files.items():
                            if file_path:
                                exists = "✓" if Path(file_path).exists() else "✗"
                                self.stdout.write(f"     {exists} {file_type}")
                        
                        self.stdout.write("")  # Linha em branco
                        
                    except Exception as e:
                        self.stdout.write(f"  ❌ {manifest.name} (erro ao ler: {e})")
            
            # Listar backups individuais
            individual_backups = []
            for pattern in ['database_backup_*.json.gz', 'media_backup_*.tar.gz', 'logs_backup_*.tar.gz']:
                individual_backups.extend(backup_dir.glob(pattern))
            
            individual_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if individual_backups:
                self.stdout.write("BACKUPS INDIVIDUAIS:")
                for backup in individual_backups:
                    size_mb = backup.stat().st_size / (1024 * 1024)
                    self.stdout.write(
                        f"  📄 {backup.name} ({size_mb:.2f} MB)"
                    )
            
            if not manifests and not individual_backups:
                self.stdout.write("Nenhum backup encontrado.")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao listar backups: {e}')
            )