# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este software é propriedade exclusiva do autor.
Proibida a reprodução, distribuição ou comercialização não autorizada.
Violações serão processadas nos termos da lei.

Licença: Proprietária - Veja LICENSE para mais detalhes
"""

from django.urls import path
from . import views

app_name = 'powerbi'

urlpatterns = [
    # Endpoints principais das APIs
    path('api/dashboard/', views.DashboardGeralAPIView.as_view(), name='dashboard-api'),
    path('api/imoveis/', views.ImoveisPowerBIAPIView.as_view(), name='imoveis-api'),
    path('api/financeiro/', views.FinanceiroPowerBIAPIView.as_view(), name='financeiro-api'),
    path('api/contratos/', views.ContratosPowerBIAPIView.as_view(), name='contratos-api'),
    path('api/manutencao/', views.ManutencaoPowerBIAPIView.as_view(), name='manutencao-api'),
    path('api/inquilinos/', views.InquilinosPowerBIAPIView.as_view(), name='inquilinos-api'),
    path('api/proprietarios/', views.ProprietariosPowerBIAPIView.as_view(), name='proprietarios-api'),
    
    # Endpoints de utilidade
    path('api/datasets/', views.powerbi_datasets, name='datasets'),
    path('api/health/', views.powerbi_health, name='health'),
    
    # Endpoints de configuração
    path('api/config/', views.PowerBIConfigView.as_view(), name='config'),
    path('api/test-connection/', views.test_powerbi_connection, name='test-connection'),
]