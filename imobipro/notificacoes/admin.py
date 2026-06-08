from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CategoriaTemplate, TemplateNotificacao, NotificacaoAgendada,
    Notificacao, EstatisticaNotificacao, TipoNotificacao, CobrancaAutomaticaLog
)

@admin.register(CategoriaTemplate)
class CategoriaTemplateAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cor_display', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'descricao']
    prepopulated_fields = {'nome': ('nome',)}
    
    def cor_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            obj.cor, obj.cor
        )
    cor_display.short_description = 'Cor'

@admin.register(TemplateNotificacao)
class TemplateNotificacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'tipo', 'formato', 'ativo', 'padrao', 'created_at']
    list_filter = ['categoria', 'tipo', 'formato', 'ativo', 'padrao', 'created_at']
    search_fields = ['nome', 'assunto_template', 'corpo_template']
    readonly_fields = ['usuario_criador', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'categoria', 'tipo', 'ativo', 'padrao')
        }),
        ('Template', {
            'fields': ('formato', 'assunto_template', 'corpo_template')
        }),
        ('Configurações Avançadas', {
            'fields': ('variaveis_disponiveis', 'preview_dados'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('usuario_criador', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(NotificacaoAgendada)
class NotificacaoAgendadaAdmin(admin.ModelAdmin):
    list_display = [
        'nome_campanha', 'template', 'status', 'data_envio', 
        'recorrencia', 'prioridade', 'tentativas_realizadas', 'created_at'
    ]
    list_filter = [
        'status', 'recorrencia', 'prioridade', 'data_envio', 'created_at'
    ]
    search_fields = ['nome_campanha', 'descricao']
    readonly_fields = [
        'tentativas_realizadas', 'ultima_tentativa', 'proximo_envio',
        'usuario_criador', 'created_at', 'updated_at'
    ]
    filter_horizontal = ['inquilinos']
    
    fieldsets = (
        ('Informações da Campanha', {
            'fields': ('nome_campanha', 'descricao', 'template')
        }),
        ('Destinatários', {
            'fields': ('inquilinos', 'filtro_personalizado')
        }),
        ('Agendamento', {
            'fields': (
                'data_envio', 'recorrencia', 'intervalo_recorrencia',
                'data_fim_recorrencia'
            )
        }),
        ('Configurações', {
            'fields': (
                'prioridade', 'max_tentativas', 'intervalo_tentativas'
            )
        }),
        ('Status', {
            'fields': (
                'status', 'tentativas_realizadas', 'ultima_tentativa',
                'proximo_envio'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('usuario_criador', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criador = request.user
        super().save_model(request, obj, form, change)

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = [
        'assunto_truncado', 'inquilino', 'canal', 'status',
        'prioridade', 'data_envio', 'tracking_display'
    ]
    list_filter = [
        'status', 'canal', 'prioridade', 'data_envio', 'created_at'
    ]
    search_fields = [
        'assunto', 'corpo', 'inquilino__nome', 'destinatario'
    ]
    readonly_fields = [
        'tracking_id', 'data_envio', 'data_entrega', 'data_abertura',
        'data_clique', 'ip_abertura', 'user_agent', 'log_tentativas',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'template', 'agendamento', 'inquilino', 'contrato'
            )
        }),
        ('Conteúdo', {
            'fields': (
                'canal', 'destinatario', 'assunto', 'corpo', 'corpo_html', 'anexos'
            )
        }),
        ('Configurações', {
            'fields': (
                'prioridade', 'tentativas_maximas', 'tentativas_realizadas'
            )
        }),
        ('Status e Tracking', {
            'fields': (
                'status', 'tracking_id', 'data_envio', 'data_entrega',
                'data_abertura', 'data_clique'
            ),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('ip_abertura', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Erros e Logs', {
            'fields': ('erro_envio', 'log_tentativas'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('usuario', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def assunto_truncado(self, obj):
        return obj.assunto[:50] + '...' if len(obj.assunto) > 50 else obj.assunto
    assunto_truncado.short_description = 'Assunto'
    
    def tracking_display(self, obj):
        if obj.tracking_id:
            return format_html(
                '<a href="{}" target="_blank">📊 Ver Tracking</a>',
                f'/admin/tracking/{obj.tracking_id}/'
            )
        return '-'
    tracking_display.short_description = 'Tracking'

@admin.register(EstatisticaNotificacao)
class EstatisticaNotificacaoAdmin(admin.ModelAdmin):
    list_display = [
        'data_referencia', 'periodo', 'canal', 'template',
        'total_enviadas', 'taxa_entrega_display', 'taxa_abertura_display',
        'taxa_clique_display'
    ]
    list_filter = [
        'periodo', 'canal', 'data_referencia', 'template__categoria'
    ]
    search_fields = ['template__nome']
    readonly_fields = [
        'taxa_entrega', 'taxa_abertura', 'taxa_clique', 'taxa_erro',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informações', {
            'fields': ('periodo', 'data_referencia', 'canal', 'template')
        }),
        ('Métricas de Envio', {
            'fields': (
                'total_enviadas', 'total_entregues', 'total_abertas',
                'total_clicadas', 'total_erros', 'total_rejeitadas'
            )
        }),
        ('Taxas Calculadas', {
            'fields': (
                'taxa_entrega', 'taxa_abertura', 'taxa_clique', 'taxa_erro'
            ),
            'classes': ('collapse',)
        }),
        ('Tempo Médio', {
            'fields': ('tempo_medio_abertura', 'tempo_medio_clique'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def taxa_entrega_display(self, obj):
        return f"{obj.taxa_entrega:.1f}%"
    taxa_entrega_display.short_description = 'Taxa Entrega'
    
    def taxa_abertura_display(self, obj):
        return f"{obj.taxa_abertura:.1f}%"
    taxa_abertura_display.short_description = 'Taxa Abertura'
    
    def taxa_clique_display(self, obj):
        return f"{obj.taxa_clique:.1f}%"
    taxa_clique_display.short_description = 'Taxa Clique'


@admin.register(CobrancaAutomaticaLog)
class CobrancaAutomaticaLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'tenant', 'tipo', 'nivel', 'inquilino', 'contrato', 'status', 'destinatario']
    list_filter = ['status', 'tipo', 'nivel', 'created_at', 'tenant']
    search_fields = ['inquilino__nome', 'destinatario', 'provider_message_id']
    readonly_fields = ['created_at']


# Modelo legado
@admin.register(TipoNotificacao)
class TipoNotificacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'template_assunto', 'template_corpo']
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'ativo')
        }),
        ('Templates (Legado)', {
            'fields': ('template_assunto', 'template_corpo'),
            'description': 'Este é um modelo legado. Use TemplateNotificacao para novos templates.'
        })
    )
