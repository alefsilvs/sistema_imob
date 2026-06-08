from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from security.models import MasterUser
import pyotp
import qrcode
import io

class Command(BaseCommand):
    help = 'Configura ou gerencia 2FA para usuários master'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nome do usuário master'
        )
        parser.add_argument(
            '--action',
            type=str,
            choices=['enable', 'disable', 'status', 'reset'],
            default='status',
            help='Ação a ser executada (enable, disable, status, reset)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a ação sem confirmação'
        )
    
    def handle(self, *args, **options):
        username = options.get('username')
        action = options.get('action')
        force = options.get('force')
        
        if not username:
            self.stdout.write(
                self.style.ERROR('Nome do usuário é obrigatório. Use --username')
            )
            return
        
        try:
            user = User.objects.get(username=username)
            master_user = user.master_profile
        except User.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não encontrado.')
        except MasterUser.DoesNotExist:
            raise CommandError(f'Usuário "{username}" não é um usuário master.')
        
        if action == 'status':
            self._show_status(master_user)
        elif action == 'enable':
            self._enable_2fa(master_user, force)
        elif action == 'disable':
            self._disable_2fa(master_user, force)
        elif action == 'reset':
            self._reset_2fa(master_user, force)
    
    def _show_status(self, master_user):
        """Mostra o status atual do 2FA"""
        self.stdout.write(f'\n=== Status 2FA para {master_user.user.username} ===')
        
        if master_user.two_factor_enabled:
            self.stdout.write(
                self.style.SUCCESS('✅ 2FA: ATIVADO')
            )
            self.stdout.write(f'Secret configurado: {"Sim" if master_user.two_factor_secret else "Não"}')
        else:
            self.stdout.write(
                self.style.WARNING('❌ 2FA: DESATIVADO')
            )
        
        self.stdout.write(f'Último login: {master_user.last_login or "Nunca"}')
        self.stdout.write(f'IPs autorizados: {len(master_user.authorized_ips) if master_user.authorized_ips else 0}')
    
    def _enable_2fa(self, master_user, force):
        """Habilita 2FA para o usuário"""
        if master_user.two_factor_enabled and not force:
            self.stdout.write(
                self.style.WARNING('2FA já está ativado. Use --force para reconfigurar.')
            )
            return
        
        # Gerar novo secret
        secret = pyotp.random_base32()
        
        # Gerar QR Code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=master_user.user.username,
            issuer_name="Sistema Imobiliário"
        )
        
        # Salvar configurações
        master_user.two_factor_secret = secret
        master_user.two_factor_enabled = True
        master_user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ 2FA ativado para {master_user.user.username}')
        )
        self.stdout.write('\n=== CONFIGURAÇÃO DO APLICATIVO AUTENTICADOR ===')
        self.stdout.write(f'Secret Key: {secret}')
        self.stdout.write(f'URI: {provisioning_uri}')
        
        # Gerar QR Code em ASCII (opcional)
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Imprimir QR Code em ASCII
            self.stdout.write('\n=== QR CODE (ASCII) ===')
            qr.print_ascii()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Não foi possível gerar QR Code ASCII: {e}')
            )
        
        self.stdout.write('\n=== INSTRUÇÕES ===')
        self.stdout.write('1. Instale um aplicativo autenticador (Google Authenticator, Authy, etc.)')
        self.stdout.write('2. Escaneie o QR Code ou digite a Secret Key manualmente')
        self.stdout.write('3. Use o código de 6 dígitos gerado pelo app para fazer login')
        
        self.stdout.write(
            self.style.WARNING('\n⚠️  IMPORTANTE: Guarde a Secret Key em local seguro!')
        )
    
    def _disable_2fa(self, master_user, force):
        """Desabilita 2FA para o usuário"""
        if not master_user.two_factor_enabled:
            self.stdout.write(
                self.style.WARNING('2FA já está desativado.')
            )
            return
        
        if not force:
            confirm = input('Tem certeza que deseja desativar o 2FA? (sim/não): ')
            if confirm.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write('Operação cancelada.')
                return
        
        master_user.two_factor_enabled = False
        master_user.two_factor_secret = ''
        master_user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ 2FA desativado para {master_user.user.username}')
        )
        self.stdout.write(
            self.style.WARNING('⚠️  A segurança da conta foi reduzida!')
        )
    
    def _reset_2fa(self, master_user, force):
        """Reseta a configuração 2FA (gera novo secret)"""
        if not master_user.two_factor_enabled:
            self.stdout.write(
                self.style.WARNING('2FA não está ativado. Use --action enable para ativar.')
            )
            return
        
        if not force:
            confirm = input('Tem certeza que deseja resetar o 2FA? Isso invalidará a configuração atual. (sim/não): ')
            if confirm.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write('Operação cancelada.')
                return
        
        # Desativar temporariamente e reativar com novo secret
        self._disable_2fa(master_user, True)
        self._enable_2fa(master_user, True)
        
        self.stdout.write(
            self.style.SUCCESS('✅ 2FA resetado com sucesso!')
        )
        self.stdout.write(
            self.style.WARNING('⚠️  Configure novamente seu aplicativo autenticador!')
        )