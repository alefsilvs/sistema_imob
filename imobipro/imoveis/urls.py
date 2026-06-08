from django.urls import path, re_path
from django.views.generic import RedirectView
from . import views

app_name = 'imoveis'

urlpatterns = [
    # Redirecionar URLs antigas de bancas para o dashboard
    re_path(r'^bancas/.*$', RedirectView.as_view(pattern_name='core:dashboard', permanent=False)),
    
    # URLs para Imóveis
    path('', views.listar_imoveis, name='listar'),
    path('cadastrar/', views.cadastrar_imovel, name='cadastrar'),
    path('detalhar/<int:pk>/', views.detalhes_imovel, name='detalhar'),
    path('detalhar/<int:pk>/', views.detalhes_imovel, name='detalhar_imovel'),
    path('<int:pk>/', views.detalhes_imovel, name='detalhes_imovel'),
    path('<int:pk>/editar/', views.editar_imovel, name='editar'),
    path('<int:pk>/excluir/', views.excluir_imovel, name='excluir'),
    path('<int:pk>/fotos/', views.gerenciar_fotos, name='gerenciar_fotos'),
]
