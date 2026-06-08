from django import forms
from django.utils import timezone

from .models import IPTU, Seguro, Parcela, Sangria
from imoveis.models import Imovel

# -----------------------------
# Formulários existentes
# -----------------------------

class IPTUForm(forms.ModelForm):
    class Meta:
        model = IPTU
        fields = [
            'imovel', 'ano_exercicio', 'valor_total', 'valor_desconto_vista',
            'data_vencimento_vista', 'numero_parcelas', 'forma_pagamento',
            'status', 'observacoes'
        ]


class SeguroForm(forms.ModelForm):
    class Meta:
        model = Seguro
        fields = [
            'imovel', 'contrato', 'seguradora', 'tipo_seguro', 'numero_apolice',
            'data_inicio', 'data_fim', 'valor_total', 'valor_mensal', 'forma_pagamento',
            'cobertura', 'franquia', 'status', 'observacoes'
        ]


class ParcelaForm(forms.ModelForm):
    class Meta:
        model = Parcela
        fields = [
            'numero_parcela', 'data_vencimento', 'valor_aluguel', 'valor_condominio',
            'valor_iptu', 'valor_seguro', 'valor_outros', 'valor_desconto', 'valor_multa',
            'valor_juros', 'data_pagamento', 'valor_pago', 'forma_pagamento',
            'observacoes', 'status', 'tipo'
        ]


class SangriaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'tenant') and user.tenant:
            # limitar imóveis por tenant, se existir
            self.fields['imovel'].queryset = Imovel.objects.filter(tenant=user.tenant)

    class Meta:
        model = Sangria
        fields = [
            'descricao', 'categoria', 'valor', 'data_vencimento', 'data_pagamento',
            'forma_pagamento', 'imovel', 'contrato', 'fornecedor', 'numero_documento',
            'observacoes', 'status'
        ]


class SangriaFiltroForm(forms.Form):
    data_inicio = forms.DateField(required=False)
    data_fim = forms.DateField(required=False)
    categoria = forms.ChoiceField(choices=[('', 'Todas')] + list(Sangria.CATEGORIA_CHOICES), required=False)
    status = forms.ChoiceField(choices=[('', 'Todos')] + list(Sangria.STATUS_CHOICES), required=False)
    forma_pagamento = forms.ChoiceField(choices=[('', 'Todas')] + list(Sangria.FORMA_PAGAMENTO_CHOICES), required=False)
    descricao = forms.CharField(required=False)


class ConfirmacaoSenhaForm(forms.Form):
    senha = forms.CharField(widget=forms.PasswordInput, label='Confirme sua senha')
    confirmar_senha = forms.CharField(widget=forms.HiddenInput, initial='1')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self.user is None:
            raise forms.ValidationError('Usuário não encontrado para validação da senha.')
        senha = cleaned.get('senha')
        if not senha or not self.user.check_password(senha):
            raise forms.ValidationError('Senha inválida.')
        return cleaned
