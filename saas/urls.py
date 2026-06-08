from django.urls import path
from . import views

app_name = 'saas'

urlpatterns = [
    path('', views.PlanosPublicosView.as_view(), name='planos_publicos'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('escolher-pagamento/', views.EscolherPagamentoView.as_view(), name='escolher_pagamento'),
    path('configuracao-inicial/', views.ConfiguracaoInicialView.as_view(), name='configuracao_inicial'),
    path('processar-pagamento/', views.processar_pagamento_plano, name='processar_pagamento'),
    path('pagamento/<str:token>/', views.PagamentoPlanoView.as_view(), name='pagamento_plano'),
    path('pagamento-pix/<str:token>/', views.pagamento_pix_view, name='pagamento_pix'),
    path('verificar-pagamento/<str:token>/', views.verificar_pagamento_pix, name='verificar_pagamento'),
    path('processar-pagamento-final/<str:token>/', views.processar_pagamento_plano_final, name='processar_pagamento_final'),
    
    # Webhooks
    path('webhook/pagamento/', views.webhook_pagamento, name='webhook_pagamento'),
    
    # Verificação de email
    path('email-enviado/', views.EmailEnviadoView.as_view(), name='email_enviado'),
    path('verificar-email/<str:token>/', views.verificar_email, name='verificar_email'),
    path('reenviar-email/', views.reenviar_email_verificacao, name='reenviar_email'),
    
    # Dashboard administrativo
    path('dashboard/', views.dashboard_saas, name='dashboard'),
]
