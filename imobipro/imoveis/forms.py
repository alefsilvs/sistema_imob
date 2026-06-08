from django import forms
from .models import Imovel, FotoImovel
from core.models import Proprietario

class ImovelForm(forms.ModelForm):
    class Meta:
        model = Imovel
        fields = [
            'codigo', 'proprietario', 'tipo', 'finalidade',
            'endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
            'area_total', 'area_construida', 'quartos', 'banheiros', 'vagas_garagem',
            'valor_aluguel', 'valor_condominio', 'valor_iptu', 'valor_seguro',
            'inscricao_municipal', 'matricula', 'descricao', 'mobiliado', 'status'
        ]
        
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: IMV001'}),
            'proprietario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'finalidade': forms.Select(attrs={'class': 'form-select'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, Avenida, etc.'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apto 101, Casa 2, etc.'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2', 'placeholder': 'SP'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'area_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'area_construida': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quartos': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'banheiros': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'vagas_garagem': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_aluguel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_condominio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_iptu': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_seguro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'inscricao_municipal': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mobiliado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proprietario'].queryset = Proprietario.objects.all()
        
        # Campos obrigatórios
        required_fields = ['codigo', 'proprietario', 'tipo', 'finalidade', 'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep', 'valor_aluguel']
        for field in required_fields:
            self.fields[field].required = True

class FotoImovelForm(forms.ModelForm):
    class Meta:
        model = FotoImovel
        fields = ['foto', 'descricao', 'principal']
        
        widgets = {
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição da foto'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
