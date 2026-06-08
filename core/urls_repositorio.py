from django.urls import path
from . import views_repositorio

app_name = 'repositorio'

urlpatterns = [
    # Dashboard do repositório
    path('', views_repositorio.repositorio_dashboard, name='dashboard'),
    
    # Gestão de documentos
    path('documentos/', views_repositorio.listar_documentos, name='listar_documentos'),
    path('documentos/upload/', views_repositorio.upload_documento, name='upload_documento'),
    path('documentos/<int:documento_id>/', views_repositorio.detalhes_documento, name='detalhes_documento'),
    path('documentos/<int:documento_id>/download/', views_repositorio.download_documento, name='download_documento'),
    
    # Favoritos
    path('documentos/<int:documento_id>/favorito/', views_repositorio.toggle_favorito, name='toggle_favorito'),
    
    # Compartilhamento
    path('documentos/<int:documento_id>/compartilhar/', views_repositorio.compartilhar_documento, name='compartilhar_documento'),
    path('compartilhado/<uuid:token>/', views_repositorio.documento_compartilhado, name='documento_compartilhado'),
    
    # Gestão de categorias
    path('categorias/', views_repositorio.gerenciar_categorias, name='gerenciar_categorias'),
    
    # Configurações
    path('configuracoes/', views_repositorio.configuracoes_repositorio, name='configuracoes'),
]