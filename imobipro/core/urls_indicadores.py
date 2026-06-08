from django.urls import path
from . import views_indicadores

app_name = 'indicadores'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', views_indicadores.dashboard_indicadores, name='dashboard'),
    
    # Detalhes dos indicadores
    path('inadimplencia/<str:data_referencia>/', 
         views_indicadores.indicador_inadimplencia_detalhes, 
         name='inadimplencia_detalhes'),
    
    path('imobiliario/<str:data_referencia>/', 
         views_indicadores.indicador_imobiliario_detalhes, 
         name='imobiliario_detalhes'),
    
    path('financeiro/<str:data_referencia>/', 
         views_indicadores.indicador_financeiro_detalhes, 
         name='financeiro_detalhes'),
    
    # API para dados dos indicadores
    path('api/resumo/', views_indicadores.api_indicadores_resumo, name='api_resumo'),
    
    # Atualização de indicadores
    path('atualizar/', views_indicadores.atualizar_indicadores, name='atualizar'),
    
    # Configuração do dashboard
    path('configurar/', views_indicadores.configurar_dashboard, name='configurar'),
]