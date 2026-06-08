from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import Vistoria, Documento, TipoDocumento, CategoriaDocumento, ItemVistoria
from imoveis.models import Imovel
from contratos.models import Contrato

class VistoriaForm(forms.ModelForm):
    class Meta:
        model = Vistoria
        fields = ['imovel', 'contrato', 'tipo', 'data_agendamento', 'responsavel', 'observacoes']
        widgets = {
            'imovel': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'contrato': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'data_agendamento': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável pela vistoria',
                'required': True
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observações sobre a vistoria (opcional)'
            })
        }
        labels = {
            'imovel': 'Imóvel',
            'contrato': 'Contrato (opcional)',
            'tipo': 'Tipo de Vistoria',
            'data_agendamento': 'Data e Hora do Agendamento',
            'responsavel': 'Responsável',
            'observacoes': 'Observações'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas imóveis ativos
        self.fields['imovel'].queryset = Imovel.objects.all().order_by('codigo')
        
        # Filtrar apenas contratos ativos
        self.fields['contrato'].queryset = Contrato.objects.filter(
            status='ATIVO'
        ).order_by('-data_inicio')
        
        # Tornar contrato opcional
        self.fields['contrato'].required = False
        
        # Definir data mínima como hoje
        self.fields['data_agendamento'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean_data_agendamento(self):
        data = self.cleaned_data.get('data_agendamento')
        if data and data < timezone.now():
            raise forms.ValidationError('A data de agendamento não pode ser no passado.')
        return data
    
    def clean(self):
        cleaned_data = super().clean()
        imovel = cleaned_data.get('imovel')
        contrato = cleaned_data.get('contrato')
        
        # Se um contrato foi selecionado, verificar se pertence ao imóvel
        if contrato and imovel and contrato.imovel != imovel:
            raise forms.ValidationError(
                'O contrato selecionado não pertence ao imóvel escolhido.'
            )
        
        return cleaned_data

# ==================== FORMULÁRIOS REPOSITÓRIO DIGITAL ====================

class DocumentoForm(forms.ModelForm):
    """Formulário para upload e edição de documentos"""
    
    tags = forms.CharField(
        max_length=500, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Separe as tags com vírgulas'
        }),
        label='Tags'
    )
    
    class Meta:
        model = Documento
        fields = [
            'nome_arquivo', 'arquivo', 'tipo', 
            'descricao', 'confidencialidade', 'data_documento',
            'data_validade', 'pessoa', 'imovel', 'contrato'
        ]
        widgets = {
            'nome_arquivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do documento',
                'required': True
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.txt',
                'required': True
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do documento (opcional)'
            }),
            'confidencialidade': forms.Select(attrs={
                'class': 'form-select'
            }),
            'data_documento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_validade': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'pessoa': forms.Select(attrs={
                'class': 'form-select'
            }),
            'imovel': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contrato': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'nome_arquivo': 'Nome do Arquivo',
            'arquivo': 'Arquivo',
            'tipo': 'Tipo de Documento',
            'descricao': 'Descrição',
            'confidencialidade': 'Nível de Confidencialidade',
            'data_documento': 'Data do Documento',
            'data_validade': 'Data de Vencimento',
            'pessoa': 'Pessoa',
            'imovel': 'Imóvel',
            'contrato': 'Contrato'
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Filtrar tipos por tenant
            self.fields['tipo'].queryset = TipoDocumento.objects.filter(
                tenant=tenant
            ).order_by('nome')
    
    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo:
            # Validar tamanho (50MB máximo)
            if arquivo.size > 50 * 1024 * 1024:
                raise forms.ValidationError('Arquivo muito grande. Tamanho máximo: 50MB')
            
            # Validar extensão
            extensoes_permitidas = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.jpg', '.jpeg', '.png', '.txt', '.zip', '.rar'
            ]
            nome_arquivo = arquivo.name.lower()
            if not any(nome_arquivo.endswith(ext) for ext in extensoes_permitidas):
                raise forms.ValidationError(
                    'Tipo de arquivo não permitido. Extensões aceitas: ' + 
                    ', '.join(extensoes_permitidas)
                )
        
        return arquivo

class CategoriaDocumentoForm(forms.ModelForm):
    """Formulário para criação e edição de categorias"""
    
    class Meta:
        model = CategoriaDocumento
        fields = ['nome', 'descricao', 'categoria_pai', 'cor', 'icone']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria (opcional)'
            }),
            'categoria_pai': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cor': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'icone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Classe do ícone Bootstrap (ex: bi-folder)',
                'value': 'bi-folder'
            })
        }
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
            'categoria_pai': 'Categoria Pai',
            'cor': 'Cor',
            'icone': 'Ícone'
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Filtrar categorias pai por tenant
            self.fields['categoria_pai'].queryset = CategoriaDocumento.objects.filter(
                tenant=tenant, ativo=True
            ).order_by('nome')
        
        # Tornar categoria pai opcional
        self.fields['categoria_pai'].required = False

class TipoDocumentoForm(forms.ModelForm):
    """Formulário para criação e edição de tipos de documento"""
    
    class Meta:
        model = TipoDocumento
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do tipo de documento',
                'required': True
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do tipo (opcional)'
            })
        }
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição'
        }

class FiltroDocumentosForm(forms.Form):
    """Formulário para filtros de busca de documentos"""
    
    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nome, descrição ou tags...'
        })
    )
    
    tipo = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.none(),
        required=False,
        empty_label="Todos os tipos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Documento.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    confidencialidade = forms.ChoiceField(
        choices=[('', 'Todos os níveis')] + Documento.CONFIDENCIALIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            self.fields['tipo'].queryset = TipoDocumento.objects.filter(
                tenant=tenant
            ).order_by('nome')

# Formset para itens de vistoria
ItemVistoriaFormSet = inlineformset_factory(
    Vistoria,
    ItemVistoria,
    fields=['item', 'estado', 'observacoes'],
    extra=5,
    can_delete=True,
    widgets={
        'item': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Item da vistoria'
        }),
        'estado': forms.Select(attrs={
            'class': 'form-select'
        }),
        'observacoes': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observações sobre o item'
        })
    }
)