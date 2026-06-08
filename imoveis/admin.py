from django.contrib import admin
from .models import Imovel, FotoImovel

@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'endereco', 'tipo', 'proprietario', 'valor_aluguel', 'status', 'disponivel']
    list_filter = ['tipo', 'finalidade', 'status', 'disponivel', 'mobiliado']
    search_fields = ['codigo', 'endereco', 'bairro', 'cidade', 'proprietario__nome']
    list_editable = ['status', 'disponivel']
    ordering = ['codigo']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'proprietario', 'tipo', 'finalidade')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Características', {
            'fields': ('area_total', 'area_construida', 'quartos', 'banheiros', 'vagas_garagem', 'mobiliado')
        }),
        ('Valores', {
            'fields': ('valor_aluguel', 'valor_condominio', 'valor_iptu', 'valor_seguro')
        }),
        ('Documentação', {
            'fields': ('inscricao_municipal', 'matricula')
        }),
        ('Outros', {
            'fields': ('descricao', 'status', 'disponivel')
        }),
    )

@admin.register(FotoImovel)
class FotoImovelAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'descricao', 'principal', 'created_at']
    list_filter = ['principal', 'created_at']
    search_fields = ['imovel__codigo', 'descricao']
    list_editable = ['principal']
    ordering = ['-created_at']
