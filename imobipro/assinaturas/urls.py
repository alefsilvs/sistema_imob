from django.urls import path
from . import views

app_name = 'assinaturas'

urlpatterns = [
    # Páginas principais
    path('planos/', views.planos_assinatura, name='planos'),
    path('assinar/<int:plano_id>/', views.assinar_plano, name='assinar'),
    path('pagamento/<int:pagamento_id>/', views.pagamento, name='pagamento'),
    path('confirmar-pagamento/<int:pagamento_id>/', views.confirmar_pagamento, name='confirmar_pagamento'),
    
    # Gerenciamento de assinatura
    path('minha-assinatura/', views.minha_assinatura, name='minha_assinatura'),
    path('renovar/', views.renovar_assinatura, name='renovar'),
    path('cancelar/', views.cancelar_assinatura, name='cancelar'),
    path('historico/', views.historico_pagamentos, name='historico'),
    
    # Páginas especiais
    path('bloqueado/', views.acesso_bloqueado, name='bloqueado'),
    path('bloqueio/', views.bloqueio_acesso, name='bloqueio_acesso'),
    path('upgrade/', views.upgrade_plano, name='upgrade_plano'),
    path('renovar/<int:assinatura_id>/', views.renovar_assinatura, name='renovar_assinatura'),
    
    # Webhooks
    path('webhook/pagamento/', views.webhook_pagamento, name='webhook_pagamento'),
    
    # ===== URLs ESPECÍFICAS PARA PAGAMENTOS DE ASSINATURA =====
    path('pagamento-assinatura/criar/<int:plano_id>/', views.criar_pagamento_assinatura, name='criar_pagamento_assinatura'),
    path('pagamento-assinatura/processar/<str:token>/', views.processar_pagamento_assinatura, name='processar_pagamento_assinatura'),
    path('pagamento-assinatura/confirmar/<str:token>/', views.confirmar_pagamento_assinatura, name='confirmar_pagamento_assinatura'),
    path('pagamento-assinatura/listar/', views.listar_pagamentos_assinatura, name='listar_pagamentos_assinatura'),
    path('pagamento-assinatura/relatorio/', views.relatorio_pagamentos_assinatura, name='relatorio_pagamentos_assinatura'),
    path('webhook/pagamento-assinatura/', views.webhook_pagamento_assinatura, name='webhook_pagamento_assinatura'),
]