from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    # Vistorias
    path('vistorias/', views.listar_vistorias, name='listar_vistorias'),
    path('vistorias/agendar/', views.agendar_vistoria, name='agendar_vistoria'),
    path('vistorias/<int:pk>/', views.detalhes_vistoria, name='detalhes_vistoria'),
    path('vistorias/<int:pk>/editar/', views.editar_vistoria, name='editar_vistoria'),
    path('vistorias/<int:pk>/cancelar/', views.cancelar_vistoria, name='cancelar_vistoria'),
    path('vistorias/<int:pk>/realizar/', views.realizar_vistoria, name='realizar_vistoria'),
    
    # Repositório Digital
    path('repositorio/', views.repositorio_dashboard, name='repositorio_dashboard'),
    path('repositorio/documentos/', views.listar_documentos, name='listar_documentos'),
    path('repositorio/upload/', views.upload_documento, name='upload_documento'),
    path('repositorio/documento/<int:documento_id>/', views.visualizar_documento, name='visualizar_documento'),
    path('repositorio/documento/<int:documento_id>/download/', views.download_documento, name='download_documento'),
    path('repositorio/documento/<int:documento_id>/compartilhar/', views.compartilhar_documento, name='compartilhar_documento'),
    path('repositorio/categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    
    # APIs para tipos de documentos
    path('repositorio/tipo/<int:tipo_id>/', views.obter_tipo_documento, name='obter_tipo_documento'),
    path('repositorio/tipo/<int:tipo_id>/editar/', views.editar_tipo_documento, name='editar_tipo_documento'),
    path('repositorio/tipo/<int:tipo_id>/excluir/', views.excluir_tipo_documento, name='excluir_tipo_documento'),
]