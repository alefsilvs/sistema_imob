import time
import hashlib
import json
import os
import uuid
import re
from datetime import datetime, timedelta
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.utils import timezone
from django.db.utils import OperationalError, ProgrammingError
from .models import SecurityLog, LoginAttempt, BlockedIP, MasterUser
from .utils import get_client_ip, log_security_event, get_hardware_fingerprint
import logging

logger = logging.getLogger('security')

class ApiJsonExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        path = getattr(request, 'path', '') or ''
        if not path.startswith('/notificacoes/whatsapp/api/'):
            return None
        err_id = uuid.uuid4().hex[:12]
        payload = {'success': False, 'error': 'Erro interno (server).', 'error_id': err_id}
        try:
            if getattr(request, 'user', None) and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
                payload['debug'] = f"{exception.__class__.__name__}: {str(exception)}"
        except Exception:
            pass
        logger.exception('API 500 [%s] %s', err_id, path)
        resp = JsonResponse(payload, status=500)
        resp['X-WA-API'] = '1'
        resp['X-WA-ERR-ID'] = err_id
        return resp

    def process_response(self, request, response):
        path = getattr(request, 'path', '') or ''
        if not path.startswith('/notificacoes/whatsapp/api/'):
            return response
        try:
            response['X-WA-API'] = '1'
        except Exception:
            pass
        try:
            if getattr(response, 'status_code', 200) >= 500 and not str(getattr(response, 'get', lambda *_: '')('Content-Type', '')).lower().startswith('application/json'):
                original_ct = ''
                try:
                    original_ct = response.get('Content-Type', '') or ''
                except Exception:
                    original_ct = ''
                err_id = uuid.uuid4().hex[:12]
                payload = {'success': False, 'error': 'Erro interno (server).', 'error_id': err_id}
                try:
                    logger.error('API 500 response [%s] %s %s (orig_ct=%s)', err_id, getattr(request, 'method', ''), path, original_ct)
                except Exception:
                    pass
                resp = JsonResponse(payload, status=getattr(response, 'status_code', 500))
                resp['X-WA-API'] = '1'
                resp['X-WA-ERR-ID'] = err_id
                if original_ct:
                    resp['X-WA-API-ORIG-CT'] = original_ct[:120]
                return resp
        except Exception:
            pass
        return response

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware principal de segurança
    """
    
    def process_request(self, request):
        path = getattr(request, 'path', '') or ''
        if path.startswith(('/accounts/', '/admin/')):
            return None
        if path.startswith('/notificacoes/whatsapp/'):
            return None

        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar se o IP está bloqueado
        if self.is_ip_blocked(ip_address):
            logger.warning(f"Blocked IP attempted access: {ip_address}")
            log_security_event(
                request,
                'IP_BLOCKED',
                f'Tentativa de acesso de IP bloqueado: {ip_address}',
                severity='HIGH'
            )
            return self._render_blocked_response(request)
        
        # Detectar ataques comuns
        if self._detect_attack_patterns(request):
            logger.critical(f"Attack pattern detected from IP: {ip_address}")
            log_security_event(
                request,
                'ATTACK_DETECTED',
                f'Padrão de ataque detectado: {request.path}',
                severity='CRITICAL'
            )
            return self._render_attack_response(request)
        
        # Rate limiting avançado
        if self.is_rate_limited(request, ip_address):
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            log_security_event(
                request,
                'RATE_LIMIT_EXCEEDED',
                f'Rate limit excedido para IP: {ip_address}',
                severity='MEDIUM'
            )
            return self._render_rate_limit_response(request)
        
        # Validar sessão de usuário master
        if hasattr(request, 'user') and request.user.is_authenticated and hasattr(request.user, 'masteruser'):
            if not self._validate_master_session(request):
                logout(request)
                logger.warning(f"Invalid master session terminated for IP: {ip_address}")
                return redirect('security:master_login')
        
        return None
    
    def process_response(self, request, response):
        # Adicionar headers de segurança
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response
    
    def is_ip_blocked(self, ip_address):
        """
        Verifica se o IP está bloqueado
        """
        try:
            blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
            return blocked_ip.is_blocked()
        except BlockedIP.DoesNotExist:
            return False
        except (ProgrammingError, OperationalError) as e:
            logger.error(f"Error checking blocked IP: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking blocked IP: {e}")
            return False
    
    def is_rate_limited(self, request, ip_address):
        """
        Implementa rate limiting avançado baseado em IP e endpoint
        """
        try:
            # Configurações de rate limiting por tipo de endpoint
            limits = {
                'default': {'requests': 100, 'window': 300},  # 100 req/5min
                'login': {'requests': 50, 'window': 300},     # 50 req/5min (aumentado para desenvolvimento)
                'admin': {'requests': 50, 'window': 300},     # 50 req/5min
                'api': {'requests': 200, 'window': 300},      # 200 req/5min
            }
            
            # Determinar tipo de endpoint
            path = request.path.lower()
            if 'login' in path:
                limit_type = 'login'
            elif 'admin' in path or 'security' in path:
                limit_type = 'admin'
            elif 'api' in path:
                limit_type = 'api'
            else:
                limit_type = 'default'
            
            limit_config = limits[limit_type]
            cache_key = f"rate_limit:{limit_type}:{ip_address}"
            
            # Verificar cache
            current_requests = cache.get(cache_key, [])
            now = time.time()
            
            # Remover requisições antigas
            current_requests = [
                req_time for req_time in current_requests 
                if now - req_time < limit_config['window']
            ]
            
            # Verificar se excedeu o limite
            if len(current_requests) >= limit_config['requests']:
                return True
            
            # Adicionar requisição atual
            current_requests.append(now)
            cache.set(cache_key, current_requests, limit_config['window'])
            
            return False
        
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            return False
    
    def _detect_attack_patterns(self, request):
        """
        Detecta padrões de ataque comuns.
        """
        try:
            url = request.get_full_path().lower()
            if any(x in url for x in ('../', '..\\', 'javascript:', 'vbscript:', '/etc/', 'boot.ini', 'win.ini')):
                return True

            tokens = set(re.split(r'[^a-z0-9]+', url))
            tokens.discard('')
            suspicious_tokens = {
                'script', 'alert', 'onload', 'onerror', 'onclick',
                'union', 'select', 'insert', 'delete', 'drop',
                'exec', 'eval', 'system', 'cmd', 'shell', 'passwd',
            }
            if tokens.intersection(suspicious_tokens):
                return True
            
            # Verificar headers suspeitos
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            suspicious_agents = [
                'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
                'burp', 'w3af', 'acunetix', 'nessus'
            ]
            
            for agent in suspicious_agents:
                if agent in user_agent:
                    return True
            
            # Verificar tamanho excessivo de parâmetros
            if len(request.GET.urlencode()) > 2048:
                return True
            
            if request.method == 'POST' and len(str(request.POST)) > 10240:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in attack detection: {e}")
            return False
    
    def _validate_master_session(self, request):
        """
        Valida a sessão do usuário master.
        """
        try:
            master_user = request.user.masteruser
            client_ip = get_client_ip(request)
            
            # Verificar IP autorizado
            if master_user.authorized_ips:
                authorized_ips = [ip.strip() for ip in master_user.authorized_ips.split(',')]
                if client_ip not in authorized_ips:
                    log_security_event(
                        request, 'UNAUTHORIZED_IP',
                        f"Master user accessed from unauthorized IP: {client_ip}",
                        severity='CRITICAL'
                    )
                    return False
            
            # Verificar hardware fingerprint
            current_fingerprint = get_hardware_fingerprint(request)
            if (master_user.hardware_fingerprint and 
                master_user.hardware_fingerprint != current_fingerprint):
                log_security_event(
                    request, 'HARDWARE_MISMATCH',
                    f"Hardware fingerprint mismatch for master user",
                    severity='CRITICAL'
                )
                return False
            
            # Verificar timeout de sessão
            session_timeout = getattr(settings, 'MASTER_SESSION_TIMEOUT', 3600)  # 1 hora
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                if (timezone.now() - last_activity_time).seconds > session_timeout:
                    log_security_event(
                        request, 'SESSION_TIMEOUT',
                        f"Master session timeout",
                        severity='MEDIUM'
                    )
                    return False
            
            # Atualizar última atividade
            request.session['last_activity'] = timezone.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating master session: {e}")
            return False
    
    def _render_blocked_response(self, request):
        """
        Renderiza resposta para IP bloqueado.
        """
        if request.headers.get('Accept', '').startswith('application/json'):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Your IP address has been blocked due to suspicious activity.'
            }, status=403)
        
        return HttpResponseForbidden("Acesso negado. IP bloqueado por atividade suspeita.")
    
    def _render_rate_limit_response(self, request):
        """
        Renderiza resposta para rate limit excedido.
        """
        if request.headers.get('Accept', '').startswith('application/json'):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        return JsonResponse({'error': 'Muitas requisições. Tente novamente em alguns minutos.'}, status=429)
    
    def _render_attack_response(self, request):
        """
        Renderiza resposta para ataque detectado.
        """
        # Bloquear IP temporariamente
        client_ip = get_client_ip(request)
        BlockedIP.objects.get_or_create(
            ip_address=client_ip,
            defaults={
                'reason': 'Attack pattern detected',
                'blocked_until': timezone.now() + timedelta(hours=24),
                'permanent': False,
            }
        )
        
        if request.headers.get('Accept', '').startswith('application/json'):
            return JsonResponse({
                'error': 'Security violation',
                'message': 'Suspicious activity detected. Access denied.'
            }, status=403)
        
        return HttpResponseForbidden("Atividade suspeita detectada. Acesso negado.")

class MasterUserMiddleware(MiddlewareMixin):
    """
    Middleware específico para validação do usuário master
    """
    
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'master_profile'):
            ip_address = get_client_ip(request)
            master_user = request.user.master_profile
            
            # Verificar se o IP está autorizado
            if not master_user.is_ip_authorized(ip_address):
                log_security_event(
                    request,
                    'UNAUTHORIZED_ACCESS',
                    f'Usuário master tentou acessar de IP não autorizado: {ip_address}',
                    severity='CRITICAL'
                )
                logout(request)
                return redirect('admin:login')
            
            hardware_check_env = os.getenv('MASTER_HARDWARE_CHECK')
            enforce_hardware_check = None
            if hardware_check_env is not None:
                enforce_hardware_check = hardware_check_env.strip().lower() in ('1', 'true', 'yes', 'on')
            else:
                enforce_hardware_check = not any(
                    os.getenv(k)
                    for k in ('RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT')
                )

            if enforce_hardware_check:
                current_fingerprint = master_user.generate_hardware_fingerprint()
                if current_fingerprint != master_user.hardware_fingerprint:
                    log_security_event(
                        request,
                        'HARDWARE_MISMATCH',
                        f'Hardware fingerprint não confere para usuário master',
                        severity='CRITICAL'
                    )
                    logout(request)
                    return redirect('admin:login')
        
        return None

class LoginSecurityMiddleware(MiddlewareMixin):
    """
    Middleware para segurança de login
    """
    
    def process_request(self, request):
        if request.path == '/admin/login/' and request.method == 'POST':
            ip_address = get_client_ip(request)
            
            # Verificar tentativas falhadas recentes
            failed_attempts = LoginAttempt.get_failed_attempts(ip_address)
            
            if failed_attempts >= 5:
                # Bloquear IP temporariamente
                BlockedIP.objects.get_or_create(
                    ip_address=ip_address,
                    defaults={
                        'reason': 'Muitas tentativas de login falhadas',
                        'blocked_until': timezone.now() + timedelta(hours=1)
                    }
                )
                
                log_security_event(
                    request,
                    'IP_BLOCKED',
                    f'IP bloqueado por tentativas excessivas de login: {ip_address}',
                    severity='HIGH'
                )
                
                return HttpResponseForbidden("IP bloqueado por tentativas excessivas de login.")
        
        return None

class CSRFSecurityMiddleware(MiddlewareMixin):
    """
    Middleware adicional de proteção CSRF
    """
    
    def process_request(self, request):
        # Verificar se a requisição tem um referer válido para operações sensíveis
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            referer = request.META.get('HTTP_REFERER')
            host = request.get_host()
            
            if referer and not referer.startswith(f'http://{host}') and not referer.startswith(f'https://{host}'):
                log_security_event(
                    request,
                    'SECURITY_BREACH',
                    f'Possível ataque CSRF detectado. Referer: {referer}',
                    severity='HIGH'
                )
        
        return None

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoria de ações administrativas
    """
    
    def process_request(self, request):
        # Armazenar informações da requisição para auditoria
        request._audit_start_time = time.time()
        request._audit_ip = get_client_ip(request)
        
        return None
    
    def process_response(self, request, response):
        # Log de ações administrativas
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path.startswith('/admin/') and 
            request.method in ['POST', 'PUT', 'DELETE', 'PATCH']):
            
            duration = time.time() - getattr(request, '_audit_start_time', 0)
            
            log_security_event(
                request,
                'ADMIN_ACTION',
                f'Ação administrativa: {request.method} {request.path}',
                metadata={
                    'duration': duration,
                    'status_code': response.status_code,
                    'content_length': len(response.content) if hasattr(response, 'content') else 0
                }
            )
        
        return response
