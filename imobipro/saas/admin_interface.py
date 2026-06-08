"""
Interface administrativa para gerenciar clientes e suas APIs Evolution
"""

from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from .models import Tenant
from .evolution_models import EvolutionInstance, EvolutionWebhook, EvolutionMessage
from .evolution_services import tenant_evolution_service
from .database_isolation import TenantDatabaseManager

logger = logging.getLogger(__name__)

class EvolutionInstanceInline(admin.TabularInline):
    """
    Inline para mostrar instâncias Evolution API no admin do Tenant
    """
    model = EvolutionInstance
    extra = 0
    readonly_fields = ('instance_name', 'token', 'status', 'qr_code', 'created_at', 'updated_at')
    
    def has_add_permission(self, request, obj=None):
        return False

class EvolutionWebhookInline(admin.TabularInline):
    """
    Inline para mostrar webhooks Evolution API no admin do Tenant
    """
    model = EvolutionWebhook
    extra = 0
    readonly_fields = ('webhook_url', 'event_type', 'is_active', 'created_at')

@admin.register(Tenant)
class TenantAdminWithEvolution(admin.ModelAdmin):
    """
    Admin customizado para Tenant com funcionalidades Evolution API
    """
    list_display = [
        'nome_empresa', 
        'slug', 
        'status', 
        'plano',
        'evolution_status',
        'evolution_actions'
    ]
    
    list_filter = ['status', 'plano', 'data_criacao']
    search_fields = ['nome_empresa', 'slug', 'subdominio']
    readonly_fields = ['data_criacao', 'evolution_info']
    
    inlines = [EvolutionInstanceInline, EvolutionWebhookInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_empresa', 'slug', 'subdominio', 'usuario_admin')
        }),
        ('Plano e Status', {
            'fields': ('plano', 'status', 'data_expiracao', 'trial_ate')
        }),
        ('Evolution API', {
            'fields': ('evolution_info',),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('configuracoes',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('data_criacao',),
            'classes': ('collapse',)
        })
    )
    
    def evolution_status(self, obj):
        """
        Mostra status da Evolution API
        """
        try:
            instance = EvolutionInstance.objects.filter(tenant=obj).first()
            if instance:
                if instance.status == 'connected':
                    return format_html('<span style="color: green;">✓ Conectado</span>')
                elif instance.status == 'disconnected':
                    return format_html('<span style="color: orange;">⚠ Desconectado</span>')
                else:
                    return format_html('<span style="color: red;">✗ Erro</span>')
            else:
                return format_html('<span style="color: gray;">- Não configurado</span>')
        except:
            return format_html('<span style="color: red;">✗ Erro</span>')
    
    evolution_status.short_description = 'Status Evolution'
    
    def evolution_actions(self, obj):
        """
        Botões de ação para Evolution API
        """
        actions = []
        
        try:
            instance = EvolutionInstance.objects.filter(tenant=obj).first()
            
            if instance:
                # QR Code
                actions.append(
                    f'<a href="{reverse("admin:evolution_qr_code", args=[obj.id])}" '
                    f'class="button" target="_blank">QR Code</a>'
                )
                
                # Reiniciar
                actions.append(
                    f'<a href="{reverse("admin:evolution_restart", args=[obj.id])}" '
                    f'class="button" onclick="return confirm(\'Reiniciar instância?\')">Reiniciar</a>'
                )
                
                # Deletar
                actions.append(
                    f'<a href="{reverse("admin:evolution_delete", args=[obj.id])}" '
                    f'class="button" style="background: #dc3545;" '
                    f'onclick="return confirm(\'Deletar instância?\')">Deletar</a>'
                )
            else:
                # Criar instância
                actions.append(
                    f'<a href="{reverse("admin:evolution_create", args=[obj.id])}" '
                    f'class="button" style="background: #28a745;">Criar Instância</a>'
                )
        except:
            pass
        
        return format_html(' '.join(actions))
    
    evolution_actions.short_description = 'Ações Evolution'
    
    def evolution_info(self, obj):
        """
        Informações detalhadas da Evolution API
        """
        try:
            instance = EvolutionInstance.objects.filter(tenant=obj).first()
            if instance:
                info = f"""
                <strong>Nome da Instância:</strong> {instance.instance_name}<br>
                <strong>Token:</strong> {instance.token}<br>
                <strong>Status:</strong> {instance.status}<br>
                <strong>Criado em:</strong> {instance.created_at}<br>
                <strong>Atualizado em:</strong> {instance.updated_at}<br>
                """
                
                if instance.phone_number:
                    info += f"<strong>Telefone:</strong> {instance.phone_number}<br>"
                
                return format_html(info)
            else:
                return "Nenhuma instância Evolution API configurada"
        except:
            return "Erro ao carregar informações"
    
    evolution_info.short_description = 'Informações Evolution API'
    
    def get_urls(self):
        """
        URLs customizadas para ações Evolution API
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:tenant_id>/evolution/create/',
                self.admin_site.admin_view(self.create_evolution_instance),
                name='evolution_create'
            ),
            path(
                '<int:tenant_id>/evolution/qr-code/',
                self.admin_site.admin_view(self.get_qr_code),
                name='evolution_qr_code'
            ),
            path(
                '<int:tenant_id>/evolution/restart/',
                self.admin_site.admin_view(self.restart_evolution_instance),
                name='evolution_restart'
            ),
            path(
                '<int:tenant_id>/evolution/delete/',
                self.admin_site.admin_view(self.delete_evolution_instance),
                name='evolution_delete'
            ),
            path(
                'evolution/dashboard/',
                self.admin_site.admin_view(self.evolution_dashboard),
                name='evolution_dashboard'
            ),
        ]
        return custom_urls + urls
    
    def create_evolution_instance(self, request, tenant_id):
        """
        Cria uma nova instância Evolution API para o tenant
        """
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            # Verificar se já existe instância
            existing = EvolutionInstance.objects.filter(tenant=tenant).first()
            if existing:
                messages.error(request, f'Tenant {tenant.nome_empresa} já possui uma instância Evolution API')
                return redirect('admin:saas_tenant_changelist')
            
            # Criar instância
            instance = tenant_evolution_service.provision_tenant_instance(tenant)
            
            if instance:
                messages.success(request, f'Instância Evolution API criada com sucesso para {tenant.nome_empresa}')
            else:
                messages.error(request, f'Erro ao criar instância Evolution API para {tenant.nome_empresa}')
                
        except Tenant.DoesNotExist:
            messages.error(request, 'Tenant não encontrado')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('admin:saas_tenant_changelist')
    
    def get_qr_code(self, request, tenant_id):
        """
        Exibe QR Code da instância Evolution API
        """
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            qr_code = tenant_evolution_service.get_qr_code(tenant)
            
            if qr_code:
                context = {
                    'tenant': tenant,
                    'qr_code': qr_code,
                    'title': f'QR Code - {tenant.nome_empresa}'
                }
                return render(request, 'admin/evolution_qr_code.html', context)
            else:
                messages.error(request, 'Não foi possível obter o QR Code')
                
        except Tenant.DoesNotExist:
            messages.error(request, 'Tenant não encontrado')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('admin:saas_tenant_changelist')
    
    def restart_evolution_instance(self, request, tenant_id):
        """
        Reinicia a instância Evolution API
        """
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            # Deletar e recriar instância
            tenant_evolution_service.cleanup_tenant_instance(tenant)
            instance = tenant_evolution_service.provision_tenant_instance(tenant)
            
            if instance:
                messages.success(request, f'Instância Evolution API reiniciada para {tenant.nome_empresa}')
            else:
                messages.error(request, f'Erro ao reiniciar instância Evolution API para {tenant.nome_empresa}')
                
        except Tenant.DoesNotExist:
            messages.error(request, 'Tenant não encontrado')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('admin:saas_tenant_changelist')
    
    def delete_evolution_instance(self, request, tenant_id):
        """
        Deleta a instância Evolution API
        """
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            success = tenant_evolution_service.cleanup_tenant_instance(tenant)
            
            if success:
                messages.success(request, f'Instância Evolution API removida para {tenant.nome_empresa}')
            else:
                messages.warning(request, f'Nenhuma instância encontrada para {tenant.nome_empresa}')
                
        except Tenant.DoesNotExist:
            messages.error(request, 'Tenant não encontrado')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
        
        return redirect('admin:saas_tenant_changelist')
    
    def evolution_dashboard(self, request):
        """
        Dashboard com estatísticas das instâncias Evolution API
        """
        try:
            # Estatísticas gerais
            total_tenants = Tenant.objects.count()
            total_instances = EvolutionInstance.objects.count()
            connected_instances = EvolutionInstance.objects.filter(status='connected').count()
            disconnected_instances = EvolutionInstance.objects.filter(status='disconnected').count()
            
            # Instâncias por status
            instances_by_status = {}
            for status in ['connected', 'disconnected', 'error']:
                count = EvolutionInstance.objects.filter(status=status).count()
                instances_by_status[status] = count
            
            # Últimas mensagens
            recent_messages = EvolutionMessage.objects.select_related('tenant').order_by('-created_at')[:10]
            
            context = {
                'title': 'Dashboard Evolution API',
                'total_tenants': total_tenants,
                'total_instances': total_instances,
                'connected_instances': connected_instances,
                'disconnected_instances': disconnected_instances,
                'instances_by_status': instances_by_status,
                'recent_messages': recent_messages,
            }
            
            return render(request, 'admin/evolution_dashboard.html', context)
            
        except Exception as e:
            messages.error(request, f'Erro ao carregar dashboard: {str(e)}')
            return redirect('admin:index')


@admin.register(EvolutionInstance)
class EvolutionInstanceAdmin(admin.ModelAdmin):
    """
    Admin para instâncias Evolution API
    """
    list_display = ['instance_name', 'tenant', 'status', 'phone_number', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['instance_name', 'tenant__nome_empresa', 'phone_number']
    readonly_fields = ['instance_name', 'token', 'qr_code', 'created_at', 'updated_at']


@admin.register(EvolutionMessage)
class EvolutionMessageAdmin(admin.ModelAdmin):
    """
    Admin para mensagens Evolution API
    """
    list_display = ['tenant', 'message_type', 'from_number', 'to_number', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['tenant__nome_empresa', 'from_number', 'to_number', 'content']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False