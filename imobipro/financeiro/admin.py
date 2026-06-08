from django.contrib import admin

# Register your models here.
from .models import IPTU, ParcelaIPTU, Seguro, ParcelaSeguro

@admin.register(IPTU)
class IPTUAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'ano_exercicio', 'valor_total', 'forma_pagamento', 'status']
    list_filter = ['ano_exercicio', 'forma_pagamento', 'status']
    search_fields = ['imovel__codigo', 'imovel__endereco']
    ordering = ['-ano_exercicio']

@admin.register(ParcelaIPTU)
class ParcelaIPTUAdmin(admin.ModelAdmin):
    list_display = ['iptu', 'numero_parcela', 'data_vencimento', 'valor_parcela', 'status']
    list_filter = ['status', 'data_vencimento']
    ordering = ['data_vencimento']

@admin.register(Seguro)
class SeguroAdmin(admin.ModelAdmin):
    list_display = ['numero_apolice', 'imovel', 'tipo_seguro', 'seguradora', 'data_inicio', 'data_fim', 'status']
    list_filter = ['tipo_seguro', 'seguradora', 'status']
    search_fields = ['numero_apolice', 'imovel__codigo', 'seguradora']
    ordering = ['-data_inicio']

@admin.register(ParcelaSeguro)
class ParcelaSeguroAdmin(admin.ModelAdmin):
    list_display = ['seguro', 'numero_parcela', 'data_vencimento', 'valor_parcela', 'status']
    list_filter = ['status', 'data_vencimento']
    ordering = ['data_vencimento']
