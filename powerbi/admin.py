# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import PowerBIConfig, PowerBIDataset, PowerBIAccessLog, PowerBIToken


@admin.register(PowerBIConfig)
class PowerBIConfigAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'criado_em', 'criado_por', 'status_display']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'ativo')
        }),
        ('Configurações Azure AD', {
            'fields': ('tenant_id', 'client_id', 'client_secret', 'workspace_id'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em', 'criado_por'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        if obj.ativo:
            return format_html(
                '<span style="color: green;">✓ Ativo</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inativo</span>'
            )
    status_display.short_description = 'Status'


@admin.register(PowerBIDataset)
class PowerBIDatasetAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'requer_autenticacao', 'criado_em', 'endpoint_link']
    list_filter = ['tipo', 'ativo', 'requer_autenticacao', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações do Dataset', {
            'fields': ('nome', 'tipo', 'descricao')
        }),
        ('Configurações da API', {
            'fields': ('endpoint', 'ativo', 'requer_autenticacao')
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    def endpoint_link(self, obj):
        if obj.endpoint:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.endpoint,
                obj.endpoint
            )
        return '-'
    endpoint_link.short_description = 'Endpoint'


@admin.register(PowerBIAccessLog)
class PowerBIAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'dataset', 'usuario', 'ip_address', 'metodo', 'status_code',
        'tempo_resposta', 'registros_retornados', 'data_acesso'
    ]
    list_filter = [
        'dataset', 'metodo', 'status_code', 'data_acesso'
    ]
    search_fields = ['usuario__username', 'ip_address', 'user_agent']
    readonly_fields = [
        'dataset', 'usuario', 'ip_address', 'user_agent', 'metodo',
        'status_code', 'tempo_resposta', 'registros_retornados', 'data_acesso'
    ]
    date_hierarchy = 'data_acesso'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PowerBIToken)
class PowerBITokenAdmin(admin.ModelAdmin):
    list_display = ['config', 'expira_em', 'is_expired_display', 'criado_em']
    list_filter = ['config', 'expira_em', 'criado_em']
    readonly_fields = ['criado_em', 'is_expired_display', 'expires_soon_display']
    
    fieldsets = (
        ('Token Information', {
            'fields': ('config', 'token', 'refresh_token', 'expira_em')
        }),
        ('Status', {
            'fields': ('is_expired_display', 'expires_soon_display', 'criado_em'),
            'classes': ('collapse',)
        })
    )
    
    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html(
                '<span style="color: red;">✗ Expirado</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ Válido</span>'
            )
    is_expired_display.short_description = 'Status do Token'
    
    def expires_soon_display(self, obj):
        if obj.expires_soon:
            return format_html(
                '<span style="color: orange;">⚠ Expira em breve</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ OK</span>'
            )
    expires_soon_display.short_description = 'Alerta de Expiração'
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Customização do admin site
admin.site.site_header = "Sistema Imobiliário - Power BI Admin"
admin.site.site_title = "Power BI Admin"
admin.site.index_title = "Administração Power BI"
