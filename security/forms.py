from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import MasterUser, SystemSetting
from .utils import check_password_strength, validate_ip_whitelist
import re

class MasterUserCreationForm(UserCreationForm):
    """
    Formulário para criação do usuário master
    """
    email = forms.EmailField(required=True, label="Email")
    authorized_ips = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="IPs Autorizados",
        help_text="Lista de IPs ou redes CIDR autorizados (um por linha). Deixe vazio para permitir qualquer IP."
    )
    security_level = forms.ChoiceField(
        choices=[
            ('BASIC', 'Básico'),
            ('ENHANCED', 'Aprimorado'),
            ('MAXIMUM', 'Máximo')
        ],
        initial='ENHANCED',
        label="Nível de Segurança",
        help_text="Nível de segurança do usuário master"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Nome de usuário único para o master. Use algo difícil de adivinhar."
        self.fields['password1'].help_text = "Senha deve ter pelo menos 12 caracteres com letras, números e símbolos."
    
    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Verificar se já existe um usuário master
        if MasterUser.objects.exists():
            raise ValidationError("Já existe um usuário master no sistema.")
        
        # Validar formato do username
        if len(username) < 6:
            raise ValidationError("Nome de usuário deve ter pelo menos 6 caracteres.")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Nome de usuário deve conter apenas letras, números e underscore.")
        
        return username
    
    def clean_password1(self):
        password = self.cleaned_data['password1']
        
        # Verificar força da senha
        strength = check_password_strength(password)
        
        if strength['strength'] != 'FORTE':
            error_msg = "Senha não atende aos critérios de segurança:\n"
            error_msg += "\n".join(strength['feedback'])
            raise ValidationError(error_msg)
        
        return password
    
    def clean_authorized_ips(self):
        ips_text = self.cleaned_data['authorized_ips']
        
        if not ips_text.strip():
            return []
        
        ips = [ip.strip() for ip in ips_text.split('\n') if ip.strip()]
        
        # Validar cada IP
        for ip in ips:
            if not self._validate_ip_format(ip):
                raise ValidationError(f"IP inválido: {ip}")
        
        return ips
    
    def _validate_ip_format(self, ip):
        """
        Valida formato de IP ou CIDR
        """
        import ipaddress
        try:
            if '/' in ip:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = True
        user.is_superuser = True
        
        if commit:
            user.save()
            
            # Criar perfil master
            MasterUser.objects.create(
                user=user,
                authorized_ips=self.cleaned_data['authorized_ips'],
                security_level=self.cleaned_data['security_level']
            )
        
        return user

class SecuritySettingsForm(forms.Form):
    """
    Formulário para configurações de segurança
    """
    max_login_attempts = forms.IntegerField(
        min_value=3,
        max_value=10,
        initial=5,
        label="Máximo de Tentativas de Login",
        help_text="Número máximo de tentativas de login antes de bloquear o IP"
    )
    
    lockout_duration = forms.IntegerField(
        min_value=15,
        max_value=1440,
        initial=60,
        label="Duração do Bloqueio (minutos)",
        help_text="Tempo em minutos que um IP fica bloqueado"
    )
    
    session_timeout = forms.IntegerField(
        min_value=5,
        max_value=120,
        initial=30,
        label="Timeout da Sessão (minutos)",
        help_text="Tempo de inatividade antes da sessão expirar"
    )
    
    password_min_length = forms.IntegerField(
        min_value=8,
        max_value=32,
        initial=8,
        label="Comprimento Mínimo da Senha",
        help_text="Número mínimo de caracteres para senhas"
    )
    
    require_2fa = forms.BooleanField(
        required=False,
        initial=False,
        label="Exigir 2FA",
        help_text="Tornar autenticação de dois fatores obrigatória"
    )
    
    log_retention_days = forms.IntegerField(
        min_value=30,
        max_value=365,
        initial=90,
        label="Retenção de Logs (dias)",
        help_text="Número de dias para manter logs de segurança"
    )
    
    enable_ip_whitelist = forms.BooleanField(
        required=False,
        initial=False,
        label="Habilitar Lista Branca de IPs",
        help_text="Restringir acesso apenas aos IPs autorizados"
    )
    
    allowed_countries = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'BR,US,CA'}),
        label="Países Permitidos",
        help_text="Códigos de países permitidos (separados por vírgula)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carregar valores atuais das configurações
        for field_name in self.fields:
            current_value = SystemSetting.get_setting(field_name)
            if current_value is not None:
                self.fields[field_name].initial = current_value

class TwoFactorSetupForm(forms.Form):
    """
    Formulário para configuração de 2FA
    """
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Código de Verificação",
        help_text="Digite o código de 6 dígitos do seu aplicativo autenticador",
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'class': 'form-control text-center',
            'style': 'font-size: 1.5em; letter-spacing: 0.5em;'
        })
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        
        if not code.isdigit():
            raise ValidationError("Código deve conter apenas números.")
        
        return code

class IPManagementForm(forms.Form):
    """
    Formulário para gerenciamento de IPs
    """
    ip_address = forms.GenericIPAddressField(
        label="Endereço IP",
        help_text="Endereço IP a ser bloqueado"
    )
    
    reason = forms.CharField(
        max_length=255,
        label="Motivo",
        help_text="Motivo do bloqueio",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Atividade suspeita'})
    )
    
    duration_hours = forms.IntegerField(
        min_value=1,
        max_value=8760,  # 1 ano
        initial=24,
        label="Duração (horas)",
        help_text="Tempo em horas para manter o bloqueio"
    )

class MasterUserUpdateForm(forms.ModelForm):
    """
    Formulário para atualizar configurações do usuário master
    """
    authorized_ips = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6}),
        required=False,
        label="IPs Autorizados",
        help_text="Lista de IPs ou redes CIDR autorizados (um por linha)"
    )
    
    class Meta:
        model = MasterUser
        fields = ['authorized_ips', 'security_level', 'two_factor_enabled']
        labels = {
            'security_level': 'Nível de Segurança',
            'two_factor_enabled': 'Autenticação de Dois Fatores'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.authorized_ips:
            self.fields['authorized_ips'].initial = '\n'.join(self.instance.authorized_ips)
    
    def clean_authorized_ips(self):
        ips_text = self.cleaned_data['authorized_ips']
        
        if not ips_text.strip():
            return []
        
        ips = [ip.strip() for ip in ips_text.split('\n') if ip.strip()]
        
        # Validar cada IP
        for ip in ips:
            if not self._validate_ip_format(ip):
                raise ValidationError(f"IP inválido: {ip}")
        
        return ips
    
    def _validate_ip_format(self, ip):
        """
        Valida formato de IP ou CIDR
        """
        import ipaddress
        try:
            if '/' in ip:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return True
        except:
            return False

class PasswordChangeForm(forms.Form):
    """
    Formulário para alteração de senha com validação de força
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(),
        label="Senha Atual"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(),
        label="Nova Senha"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(),
        label="Confirmar Nova Senha"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        
        if not self.user.check_password(password):
            raise ValidationError("Senha atual incorreta.")
        
        return password
    
    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        
        # Verificar força da senha
        strength = check_password_strength(password)
        
        if strength['strength'] != 'FORTE':
            error_msg = "Nova senha não atende aos critérios de segurança:\n"
            error_msg += "\n".join(strength['feedback'])
            raise ValidationError(error_msg)
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("As senhas não coincidem.")
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user

class SecurityReportForm(forms.Form):
    """
    Formulário para geração de relatórios de segurança
    """
    REPORT_TYPES = [
        ('login_attempts', 'Tentativas de Login'),
        ('security_events', 'Eventos de Segurança'),
        ('blocked_ips', 'IPs Bloqueados'),
        ('user_activity', 'Atividade de Usuários'),
        ('system_health', 'Saúde do Sistema')
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        label="Tipo de Relatório"
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data Inicial"
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data Final"
    )
    
    format_type = forms.ChoiceField(
        choices=[('html', 'HTML'), ('pdf', 'PDF'), ('csv', 'CSV')],
        initial='html',
        label="Formato"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Data inicial deve ser anterior à data final.")
        
        return cleaned_data