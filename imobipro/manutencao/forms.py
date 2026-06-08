from django import forms
from .models import OrdemServico, Fornecedor
from imoveis.models import Imovel
from contratos.models import Contrato

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = [
            'numero',
            'imovel',
            'contrato',
            'fornecedor',
            'descricao',
            'status',
            'data_agendamento',
            'data_conclusao',
            'valor_orcamento',
            'valor_final',
            'responsavel_pagamento',
            'observacoes',
        ]
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'imovel': forms.Select(attrs={'class': 'form-select'}),
            'contrato': forms.Select(attrs={'class': 'form-select'}),
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'data_agendamento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'data_conclusao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valor_orcamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'responsavel_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'numero': 'Número da OS',
            'imovel': 'Imóvel',
            'contrato': 'Contrato',
            'fornecedor': 'Fornecedor',
            'descricao': 'Descrição do Serviço',
            'status': 'Status',
            'data_agendamento': 'Data de Agendamento',
            'data_conclusao': 'Data de Conclusão',
            'valor_orcamento': 'Valor do Orçamento',
            'valor_final': 'Valor Final',
            'responsavel_pagamento': 'Responsável pelo Pagamento',
            'observacoes': 'Observações',
        }

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'telefone', 'email', 'endereco', 'especialidade', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome': 'Nome do Fornecedor',
            'cnpj': 'CNPJ',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'endereco': 'Endereço',
            'especialidade': 'Especialidade',
            'ativo': 'Fornecedor ativo',
        }
