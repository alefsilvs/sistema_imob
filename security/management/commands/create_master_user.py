from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from security.models import MasterUser
from security.utils import generate_hardware_fingerprint, get_client_ip
import getpass
import sys

class Command(BaseCommand):
    help = 'Cria o usuário master único do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome de usuário para o master user',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email do master user',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Senha do master user (não recomendado por segurança)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a criação mesmo se já existir um master user',
        )
    
    def handle(self, *args, **options):
        # Verificar se já existe um master user
        if MasterUser.objects.exists() and not options['force']:
            raise CommandError(
                'Já existe um usuário master no sistema. '
                'Use --force para substituir o existente.'
            )
        
        # Obter dados do usuário
        username = options['username'] or input('Nome de usuário: ')
        email = options['email'] or input('Email: ')
        
        if options['password']:
            password = options['password']
            self.stdout.write(
                self.style.WARNING(
                    'AVISO: Passar senha via linha de comando não é seguro!'
                )
            )
        else:
            password = getpass.getpass('Senha: ')
            password_confirm = getpass.getpass('Confirme a senha: ')
            
            if password != password_confirm:
                raise CommandError('As senhas não coincidem!')
        
        # Validar força da senha
        if len(password) < 12:
            raise CommandError(
                'A senha deve ter pelo menos 12 caracteres para o usuário master!'
            )
        
        try:
            with transaction.atomic():
                # Remover master user existente se --force foi usado
                if options['force'] and MasterUser.objects.exists():
                    old_master = MasterUser.objects.first()
                    old_user = old_master.user
                    old_master.delete()
                    old_user.delete()
                    self.stdout.write(
                        self.style.WARNING('Usuário master anterior removido.')
                    )
                
                # Criar usuário Django
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.is_staff = True
                user.is_superuser = True
                user.save()
                
                # Criar perfil master
                master_user = MasterUser.objects.create(
                    user=user,
                    security_level='MAXIMUM',
                    hardware_fingerprint=generate_hardware_fingerprint(),
                    authorized_ips=['127.0.0.1', '::1'],  # Localhost por padrão
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Usuário master "{username}" criado com sucesso!'
                    )
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Hardware Fingerprint: {master_user.hardware_fingerprint}'
                    )
                )
                
                self.stdout.write(
                    self.style.WARNING(
                        'IMPORTANTE: Configure os IPs autorizados e ative 2FA '
                        'através do painel administrativo para máxima segurança.'
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Erro ao criar usuário master: {str(e)}')