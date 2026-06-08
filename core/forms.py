from django import forms
from .models import Inquilino, Proprietario

class InquilinoForm(forms.ModelForm):
    class Meta:
        model = Inquilino
        fields = [
            'nome', 'tipo', 'cpf_cnpj', 'rg_ie', 'data_nascimento',
            'profissao', 'telefone', 'email',
            'endereco', 'cep', 'cidade', 'estado',
            'renda', 'banco', 'agencia', 'conta', 'pix',
            'fiador', 'renda_comprovada', 'observacoes'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg_ie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000-0'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profissao': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 90000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2', 'placeholder': 'SP'}),
            'renda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do banco'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-0'}),
            'pix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chave PIX'}),
            'fiador': forms.Select(attrs={'class': 'form-select'}),
            'renda_comprovada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fiador'].queryset = Inquilino.objects.all()
        self.fields['fiador'].empty_label = "Selecione um fiador (opcional)"
        
        # Campos obrigatórios
        required_fields = ['nome', 'tipo', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'cep', 'cidade', 'estado']
        for field in required_fields:
            self.fields[field].required = True

class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = [
            'nome', 'tipo', 'cpf_cnpj', 'rg_ie', 'data_nascimento',
            'profissao', 'telefone', 'email',
            'endereco', 'cep', 'cidade', 'estado',
            'renda', 'banco', 'agencia', 'conta', 'pix', 'observacoes'
        ]
        
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg_ie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000-0'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profissao': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 90000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2', 'placeholder': 'SP'}),
            'renda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do banco'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-0'}),
            'pix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chave PIX'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        required_fields = ['nome', 'tipo', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'cep', 'cidade', 'estado']
        for field in required_fields:
            self.fields[field].required = True