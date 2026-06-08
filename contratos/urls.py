from django.urls import path
from . import views

app_name = 'contratos'

urlpatterns = [
    path('', views.listar_contratos, name='listar'),
    path('cadastrar/', views.cadastrar_contrato, name='cadastrar'),
    path('<int:pk>/', views.detalhes_contrato, name='detalhes_contrato'),
    path('<int:pk>/editar/', views.editar_contrato, name='editar'),
    path('<int:pk>/excluir/', views.excluir_contrato, name='excluir'),
    
    # Reajustes
    path('reajustes/', views.listar_reajustes, name='listar_reajustes'),
    path('<int:contrato_pk>/reajustes/cadastrar/', views.cadastrar_reajuste, name='cadastrar_reajuste'),
]