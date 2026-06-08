from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import PlanoComercial, Tenant, ConfiguracaoTenant

class RegistroEmpresaForm(forms.Form):
    """Formulário para criação de conta (somente e-mail e senha)"""
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail'
        })
    )

    senha = forms.CharField(
        min_length=8,
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite uma senha segura'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

class CriarEmpresaForm(forms.Form):
    nome_empresa = forms.CharField(
        max_length=200,
        label='Nome da Empresa',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome da sua empresa',
            }
        ),
    )

    aceitar_termos = forms.BooleanField(
        label='Aceito os termos de uso e política de privacidade',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

class ConfiguracaoInicialForm(forms.Form):
    """Formulário para configuração inicial do tenant"""
    email_contato = forms.EmailField(
        label='E-mail de Contato',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contato@suaempresa.com'
        })
    )
    
    telefone_contato = forms.CharField(
        max_length=20,
        label='Telefone de Contato',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999'
        })
    )
    
    endereco = forms.CharField(
        label='Endereço',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Endereço completo da empresa'
        })
    )
    
    cor_primaria = forms.CharField(
        max_length=7,
        label='Cor Primária',
        initial='#007bff',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )
    
    cor_secundaria = forms.CharField(
        max_length=7,
        label='Cor Secundária',
        initial='#6c757d',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color'
        })
    )

class PlanoComercialForm(forms.ModelForm):
    """Formulário para criação/edição de planos comerciais"""
    class Meta:
        model = PlanoComercial
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'preco_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_anual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_usuarios': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_imoveis': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_contratos': forms.NumberInput(attrs={'class': 'form-control'}),
            'storage_gb': forms.NumberInput(attrs={'class': 'form-control'}),
            'api_calls_mes': forms.NumberInput(attrs={'class': 'form-control'}),
            'suporte_prioritario': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'backup_automatico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'subdominio_personalizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TenantForm(forms.ModelForm):
    """Formulário para criação/edição de tenants"""
    class Meta:
        model = Tenant
        fields = ['nome_empresa', 'usuario_admin', 'plano', 'status']
        widgets = {
            'nome_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_admin': forms.Select(attrs={'class': 'form-control'}),
            'plano': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
