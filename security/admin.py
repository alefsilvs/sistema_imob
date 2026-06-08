from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import MasterUser, SecurityLog, LoginAttempt, BlockedIP, SystemSetting

# Customizar o admin do User para mostrar informações de segurança
class MasterUserInline(admin.StackedInline):
    model = MasterUser
    can_delete = False
    verbose_name_plural = 'Configurações Master'
    readonly_fields = ('hardware_fingerprint', 'created_at')
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Configurações de Segurança', {
            'fields': ('security_level', 'two_factor_enabled', 'authorized_ips')
        }),
        ('Informações do Sistema', {
            'fields': ('hardware_fingerprint', 'created_at'),
            'classes': ('collapse',)
        }),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (MasterUserInline,)
    
    def get_inlines(self, request, obj):
        # Só mostrar inline para usuários que têm perfil master
        if obj and hasattr(obj, 'master_profile'):
            return self.inlines
        return []

# Re-registrar o User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(MasterUser)
class MasterUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'security_level', 'two_factor_enabled', 'is_active', 'created_at')
    list_filter = ('security_level', 'two_factor_enabled', 'is_active', 'created_at')
    readonly_fields = ('hardware_fingerprint', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'is_active')
        }),
        ('Configurações de Segurança', {
            'fields': ('security_level', 'two_factor_enabled', 'authorized_ips')
        }),
        ('Informações do Sistema', {
            'fields': ('hardware_fingerprint', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    

    
    def has_add_permission(self, request):
        # Só permitir um usuário master
        return not MasterUser.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Não permitir deletar o último usuário master
        return False

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'user', 'severity', 'ip_address', 'short_description')
    list_filter = ('severity', 'event_type', 'timestamp')
    search_fields = ('description', 'ip_address', 'user__username')
    readonly_fields = ('timestamp', 'user', 'event_type', 'description', 'ip_address', 'user_agent', 'severity', 'metadata')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def short_description(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    short_description.short_description = 'Descrição'
    
    def has_add_permission(self, request):
        return False  # Logs são criados automaticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs são imutáveis
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Só superuser pode deletar logs
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    # Adicionar ações personalizadas
    actions = ['export_logs']
    
    def export_logs(self, request, queryset):
        # Implementar exportação de logs
        pass
    export_logs.short_description = "Exportar logs selecionados"

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'ip_address', 'username', 'success', 'user_agent_short')
    list_filter = ('success', 'timestamp')
    search_fields = ('ip_address', 'username')
    readonly_fields = ('timestamp', 'ip_address', 'username', 'success', 'user_agent')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def user_agent_short(self, obj):
        return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def has_add_permission(self, request):
        return False  # Tentativas são criadas automaticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # Tentativas são imutáveis
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    # Adicionar estatísticas
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Estatísticas rápidas
        total_attempts = LoginAttempt.objects.count()
        failed_attempts = LoginAttempt.objects.filter(success=False).count()
        success_rate = ((total_attempts - failed_attempts) / total_attempts * 100) if total_attempts > 0 else 0
        
        extra_context['stats'] = {
            'total_attempts': total_attempts,
            'failed_attempts': failed_attempts,
            'success_rate': round(success_rate, 2)
        }
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'reason', 'blocked_at', 'blocked_until', 'is_currently_blocked')
    list_filter = ('blocked_at', 'blocked_until')
    search_fields = ('ip_address', 'reason')
    readonly_fields = ('blocked_at',)
    ordering = ('-blocked_at',)
    
    def is_currently_blocked(self, obj):
        return obj.is_blocked()
    is_currently_blocked.boolean = True
    is_currently_blocked.short_description = 'Bloqueado Atualmente'
    
    # Ações personalizadas
    actions = ['unblock_ips', 'extend_block']
    
    def unblock_ips(self, request, queryset):
        count = 0
        for blocked_ip in queryset:
            if blocked_ip.is_blocked():
                blocked_ip.blocked_until = timezone.now()
                blocked_ip.save()
                count += 1
        
        self.message_user(request, f'{count} IPs desbloqueados com sucesso.')
    unblock_ips.short_description = "Desbloquear IPs selecionados"
    
    def extend_block(self, request, queryset):
        count = 0
        for blocked_ip in queryset:
            if blocked_ip.is_blocked():
                blocked_ip.blocked_until = blocked_ip.blocked_until + timezone.timedelta(hours=24)
                blocked_ip.save()
                count += 1
        
        self.message_user(request, f'Bloqueio estendido por 24h para {count} IPs.')
    extend_block.short_description = "Estender bloqueio por 24h"

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)
    ordering = ('key',)
    
    def has_delete_permission(self, request, obj=None):
        # Não permitir deletar configurações críticas
        if obj and obj.key in ['max_login_attempts', 'lockout_duration', 'session_timeout']:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        # Tornar a chave readonly para edição
        if obj:  # Editando
            return self.readonly_fields + ('key',)
        return self.readonly_fields

# Customizar o site admin
admin.site.site_header = "Sistema Imobiliário - Administração de Segurança"
admin.site.site_title = "Segurança Admin"
admin.site.index_title = "Painel de Controle de Segurança"

# Adicionar CSS customizado
class SecurityAdminMixin:
    class Media:
        css = {
            'all': ('security/admin.css',)
        }
        js = ('security/admin.js',)

# Aplicar o mixin aos admins
for admin_class in [SecurityLogAdmin, LoginAttemptAdmin, BlockedIPAdmin, MasterUserAdmin]:
    admin_class.__bases__ = (SecurityAdminMixin,) + admin_class.__bases__