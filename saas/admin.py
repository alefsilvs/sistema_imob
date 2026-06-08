from django.contrib import admin
from .models import PlanoComercial, Tenant, ConfiguracaoTenant, RegistroUso, Faturamento

# Importar admin customizado para Evolution API
from .admin_interface import TenantAdminWithEvolution, EvolutionInstanceAdmin, EvolutionMessageAdmin
from .evolution_models import EvolutionInstance, EvolutionWebhook, EvolutionMessage

@admin.register(PlanoComercial)
class PlanoComercialAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'preco_mensal', 'max_usuarios', 'max_imoveis', 'ativo']
    list_filter = ['tipo', 'ativo', 'suporte_prioritario', 'backup_automatico']
    search_fields = ['nome']
    ordering = ['tipo', 'preco_mensal']

# Desregistrar o admin padrão do Tenant se já estiver registrado
try:
    admin.site.unregister(Tenant)
except admin.sites.NotRegistered:
    pass

# Registrar o admin customizado com Evolution API
admin.site.register(Tenant, TenantAdminWithEvolution)

@admin.register(ConfiguracaoTenant)
class ConfiguracaoTenantAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'email_contato', 'telefone_contato']
    list_filter = ['tenant']
    search_fields = ['tenant__nome_empresa', 'email_contato']
    ordering = ['tenant']

@admin.register(RegistroUso)
class RegistroUsoAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'data', 'usuarios_ativos', 'imoveis_cadastrados', 'contratos_ativos']
    list_filter = ['data', 'tenant']
    search_fields = ['tenant__nome_empresa']
    ordering = ['-data']

@admin.register(Faturamento)
class FaturamentoAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'periodo_inicio', 'periodo_fim', 'valor', 'status', 'data_vencimento']
    list_filter = ['status', 'data_vencimento', 'periodo_inicio']
    search_fields = ['tenant__nome_empresa']
    ordering = ['-periodo_inicio']

# Registrar modelos Evolution API
admin.site.register(EvolutionWebhook)
