from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import PagamentoOnline, LogPagamento, ConfiguracaoPagamento

@admin.register(PagamentoOnline)
class PagamentoOnlineAdmin(admin.ModelAdmin):
    list_display = [
        'token_display', 'parcela_info', 'valor_original', 'status_display', 
        'metodo_pagamento', 'data_criacao', 'data_pagamento', 'actions_display'
    ]
    list_filter = [
        'status', 'metodo_pagamento', 'data_criacao', 'data_pagamento'
    ]
    search_fields = [
        'token_pagamento', 'parcela__contrato__inquilino__nome',
        'parcela__contrato__imovel__endereco', 'nome_pagador', 'email_pagador'
    ]
    readonly_fields = [
        'id', 'token_pagamento', 'data_criacao', 'updated_at', 
        'url_pagamento_display', 'gateway_response_display'
    ]
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'token_pagamento', 'url_pagamento_display')
        }),
        ('Dados do Pagamento', {
            'fields': ('parcela', 'valor_original', 'valor_pago', 'status', 'metodo_pagamento')
        }),
        ('Transação', {
            'fields': ('transaction_id', 'gateway_response_display')
        }),
        ('Controle de Tempo', {
            'fields': ('data_criacao', 'data_expiracao', 'data_pagamento', 'data_confirmacao', 'updated_at')
        }),
        ('Dados do Pagador', {
            'fields': ('nome_pagador', 'email_pagador', 'telefone_pagador')
        }),
        ('Controle e Logs', {
            'fields': ('tentativas_processamento', 'ultimo_erro')
        }),
        ('Metadados', {
            'fields': ('ip_origem', 'user_agent')
        })
    )
    
    def token_display(self, obj):
        return f"{obj.token_pagamento[:12]}..."
    token_display.short_description = 'Token'
    
    def parcela_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/>'
            '<small>{} - {}</small>',
            obj.parcela.contrato.inquilino.nome,
            obj.parcela.contrato.imovel.endereco[:30],
            obj.parcela.get_tipo_display()
        )
    parcela_info.short_description = 'Parcela'
    
    def status_display(self, obj):
        colors = {
            'PENDENTE': '#ffc107',
            'PROCESSANDO': '#17a2b8',
            'APROVADO': '#28a745',
            'REJEITADO': '#dc3545',
            'CANCELADO': '#6c757d',
            'EXPIRADO': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def url_pagamento_display(self, obj):
        if obj.token_pagamento:
            url = obj.url_pagamento
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url, url
            )
        return '-'
    url_pagamento_display.short_description = 'URL de Pagamento'
    
    def gateway_response_display(self, obj):
        if obj.gateway_response:
            import json
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.gateway_response, indent=2, ensure_ascii=False)
            )
        return '-'
    gateway_response_display.short_description = 'Resposta do Gateway'
    
    def actions_display(self, obj):
        actions = []
        
        if obj.status == 'PENDENTE' and not obj.esta_expirado:
            actions.append(
                format_html(
                    '<a href="{}" target="_blank" class="button">Ver Pagamento</a>',
                    obj.url_pagamento
                )
            )
        
        if obj.status in ['PROCESSANDO', 'PENDENTE']:
            actions.append(
                format_html(
                    '<a href="#" onclick="marcarComoPago({})" class="button">Marcar como Pago</a>',
                    obj.pk
                )
            )
        
        return format_html(' '.join(actions)) if actions else '-'
    actions_display.short_description = 'Ações'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'parcela__contrato__inquilino',
            'parcela__contrato__imovel'
        )
    
    class Media:
        js = ('admin/js/pagamentos_admin.js',)

@admin.register(LogPagamento)
class LogPagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'pagamento_token', 'tipo', 'descricao_short', 'ip_origem'
    ]
    list_filter = ['tipo', 'timestamp']
    search_fields = [
        'pagamento__token_pagamento', 'descricao', 'ip_origem'
    ]
    readonly_fields = [
        'pagamento', 'tipo', 'descricao', 'dados_extras_display', 
        'ip_origem', 'user_agent', 'timestamp'
    ]
    
    def pagamento_token(self, obj):
        return f"{obj.pagamento.token_pagamento[:12]}..."
    pagamento_token.short_description = 'Token do Pagamento'
    
    def descricao_short(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_short.short_description = 'Descrição'
    
    def dados_extras_display(self, obj):
        if obj.dados_extras:
            import json
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto;">{}</pre>',
                json.dumps(obj.dados_extras, indent=2, ensure_ascii=False)
            )
        return '-'
    dados_extras_display.short_description = 'Dados Extras'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(ConfiguracaoPagamento)
class ConfiguracaoPagamentoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('PIX', {
            'fields': ('pix_habilitado', 'pix_chave', 'pix_nome_recebedor')
        }),
        ('Cartão de Crédito/Débito', {
            'fields': ('cartao_habilitado', 'gateway_api_key', 'gateway_secret_key', 'gateway_endpoint')
        }),
        ('Boleto Bancário', {
            'fields': ('boleto_habilitado', 'banco_codigo', 'agencia', 'conta')
        }),
        ('Configurações Gerais', {
            'fields': ('tempo_expiracao_horas', 'valor_minimo', 'taxa_processamento')
        }),
        ('URLs de Retorno', {
            'fields': ('url_sucesso', 'url_erro', 'url_cancelamento')
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Permitir apenas uma configuração
        return not ConfiguracaoPagamento.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

# Customização do admin site
admin.site.site_header = "Sistema Imobiliário - Pagamentos"
admin.site.site_title = "Pagamentos Admin"
admin.site.index_title = "Administração de Pagamentos"
