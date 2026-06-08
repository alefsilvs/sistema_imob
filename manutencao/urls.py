from django.urls import path
from . import views

app_name = 'manutencao'

urlpatterns = [
    # Ordens de Serviço
    path('ordens/', views.listar_ordens, name='listar_ordens'),
    path('ordens/cadastrar/', views.cadastrar_ordem, name='cadastrar_ordem'),
    path('ordens/<int:pk>/', views.detalhes_ordem, name='detalhes_ordem'),
    path('ordens/<int:pk>/editar/', views.editar_ordem, name='editar_ordem'),
    
    # Fornecedores
    path('fornecedores/', views.listar_fornecedores, name='listar_fornecedores'),
    path('fornecedores/cadastrar/', views.cadastrar_fornecedor, name='cadastrar_fornecedor'),
]