from django.urls import path
from . import views_suporte

urlpatterns = [
    # Dashboard
    path('', views_suporte.dashboard_suporte, name='dashboard_suporte'),
    path('dashboard/', views_suporte.dashboard_suporte, name='dashboard_suporte_alt'),
    
    # Gestão de Tickets
    path('tickets/', views_suporte.listar_tickets, name='listar_tickets'),
    path('tickets/criar/', views_suporte.criar_ticket, name='criar_ticket'),
    path('tickets/<int:ticket_id>/', views_suporte.detalhes_ticket, name='detalhes_ticket'),
    path('tickets/<int:ticket_id>/responder/', views_suporte.responder_ticket, name='responder_ticket'),
    path('tickets/<int:ticket_id>/atribuir/', views_suporte.atribuir_ticket, name='atribuir_ticket'),
    path('tickets/<int:ticket_id>/avaliar/', views_suporte.avaliar_ticket, name='avaliar_ticket'),
    
    # Anexos
    path('anexos/<int:anexo_id>/download/', views_suporte.download_anexo, name='download_anexo'),
    
    # Base de Conhecimento
    path('conhecimento/', views_suporte.base_conhecimento, name='base_conhecimento'),
    path('conhecimento/<int:artigo_id>/', views_suporte.artigo_conhecimento, name='artigo_conhecimento'),
    path('conhecimento/<int:artigo_id>/avaliar/', views_suporte.avaliar_artigo, name='avaliar_artigo'),
    
    # Relatórios
    path('relatorios/', views_suporte.relatorios_suporte, name='relatorios_suporte'),
    
    # Configurações
    path('configuracoes/', views_suporte.configuracoes_suporte, name='configuracoes_suporte'),
    
    # API
    path('api/criar-ticket/', views_suporte.api_criar_ticket, name='api_criar_ticket'),
    path('api/ticket/<str:numero>/status/', views_suporte.api_status_ticket, name='api_status_ticket'),
]