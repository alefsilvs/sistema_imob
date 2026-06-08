from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('security')

class PaymentRateLimitMiddleware:
    """
    Middleware para controlar rate limiting em tentativas de pagamento.
    Previne ataques de força bruta e tentativas maliciosas de pagamento.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configurações de rate limiting
        self.max_attempts = getattr(settings, 'PAYMENT_MAX_ATTEMPTS', 5)
        self.window_minutes = getattr(settings, 'PAYMENT_WINDOW_MINUTES', 15)
        self.block_duration = getattr(settings, 'PAYMENT_BLOCK_DURATION', 60)  # minutos
    
    def __call__(self, request):
        # URLs de pagamento que devem ser protegidas
        payment_urls = [
            '/saas/pagamento/',
            '/saas/webhook/',
            '/saas/confirmar-pagamento/',
            '/api/pagamento/',
        ]
        
        # Verifica se é uma requisição de pagamento
        is_payment_request = any(request.path.startswith(url) for url in payment_urls)
        
        if is_payment_request and request.method == 'POST':
            if not self._check_rate_limit(request):
                logger.warning(
                    f"PAYMENT RATE LIMIT EXCEEDED - IP: {self._get_client_ip(request)} | "
                    f"User: {getattr(request.user, 'username', 'Anonymous')} | "
                    f"Path: {request.path} | Timestamp: {timezone.now()}"
                )
                return JsonResponse({
                    'error': 'Muitas tentativas de pagamento. Tente novamente em alguns minutos.',
                    'retry_after': self.block_duration * 60
                }, status=429)
        
        response = self.get_response(request)
        return response
    
    def _get_client_ip(self, request):
        """Obtém o IP real do cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _check_rate_limit(self, request):
        """Verifica se o rate limit foi excedido."""
        ip = self._get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        
        # Chaves de cache para IP e usuário
        ip_key = f"payment_attempts_ip_{ip}"
        user_key = f"payment_attempts_user_{user_id}"
        block_key = f"payment_blocked_{ip}_{user_id}"
        
        # Verifica se está bloqueado
        if cache.get(block_key):
            return False
        
        # Conta tentativas por IP
        ip_attempts = cache.get(ip_key, 0)
        user_attempts = cache.get(user_key, 0)
        
        # Se excedeu o limite, bloqueia
        if ip_attempts >= self.max_attempts or user_attempts >= self.max_attempts:
            cache.set(block_key, True, self.block_duration * 60)
            return False
        
        # Incrementa contadores
        cache.set(ip_key, ip_attempts + 1, self.window_minutes * 60)
        if request.user.is_authenticated:
            cache.set(user_key, user_attempts + 1, self.window_minutes * 60)
        
        return True

class PaymentSecurityValidator:
    """
    Classe para validações adicionais de segurança em pagamentos.
    """
    
    @staticmethod
    def validate_payment_request(request, amount, plan_id):
        """Valida uma requisição de pagamento."""
        errors = []
        
        # Validação de valor mínimo
        if amount <= 0:
            errors.append("Valor de pagamento inválido")
        
        # Validação de valor máximo (previne tentativas de overflow)
        if amount > 10000:  # R$ 10.000 como limite máximo
            errors.append("Valor de pagamento excede o limite máximo")
            logger.warning(
                f"SUSPICIOUS PAYMENT AMOUNT - User: {request.user.username} | "
                f"Amount: {amount} | Plan: {plan_id} | IP: {PaymentRateLimitMiddleware()._get_client_ip(request)}"
            )
        
        # Validação de plano existente
        from .models import PlanoComercial
        try:
            plano = PlanoComercial.objects.get(id=plan_id, ativo=True)
            # Verifica se o valor corresponde ao plano
            if abs(float(amount) - float(plano.preco)) > 0.01:  # Tolerância de 1 centavo
                errors.append("Valor não corresponde ao plano selecionado")
                logger.warning(
                    f"PAYMENT AMOUNT MISMATCH - User: {request.user.username} | "
                    f"Expected: {plano.preco} | Received: {amount} | Plan: {plan_id}"
                )
        except PlanoComercial.DoesNotExist:
            errors.append("Plano selecionado não existe ou está inativo")
        
        return errors
    
    @staticmethod
    def log_payment_attempt(request, success, amount, plan_id, error_msg=None):
        """Registra tentativa de pagamento para auditoria."""
        status = "SUCCESS" if success else "FAILED"
        
        log_msg = (
            f"PAYMENT ATTEMPT {status} - User: {request.user.username} (ID: {request.user.id}) | "
            f"Amount: {amount} | Plan: {plan_id} | IP: {PaymentRateLimitMiddleware()._get_client_ip(request)} | "
            f"Timestamp: {timezone.now()}"
        )
        
        if error_msg:
            log_msg += f" | Error: {error_msg}"
        
        if success:
            logger.info(log_msg)
        else:
            logger.warning(log_msg)