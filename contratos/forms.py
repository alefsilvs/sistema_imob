from django import forms
from .models import Contrato, ReajusteContrato
from core.models import Inquilino
from imoveis.models import Imovel

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['numero', 'imovel', 'inquilino', 'data_inicio', 'data_fim', 
                 'valor_aluguel', 'valor_condominio', 'valor_iptu', 'dia_vencimento',
                 'tipo_reajuste', 'percentual_reajuste', 'periodicidade_reajuste',
                 'percentual_honorario', 'caucao', 'observacoes']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'imovel': forms.Select(attrs={'class': 'form-select'}),
            'inquilino': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_aluguel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_condominio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_iptu': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'tipo_reajuste': forms.Select(attrs={'class': 'form-select'}),
            'percentual_reajuste': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'periodicidade_reajuste': forms.NumberInput(attrs={'class': 'form-control'}),
            'percentual_honorario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'caucao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'numero': 'Número do Contrato',
            'imovel': 'Imóvel',
            'inquilino': 'Inquilino',
            'data_inicio': 'Data de Início',
            'data_fim': 'Data de Fim',
            'valor_aluguel': 'Valor do Aluguel',
            'valor_condominio': 'Valor do Condomínio',
            'valor_iptu': 'Valor do IPTU',
            'dia_vencimento': 'Dia de Vencimento',
            'tipo_reajuste': 'Tipo de Reajuste',
            'percentual_reajuste': 'Percentual de Reajuste (%)',
            'periodicidade_reajuste': 'Periodicidade do Reajuste (meses)',
            'percentual_honorario': 'Percentual de Honorário (%)',
            'caucao': 'Caução',
            'observacoes': 'Observações',
        }

class ReajusteForm(forms.ModelForm):
    class Meta:
        model = ReajusteContrato
        fields = ['data_reajuste', 'valor_anterior', 'valor_novo', 'indice_aplicado', 'observacoes']
        widgets = {
            'data_reajuste': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_anterior': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'valor_novo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'indice_aplicado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'data_reajuste': 'Data do Reajuste',
            'valor_anterior': 'Valor Anterior',
            'valor_novo': 'Valor Novo',
            'indice_aplicado': 'Índice Aplicado',
            'observacoes': 'Observações',
        }