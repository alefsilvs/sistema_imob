from django.urls import path, include
from . import views
from . import views_perfil

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # API para elementos editáveis
    path('api/save-editable-changes/', views.save_editable_changes, name='save_editable_changes'),
    
    # URLs para Inquilinos
    path('inquilinos/', views.listar_inquilinos, name='listar_inquilinos'),
    path('inquilinos/cadastrar/', views.cadastrar_inquilino, name='cadastrar_inquilino'),
    path('inquilinos/<int:pk>/', views.detalhes_inquilino, name='detalhes_inquilino'),
    path('inquilinos/<int:pk>/editar/', views.editar_inquilino, name='editar_inquilino'),
    path('inquilinos/<int:pk>/excluir/', views.excluir_inquilino, name='excluir_inquilino'),
    
    # URLs para Proprietários
    path('proprietarios/', views.listar_proprietarios, name='listar_proprietarios'),
    path('proprietarios/cadastrar/', views.cadastrar_proprietario, name='cadastrar_proprietario'),
    path('proprietarios/<int:pk>/', views.detalhes_proprietario, name='detalhes_proprietario'),
    path('proprietarios/<int:pk>/editar/', views.editar_proprietario, name='editar_proprietario'),
    path('proprietarios/<int:pk>/excluir/', views.excluir_proprietario, name='excluir_proprietario'),
    
    # URLs para Perfil e Configurações
    path('perfil/', views.perfil, name='perfil'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    
    # Página sobre o sistema
    path('sobre/', views.sobre_sistema, name='sobre_sistema'),
    
    # URLs para Sistema de Perfis
    path('perfis/', views_perfil.listar_perfis, name='listar_perfis'),
    path('perfis/<int:perfil_id>/', views_perfil.detalhar_perfil, name='detalhar_perfil'),
    path('perfis/<int:perfil_id>/usuarios/', views_perfil.listar_usuarios_perfil, name='listar_usuarios_perfil'),
    path('usuarios/<int:usuario_id>/atribuir-perfil/', views_perfil.atribuir_perfil, name='atribuir_perfil'),
    path('meu-perfil/permissoes/', views_perfil.meu_perfil_permissoes, name='meu_perfil_permissoes'),
    path('perfis/logs/', views_perfil.logs_alteracao_perfil, name='logs_alteracao_perfil'),
    path('ajax/verificar-permissao/', views_perfil.verificar_permissao_ajax, name='verificar_permissao_ajax'),
    
    # URLs para Sistema de Indicadores
    path('indicadores/', include('core.urls_indicadores')),
    
    # URLs para Repositório Digital
    path('repositorio/', include('core.urls_repositorio')),
    
    # URLs para Sistema de Suporte 24x7
    path('suporte/', include('core.urls_suporte')),
]