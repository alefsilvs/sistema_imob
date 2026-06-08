# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Admin para Sistema de Perfis de Usuário
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models_perfil import PerfilUsuario, AbrangenciaPerfil, UsuarioPerfil, LogAlteracaoPerfil


class AbrangenciaPerfilInline(admin.TabularInline):
    model = AbrangenciaPerfil
    extra = 0
    fields = ['modulo', 'acao', 'permitido']
    list_display = ['modulo', 'acao', 'permitido']


class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'total_usuarios', 'criado_em']
    list_filter = ['tipo', 'ativo', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [AbrangenciaPerfilInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'descricao', 'ativo')
        }),
        ('Controle de Tempo', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def total_usuarios(self, obj):
        count = UsuarioPerfil.objects.filter(perfil=obj, ativo=True).count()
        if count > 0:
            url = reverse('admin:core_usuarioperfil_changelist') + f'?perfil__id__exact={obj.id}'
            return format_html('<a href="{}">{} usuários</a>', url, count)
        return '0 usuários'
    total_usuarios.short_description = 'Usuários Ativos'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Criar abrangências padrão para novos perfis
        if not change:  # Novo perfil
            self.criar_abrangencias_padrao(obj)
    
    def criar_abrangencias_padrao(self, perfil):
        """Cria abrangências padrão baseadas no tipo de perfil"""
        abrangencias_padrao = {
            'administrador': {
                'imoveis': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
                'contratos': ['visualizar', 'criar', 'editar', 'excluir', 'aprovar', 'exportar'],
                'financeiro': ['visualizar', 'criar', 'editar', 'excluir', 'aprovar', 'exportar'],
                'pessoas': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
                'manutencao': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
                'documentos': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
                'notificacoes': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
                'relatorios': ['visualizar', 'exportar'],
                'configuracoes': ['visualizar', 'editar'],
                'bancas': ['visualizar', 'criar', 'editar', 'excluir', 'exportar'],
            },
            'gerente': {
                'imoveis': ['visualizar', 'criar', 'editar', 'exportar'],
                'contratos': ['visualizar', 'criar', 'editar', 'aprovar', 'exportar'],
                'financeiro': ['visualizar', 'criar', 'editar', 'aprovar', 'exportar'],
                'pessoas': ['visualizar', 'criar', 'editar', 'exportar'],
                'manutencao': ['visualizar', 'criar', 'editar', 'exportar'],
                'documentos': ['visualizar', 'criar', 'editar', 'exportar'],
                'notificacoes': ['visualizar', 'criar', 'editar', 'exportar'],
                'relatorios': ['visualizar', 'exportar'],
                'bancas': ['visualizar', 'criar', 'editar', 'exportar'],
            },
            'corretor': {
                'imoveis': ['visualizar', 'criar', 'editar'],
                'contratos': ['visualizar', 'criar', 'editar'],
                'pessoas': ['visualizar', 'criar', 'editar'],
                'documentos': ['visualizar', 'criar'],
                'notificacoes': ['visualizar', 'criar'],
                'relatorios': ['visualizar'],
            },
            'financeiro': {
                'financeiro': ['visualizar', 'criar', 'editar', 'aprovar', 'exportar'],
                'contratos': ['visualizar', 'exportar'],
                'pessoas': ['visualizar'],
                'relatorios': ['visualizar', 'exportar'],
            },
            'atendimento': {
                'imoveis': ['visualizar'],
                'contratos': ['visualizar'],
                'pessoas': ['visualizar', 'criar', 'editar'],
                'notificacoes': ['visualizar', 'criar', 'editar'],
                'documentos': ['visualizar'],
            },
            'consulta': {
                'imoveis': ['visualizar'],
                'contratos': ['visualizar'],
                'financeiro': ['visualizar'],
                'pessoas': ['visualizar'],
                'relatorios': ['visualizar'],
            },
        }
        
        permissoes = abrangencias_padrao.get(perfil.tipo, {})
        
        for modulo, acoes in permissoes.items():
            for acao in acoes:
                AbrangenciaPerfil.objects.get_or_create(
                    perfil=perfil,
                    modulo=modulo,
                    acao=acao,
                    defaults={'permitido': True}
                )


class AbrangenciaPerfilAdmin(admin.ModelAdmin):
    list_display = ['perfil', 'modulo', 'acao', 'permitido']
    list_filter = ['perfil', 'modulo', 'acao', 'permitido']
    search_fields = ['perfil__nome']
    list_editable = ['permitido']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('perfil')


class UsuarioPerfilInline(admin.StackedInline):
    model = UsuarioPerfil
    can_delete = False
    verbose_name_plural = 'Perfil do Usuário'
    fields = ['perfil', 'ativo', 'observacoes']
    extra = 0
    max_num = 1


class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'perfil', 'ativo', 'data_atribuicao', 'permissoes_resumo']
    list_filter = ['perfil', 'ativo', 'data_atribuicao']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'perfil__nome']
    readonly_fields = ['data_atribuicao']
    
    fieldsets = (
        ('Usuário e Perfil', {
            'fields': ('usuario', 'perfil', 'ativo')
        }),
        ('Informações Adicionais', {
            'fields': ('observacoes', 'data_atribuicao'),
        }),
    )
    
    def permissoes_resumo(self, obj):
        if not obj.ativo:
            return mark_safe('<span style="color: red;">Inativo</span>')
        
        total_permissoes = AbrangenciaPerfil.objects.filter(
            perfil=obj.perfil, 
            permitido=True
        ).count()
        
        return f"{total_permissoes} permissões"
    permissoes_resumo.short_description = 'Permissões'
    
    def save_model(self, request, obj, form, change):
        # Log da alteração
        if change:
            original = UsuarioPerfil.objects.get(pk=obj.pk)
            if original.perfil != obj.perfil:
                LogAlteracaoPerfil.objects.create(
                    usuario_alterado=obj.usuario,
                    usuario_responsavel=request.user,
                    acao='edicao',
                    perfil_anterior=original.perfil.nome,
                    perfil_novo=obj.perfil.nome,
                    detalhes=f'Perfil alterado de {original.perfil.nome} para {obj.perfil.nome}',
                    ip_address=self.get_client_ip(request)
                )
        else:
            LogAlteracaoPerfil.objects.create(
                usuario_alterado=obj.usuario,
                usuario_responsavel=request.user,
                acao='atribuicao',
                perfil_novo=obj.perfil.nome,
                detalhes=f'Perfil {obj.perfil.nome} atribuído ao usuário',
                ip_address=self.get_client_ip(request)
            )
        
        super().save_model(request, obj, form, change)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogAlteracaoPerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario_alterado', 'acao', 'perfil_anterior', 'perfil_novo', 'usuario_responsavel', 'data_alteracao']
    list_filter = ['acao', 'data_alteracao']
    search_fields = ['usuario_alterado__username', 'usuario_responsavel__username']
    readonly_fields = ['usuario_alterado', 'usuario_responsavel', 'acao', 'perfil_anterior', 
                      'perfil_novo', 'detalhes', 'data_alteracao', 'ip_address']
    date_hierarchy = 'data_alteracao'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Estender o UserAdmin para incluir o perfil
class UserAdmin(BaseUserAdmin):
    inlines = list(BaseUserAdmin.inlines) + [UsuarioPerfilInline]


# Re-registrar o User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)