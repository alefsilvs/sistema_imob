from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Pessoa
from financeiro.models import NotaFiscal, Seguro
from imoveis.models import Imovel
from security.models import MasterUser, SystemSetting
from security.encryption import encryption, is_encrypted
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migra dados existentes para formato criptografado'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações no banco de dados',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a criptografia mesmo se os dados já parecem estar criptografados',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita no banco de dados'))
        
        self.stdout.write('Iniciando migração de dados para formato criptografado...')
        
        try:
            with transaction.atomic():
                # Migrar dados de Pessoa
                self._migrate_pessoa_data(dry_run, force)
                
                # Migrar dados de NotaFiscal
                self._migrate_notafiscal_data(dry_run, force)
                
                # Migrar dados de Seguro
                self._migrate_seguro_data(dry_run, force)
                
                # Migrar dados de Imovel
                self._migrate_imovel_data(dry_run, force)
                
                # Migrar dados de MasterUser
                self._migrate_masteruser_data(dry_run, force)
                
                # Migrar dados de SystemSetting
                self._migrate_systemsetting_data(dry_run, force)
                
                if dry_run:
                    # Reverter transação no modo dry-run
                    raise Exception("Dry-run completed")
                    
        except Exception as e:
            if "Dry-run completed" in str(e):
                self.stdout.write(self.style.SUCCESS('Dry-run concluído com sucesso!'))
            else:
                self.stdout.write(self.style.ERROR(f'Erro durante a migração: {e}'))
                raise
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))
    
    def _migrate_pessoa_data(self, dry_run, force):
        """Migra dados sensíveis de Pessoa"""
        self.stdout.write('Migrando dados de Pessoa...')
        
        pessoas = Pessoa.objects.all()
        count = 0
        
        for pessoa in pessoas:
            updated = False
            
            # CPF/CNPJ
            if pessoa.cpf_cnpj and (force or not is_encrypted(pessoa.cpf_cnpj)):
                if not dry_run:
                    pessoa.cpf_cnpj = encryption.encrypt(pessoa.cpf_cnpj)
                updated = True
            
            # RG/IE
            if pessoa.rg_ie and (force or not is_encrypted(pessoa.rg_ie)):
                if not dry_run:
                    pessoa.rg_ie = encryption.encrypt(pessoa.rg_ie)
                updated = True
            
            # Banco
            if pessoa.banco and (force or not is_encrypted(pessoa.banco)):
                if not dry_run:
                    pessoa.banco = encryption.encrypt(pessoa.banco)
                updated = True
            
            # Agência
            if pessoa.agencia and (force or not is_encrypted(pessoa.agencia)):
                if not dry_run:
                    pessoa.agencia = encryption.encrypt(pessoa.agencia)
                updated = True
            
            # Conta
            if pessoa.conta and (force or not is_encrypted(pessoa.conta)):
                if not dry_run:
                    pessoa.conta = encryption.encrypt(pessoa.conta)
                updated = True
            
            # PIX
            if pessoa.pix and (force or not is_encrypted(pessoa.pix)):
                if not dry_run:
                    pessoa.pix = encryption.encrypt(pessoa.pix)
                updated = True
            
            if updated:
                if not dry_run:
                    pessoa.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de Pessoa processados')
    
    def _migrate_notafiscal_data(self, dry_run, force):
        """Migra dados sensíveis de NotaFiscal"""
        self.stdout.write('Migrando dados de NotaFiscal...')
        
        notas = NotaFiscal.objects.all()
        count = 0
        
        for nota in notas:
            updated = False
            
            # Chave de acesso
            if nota.chave_acesso and (force or not is_encrypted(nota.chave_acesso)):
                if not dry_run:
                    nota.chave_acesso = encryption.encrypt(nota.chave_acesso)
                updated = True
            
            # Cliente documento
            if nota.cliente_documento and (force or not is_encrypted(nota.cliente_documento)):
                if not dry_run:
                    nota.cliente_documento = encryption.encrypt(nota.cliente_documento)
                updated = True
            
            if updated:
                if not dry_run:
                    nota.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de NotaFiscal processados')
    
    def _migrate_seguro_data(self, dry_run, force):
        """Migra dados sensíveis de Seguro"""
        self.stdout.write('Migrando dados de Seguro...')
        
        seguros = Seguro.objects.all()
        count = 0
        
        for seguro in seguros:
            updated = False
            
            # Número da apólice
            if seguro.numero_apolice and (force or not is_encrypted(seguro.numero_apolice)):
                if not dry_run:
                    seguro.numero_apolice = encryption.encrypt(seguro.numero_apolice)
                updated = True
            
            if updated:
                if not dry_run:
                    seguro.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de Seguro processados')
    
    def _migrate_imovel_data(self, dry_run, force):
        """Migra dados sensíveis de Imovel"""
        self.stdout.write('Migrando dados de Imovel...')
        
        imoveis = Imovel.objects.all()
        count = 0
        
        for imovel in imoveis:
            updated = False
            
            # Inscrição municipal
            if imovel.inscricao_municipal and (force or not is_encrypted(imovel.inscricao_municipal)):
                if not dry_run:
                    imovel.inscricao_municipal = encryption.encrypt(imovel.inscricao_municipal)
                updated = True
            
            # Matrícula
            if imovel.matricula and (force or not is_encrypted(imovel.matricula)):
                if not dry_run:
                    imovel.matricula = encryption.encrypt(imovel.matricula)
                updated = True
            
            if updated:
                if not dry_run:
                    imovel.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de Imovel processados')
    
    def _migrate_masteruser_data(self, dry_run, force):
        """Migra dados sensíveis de MasterUser"""
        self.stdout.write('Migrando dados de MasterUser...')
        
        master_users = MasterUser.objects.all()
        count = 0
        
        for master_user in master_users:
            updated = False
            
            # Two factor secret
            if master_user.two_factor_secret and (force or not is_encrypted(master_user.two_factor_secret)):
                if not dry_run:
                    master_user.two_factor_secret = encryption.encrypt(master_user.two_factor_secret)
                updated = True
            
            # Backup codes
            if master_user.backup_codes and isinstance(master_user.backup_codes, list):
                if not dry_run:
                    import json
                    json_str = json.dumps(master_user.backup_codes)
                    if force or not is_encrypted(json_str):
                        master_user.backup_codes = master_user.backup_codes  # O campo já criptografa automaticamente
                        updated = True
            
            if updated:
                if not dry_run:
                    master_user.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de MasterUser processados')
    
    def _migrate_systemsetting_data(self, dry_run, force):
        """Migra dados sensíveis de SystemSetting"""
        self.stdout.write('Migrando dados de SystemSetting...')
        
        settings = SystemSetting.objects.all()
        count = 0
        
        for setting in settings:
            updated = False
            
            # Value
            if setting.value and (force or not is_encrypted(setting.value)):
                if not dry_run:
                    setting.value = encryption.encrypt(setting.value)
                updated = True
            
            if updated:
                if not dry_run:
                    setting.save()
                count += 1
        
        self.stdout.write(f'  - {count} registros de SystemSetting processados')