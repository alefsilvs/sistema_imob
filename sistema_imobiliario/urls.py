from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('security/', include('security.urls')),  # Sistema de segurança master
    path('', home, name='home'),
    path('dashboard/', include('core.urls')),
    path('suporte/', include(('core.urls_suporte', 'suporte'), namespace='suporte')),  # Sistema de suporte
    path('imoveis/', include('imoveis.urls')),
    path('contratos/', include('contratos.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('manutencao/', include('manutencao.urls')),
    path('documentos/', include('documentos.urls')),
    path('notificacoes/', include('notificacoes.urls')),  # ✅ Apenas uma linha
    path('indicadores/', include('core.urls_indicadores')),  # Sistema de indicadores
    path('pagamentos/', include('pagamentos.urls')),  # Sistema de pagamentos online
    path('assinaturas/', include('assinaturas.urls')),  # Sistema de controle de acesso
    path('saas/', include('saas.urls')),  # Sistema SaaS multi-tenant
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
