from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'pagamentos'

urlpatterns = [
    # Página principal de pagamento
    path('pagar/<str:token>/', views.PagamentoView.as_view(), name='pagamento'),
    
    # Página profissional de pagamento
    path('pro/<str:token>/', views.PagamentoProfissionalView.as_view(), name='pagamento_profissional'),
    path('sucesso/<str:token>/', views.SucessoProfissionalView.as_view(), name='sucesso_profissional'),
    path('teste/<str:token>/', TemplateView.as_view(template_name='pagamentos/pagamento_teste.html'), name='pagamento_teste'),
    path('informacoes-cobranca/', TemplateView.as_view(template_name='pagamentos/informacoes_cobranca.html'), name='informacoes_cobranca'),
    
    # Pagamento de assinatura após configuração inicial
    path('assinatura/', views.PagamentoAssinaturaView.as_view(), name='pagamento_assinatura'),
    
    # Processamento de pagamentos
    path('processar/<str:token>/', views.processar_pagamento, name='processar_pagamento'),
    
    # Páginas de resultado
    path('sucesso/<str:token>/', views.sucesso, name='sucesso'),
    path('aguardar/<str:token>/', views.aguardar_confirmacao, name='aguardar_confirmacao'),
    path('boleto/<str:token>/', views.boleto, name='boleto'),
    
    # APIs
    path('status/<str:token>/', views.status_pagamento, name='status_pagamento'),
    path('webhook/confirmacao/', views.webhook_confirmacao, name='webhook_confirmacao'),
    
    # ===== RELATÓRIOS ESPECÍFICOS POR TIPO DE PAGAMENTO =====
    path('relatorio/inquilinos/', views.relatorio_pagamentos_inquilinos, name='relatorio_inquilinos'),
    path('relatorio/outros/', views.relatorio_pagamentos_outros, name='relatorio_outros'),
    path('dashboard/separado/', views.dashboard_pagamentos_separados, name='dashboard_separado'),
]