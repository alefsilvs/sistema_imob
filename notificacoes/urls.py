from django.urls import path
from . import views

app_name = 'notificacoes'

urlpatterns = [
    path('', views.listar_notificacoes, name='listar'),
    path('enviar/', views.envio_notificacoes_removido, name='enviar'),
    path('agendar/', views.agendar_notificacao, name='agendar'),
    path('detalhes/<int:notificacao_id>/', views.detalhes_notificacao, name='detalhes'),
    
    # Preview de notificações
    path('preview/', views.preview_notificacao, name='preview_notificacao'),
    path('preview-lote/', views.preview_lote, name='preview_lote'),
    path('templates/<int:template_id>/preview/', views.preview_template, name='preview_template'),
    
    # APIs
    path('api/templates/', views.api_templates, name='api_templates'),
    path('api/inquilinos/', views.api_inquilinos, name='api_inquilinos'),
    path('api/robo-cobranca/', views.executar_robo_cobranca, name='robo_cobranca'),
    
    # Agendamentos
    path('agendamentos/', views.listar_agendamentos, name='listar_agendamentos'),
    path('agendamentos/criar/', views.criar_agendamento, name='criar_agendamento'),
    path('agendamentos/<int:agendamento_id>/cancelar/', views.cancelar_agendamento, name='cancelar_agendamento'),
    
    # Filtros avançados
    path('enviar-avancado/', views.envio_notificacoes_removido, name='enviar_avancado'),
    path('api/filtrar-destinatarios/', views.filtrar_destinatarios, name='filtrar_destinatarios'),
    path('api/cidades/', views.obter_cidades, name='obter_cidades'),
    path('api/estatisticas-destinatarios/', views.estatisticas_destinatarios, name='estatisticas_destinatarios'),
    # Estatísticas de entrega e abertura
    path('dashboard/', views.dashboard_estatisticas, name='dashboard_estatisticas'),
    path('rastrear-abertura/<int:notificacao_id>/', views.rastrear_abertura, name='rastrear_abertura'),
    path('rastrear-clique/<int:notificacao_id>/', views.rastrear_clique, name='rastrear_clique'),
    path('estatisticas-detalhadas/', views.estatisticas_detalhadas, name='estatisticas_detalhadas'),
    path('relatorio-performance/', views.relatorio_performance_templates, name='relatorio_performance_templates'),
    path('exportar-estatisticas/', views.exportar_estatisticas_csv, name='exportar_estatisticas_csv'),
    # URLs existentes...
    
    # Gerenciamento de templates
    # Certifique-se de que esta URL existe
    path('templates/', views.listar_templates, name='listar_templates'),
    path('templates/criar/', views.criar_template, name='criar_template'),
    path('templates/<int:template_id>/editar/', views.editar_template, name='editar_template'),
    path('templates/<int:template_id>/excluir/', views.excluir_template, name='excluir_template'),
    path('templates/<int:template_id>/duplicar/', views.duplicar_template, name='duplicar_template'),
    path('templates/<int:template_id>/testar/', views.testar_template, name='testar_template'),
    path('templates/categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    
    # Sistema aprimorado de logs e histórico
    path('logs/', views.logs_detalhados, name='logs_detalhados'),
    path('monitoramento/', views.dashboard_monitoramento, name='dashboard_monitoramento'),
    path('monitoramento/tempo-real/', views.monitoramento_tempo_real, name='monitoramento_tempo_real'),
    path('analise/performance/', views.analise_performance, name='analise_performance'),
    path('relatorio/erros/', views.relatorio_erros_detalhado, name='relatorio_erros_detalhado'),
    path('exportar/logs-avancado/', views.exportar_logs_avancado, name='exportar_logs_avancado'),
    path('limpar/logs-antigos/', views.limpar_logs_antigos, name='limpar_logs_antigos'),

    # WhatsApp Dashboard
    path('whatsapp/', views.whatsapp_dashboard, name='whatsapp_dashboard'),
    path('whatsapp/conectar/', views.whatsapp_conectar, name='whatsapp_conectar'),
    path('whatsapp/api/status/', views.api_whatsapp_status, name='api_whatsapp_status'),
    path('whatsapp/api/qrcode/', views.api_whatsapp_qrcode, name='api_whatsapp_qrcode'),
    path('whatsapp/api/logout/', views.api_whatsapp_logout, name='api_whatsapp_logout'),
    path('whatsapp/api/send/', views.api_whatsapp_send_test, name='api_whatsapp_send_test'),
    path('whatsapp/api/send-campaign/', views.api_whatsapp_send_campaign, name='api_whatsapp_send_campaign'),
    path('whatsapp/api/send-selected/', views.api_whatsapp_send_selected, name='api_whatsapp_send_selected'),
    path('whatsapp/api/start-docker/', views.api_whatsapp_start_docker, name='api_whatsapp_start_docker'),
    path('whatsapp/api/config/save/', views.api_whatsapp_config_save, name='api_whatsapp_config_save'),
    path('whatsapp/api/excecoes/', views.api_whatsapp_excecoes, name='api_whatsapp_excecoes'),
]
