from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from saas.models import Tenant

class TrialMiddleware:
    """
    Middleware para verificar status do trial e restringir acesso quando expirado
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que não requerem verificação de trial
        self.exempt_urls = [
            '/saas/',
            '/admin/',
            '/accounts/login/',
            '/accounts/logout/',
            '/static/',
            '/media/',
            '/api/webhook/',
        ]
    
    def __call__(self, request):
        # Verificar se a URL está isenta
        if self._is_exempt_url(request.path):
            return self.get_response(request)
        
        # Verificar se o usuário está logado
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Verificar se é superusuário (admin)
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Obter tenant do usuário
        try:
            tenant = Tenant.objects.get(usuario_admin=request.user)
            request.tenant = tenant
        except Tenant.DoesNotExist:
            # Usuário sem tenant, permitir acesso
            return self.get_response(request)
        
        # Verificar status do trial
        if tenant.status == 'trial':
            if not tenant.is_trial_ativo:
                # Trial expirado
                return self._handle_expired_trial(request, tenant)
            elif tenant.dias_restantes_trial <= 3:
                # Trial próximo do vencimento - adicionar aviso
                if not request.session.get('trial_warning_shown'):
                    messages.warning(
                        request,
                        f'Seu período gratuito expira em {tenant.dias_restantes_trial} dias. '
                        f'Entre em contato com o administrador.'
                    )
                    request.session['trial_warning_shown'] = True
        
        # Verificar se a conta está suspensa
        elif tenant.status == 'suspenso':
            return self._handle_suspended_account(request, tenant)
        
        # Verificar se a conta está cancelada
        elif tenant.status == 'cancelado':
            return self._handle_cancelled_account(request, tenant)
        
        response = self.get_response(request)
        return response
    
    def _is_exempt_url(self, path):
        """Verificar se a URL está isenta da verificação de trial"""
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                return True
        return False
    
    def _handle_expired_trial(self, request, tenant):
        """Lidar com trial expirado"""
        # Para requisições AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'trial_expired',
                'message': 'Seu período gratuito expirou. Entre em contato com o administrador.',
                'redirect_url': reverse('login')
            }, status=403)
        
        # Para requisições normais, redirecionar para login
        messages.error(
            request,
            'Seu período gratuito expirou. Entre em contato com o administrador.'
        )
        return redirect('login')
    
    def _handle_suspended_account(self, request, tenant):
        """Lidar com conta suspensa"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'account_suspended',
                'message': 'Sua conta está suspensa. Entre em contato com o suporte.',
                'redirect_url': reverse('login')
            }, status=403)
        
        messages.error(
            request,
            'Sua conta está suspensa. Entre em contato com o suporte para reativar.'
        )
        return redirect('login')
    
    def _handle_cancelled_account(self, request, tenant):
        """Lidar com conta cancelada"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'account_cancelled',
                'message': 'Sua conta foi cancelada. Entre em contato com o administrador.',
                'redirect_url': reverse('login')
            }, status=403)
        
        messages.error(
            request,
            'Sua conta foi cancelada. Entre em contato com o administrador.'
        )
        return redirect('login')
