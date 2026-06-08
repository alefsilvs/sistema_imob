from django.urls import path
from . import views
from .logout_views import custom_logout

app_name = 'security'

urlpatterns = [
    # Logout customizado
    path('logout/', custom_logout, name='custom_logout'),
    # Dashboard principal
    path('', views.security_dashboard, name='dashboard'),
    
    # Autenticação master
    path('master-login/', views.master_login, name='master_login'),
    
    # Logs de segurança
    path('logs/', views.security_logs, name='logs'),
    
    # Gerenciamento de IPs bloqueados
    path('blocked-ips/', views.blocked_ips_view, name='blocked_ips'),
    
    # Configuração de 2FA
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    
    # Configurações do sistema
    path('settings/', views.system_settings, name='system_settings'),
    
    # Relatórios de segurança
    path('reports/', views.security_reports, name='reports'),
    
    # API endpoints
    path('api/status/', views.api_security_status, name='api_status'),
    path('api/alerts/', views.api_security_alerts, name='api_alerts'),
]