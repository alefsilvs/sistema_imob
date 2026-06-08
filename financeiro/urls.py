from django.urls import path, include
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Parcelas
    path('parcelas/', views.listar_parcelas, name='listar_parcelas'),
    path('parcelas/<int:pk>/', views.detalhes_parcela, name='detalhes_parcela'),
    path('parcelas/<int:pk>/editar/', views.editar_parcela, name='editar_parcela'),
    path('parcelas/<int:pk>/marcar-pago/', views.marcar_pago, name='marcar_pago'),
    
    # IPTU
    path('iptu/', views.listar_iptus, name='listar_iptus'),
    path('iptu/cadastrar/', views.cadastrar_iptu, name='cadastrar_iptu'),
    path('iptu/<int:pk>/', views.detalhes_iptu, name='detalhes_iptu'),
    path('iptu/<int:pk>/editar/', views.editar_iptu, name='editar_iptu'),
    path('iptu/<int:pk>/excluir/', views.excluir_iptu, name='excluir_iptu'),
    path('iptu/relatorios/', views.relatorios_iptu, name='relatorios_iptu'),
    
    # Seguros
    path('seguros/', views.listar_seguros, name='listar_seguros'),
    path('seguros/cadastrar/', views.cadastrar_seguro, name='cadastrar_seguro'),
    path('seguros/<int:pk>/', views.detalhes_seguro, name='detalhes_seguro'),
    path('seguros/<int:pk>/editar/', views.editar_seguro, name='editar_seguro'),
    
    # Repasses
    path('repasses/', views.listar_repasses, name='listar_repasses'),
    
    # Boletos
    path('boletos/gerar/', views.gerar_boletos, name='gerar_boletos'),
    
    # NFe
    path('nfe/', views.listar_nfe, name='listar_nfe'),
    path('nfe/emitir/', views.emitir_nfe, name='emitir_nfe'),
    path('nfe/<int:pk>/', views.detalhes_nfe, name='detalhes_nfe'),
    path('nfe/<int:pk>/pdf/', views.download_nfe_pdf, name='download_nfe_pdf'),
    path('nfe/<int:pk>/xml/', views.download_nfe_xml, name='download_nfe_xml'),
    
    # Sangrias
    path('sangrias/', views.listar_sangrias, name='listar_sangrias'),
    path('sangrias/cadastrar/', views.cadastrar_sangria, name='cadastrar_sangria'),
    path('sangrias/<int:pk>/', views.detalhes_sangria, name='detalhes_sangria'),
    path('sangrias/<int:pk>/editar/', views.editar_sangria, name='editar_sangria'),
    path('sangrias/<int:pk>/excluir/', views.excluir_sangria, name='excluir_sangria'),
    path('sangrias/<int:pk>/marcar-paga/', views.marcar_sangria_paga, name='marcar_sangria_paga'),
    path('sangrias/<int:pk>/cancelar/', views.cancelar_sangria, name='cancelar_sangria'),
]