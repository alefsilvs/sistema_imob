from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import PlanoAssinatura, AssinaturaUsuario, HistoricoPagamento, ConfiguracaoSistema

@admin.register(PlanoAssinatura)
class PlanoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'preco_formatado', 'duracao_dias', 'max_imoveis', 'max_contratos', 'ativo', 'created_at']
    list_filter = ['tipo', 'ativo', 'created_at']
    search_fields = ['nome', 'descricao']
    ordering = ['preco']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'tipo', 'preco', 'ativo')
        }),
        ('Configurações do Plano', {
            'fields': ('duracao_dias', 'max_imoveis', 'max_contratos', 'max_usuarios')
        }),
    )
    
    def preco_formatado(self, obj):
        return f'R$ {obj.preco:,.2f}'
    preco_formatado.short_description = 'Preço'
    preco_formatado.admin_order_field = 'preco'

@admin.register(AssinaturaUsuario)
class AssinaturaUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'plano', 'status_badge', 'data_inicio', 'data_fim', 
        'dias_restantes_display', 'valor_pago_formatado', 'renovacao_automatica'
    ]
    list_filter = ['status', 'plano__tipo', 'renovacao_automatica', 'data_inicio', 'data_fim']
    search_fields = ['usuario__username', 'usuario__email', 'plano__nome']
    ordering = ['-data_inicio']
    readonly_fields = ['created_at', 'updated_at', 'dias_restantes_display', 'esta_ativa_display']
    
    fieldsets = (
        ('Informações da Assinatura', {
            'fields': ('usuario', 'plano', 'status', 'valor_pago', 'forma_pagamento')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim', 'data_cancelamento')
        }),
        ('Configurações', {
            'fields': ('renovacao_automatica', 'observacoes')
        }),
        ('Informações do Sistema', {
            'fields': ('esta_ativa_display', 'dias_restantes_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'ATIVA': 'green',
            'TRIAL': 'blue',
            'VENCIDA': 'red',
            'CANCELADA': 'gray',
            'SUSPENSA': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        if dias <= 0:
            return format_html('<span style="color: red;">Expirada</span>')
        elif dias <= 7:
            return format_html('<span style="color: orange;">{} dias</span>', dias)
        else:
            return f'{dias} dias'
    dias_restantes_display.short_description = 'Dias Restantes'
    
    def esta_ativa_display(self, obj):
        if obj.esta_ativa:
            return format_html('<span style="color: green;">✓ Ativa</span>')
        else:
            return format_html('<span style="color: red;">✗ Inativa</span>')
    esta_ativa_display.short_description = 'Está Ativa'
    
    def valor_pago_formatado(self, obj):
        return f'R$ {obj.valor_pago:,.2f}'
    valor_pago_formatado.short_description = 'Valor Pago'
    valor_pago_formatado.admin_order_field = 'valor_pago'
    
    actions = ['renovar_assinaturas', 'cancelar_assinaturas', 'ativar_assinaturas']
    
    def renovar_assinaturas(self, request, queryset):
        count = 0
        for assinatura in queryset:
            if assinatura.status in ['VENCIDA', 'CANCELADA']:
                assinatura.renovar()
                count += 1
        self.message_user(request, f'{count} assinaturas renovadas com sucesso.')
    renovar_assinaturas.short_description = 'Renovar assinaturas selecionadas'
    
    def cancelar_assinaturas(self, request, queryset):
        count = 0
        for assinatura in queryset:
            if assinatura.status == 'ATIVA':
                assinatura.cancelar('Cancelamento em massa pelo admin')
                count += 1
        self.message_user(request, f'{count} assinaturas canceladas.')
    cancelar_assinaturas.short_description = 'Cancelar assinaturas selecionadas'
    
    def ativar_assinaturas(self, request, queryset):
        count = queryset.update(status='ATIVA')
        self.message_user(request, f'{count} assinaturas ativadas.')
    ativar_assinaturas.short_description = 'Ativar assinaturas selecionadas'

@admin.register(HistoricoPagamento)
class HistoricoPagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'assinatura_usuario', 'valor_formatado', 'status_badge', 
        'forma_pagamento', 'data_pagamento', 'data_vencimento', 'created_at'
    ]
    list_filter = ['status', 'forma_pagamento', 'data_pagamento', 'data_vencimento', 'created_at']
    search_fields = [
        'assinatura__usuario__username', 'assinatura__usuario__email', 
        'referencia_externa', 'observacoes'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': ('assinatura', 'valor', 'status', 'forma_pagamento')
        }),
        ('Referências', {
            'fields': ('referencia_externa', 'observacoes')
        }),
        ('Datas', {
            'fields': ('data_pagamento', 'data_vencimento', 'created_at', 'updated_at')
        }),
    )
    
    def assinatura_usuario(self, obj):
        return obj.assinatura.usuario.username
    assinatura_usuario.short_description = 'Usuário'
    assinatura_usuario.admin_order_field = 'assinatura__usuario__username'
    
    def valor_formatado(self, obj):
        return f'R$ {obj.valor:,.2f}'
    valor_formatado.short_description = 'Valor'
    valor_formatado.admin_order_field = 'valor'
    
    def status_badge(self, obj):
        colors = {
            'PENDENTE': 'orange',
            'APROVADO': 'green',
            'REJEITADO': 'red',
            'CANCELADO': 'gray',
            'ESTORNADO': 'purple',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    actions = ['aprovar_pagamentos', 'rejeitar_pagamentos']
    
    def aprovar_pagamentos(self, request, queryset):
        count = 0
        for pagamento in queryset.filter(status='PENDENTE'):
            pagamento.status = 'APROVADO'
            pagamento.data_pagamento = timezone.now()
            pagamento.save()
            
            # Ativar assinatura
            assinatura = pagamento.assinatura
            assinatura.status = 'ATIVA'
            assinatura.save()
            count += 1
        
        self.message_user(request, f'{count} pagamentos aprovados e assinaturas ativadas.')
    aprovar_pagamentos.short_description = 'Aprovar pagamentos selecionados'
    
    def rejeitar_pagamentos(self, request, queryset):
        count = queryset.filter(status='PENDENTE').update(status='REJEITADO')
        self.message_user(request, f'{count} pagamentos rejeitados.')
    rejeitar_pagamentos.short_description = 'Rejeitar pagamentos selecionados'

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'trial_dias', 'permitir_trial', 'bloquear_acesso_vencido', 'dias_graca']
    
    fieldsets = (
        ('Configurações de Trial', {
            'fields': ('permitir_trial', 'trial_dias')
        }),
        ('Configurações de Bloqueio', {
            'fields': ('bloquear_acesso_vencido', 'dias_graca', 'mensagem_bloqueio')
        }),
        ('Configurações de Cobrança', {
            'fields': ('email_cobranca',)
        }),
    )
    
    def has_add_permission(self, request):
        # Só permite criar se não existir nenhuma configuração
        return not ConfiguracaoSistema.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Não permite deletar a configuração
        return False

# Customização do admin site
admin.site.site_header = 'ImobilPro - Sistema de Assinaturas'
admin.site.site_title = 'ImobilPro Admin'
admin.site.index_title = 'Gerenciamento de Assinaturas'
