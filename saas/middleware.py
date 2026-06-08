from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from .models import Tenant
from .admin_utils import is_system_admin, bypass_tenant_restrictions
import logging

logger = logging.getLogger(__name__)

def _enforce_tenant_billing_state(request, tenant, *, api=False):
    if getattr(request, 'is_system_admin', False):
        return None
    if hasattr(request, 'user') and getattr(request.user, 'is_superuser', False):
        return None

    now = timezone.now()
    if tenant.status == 'ativo' and tenant.data_expiracao and now > tenant.data_expiracao:
        try:
            Tenant.objects.filter(pk=tenant.pk, status='ativo').update(status='pendente_pagamento')
            tenant.status = 'pendente_pagamento'
        except Exception:
            pass

    if tenant.status == 'pendente_pagamento':
        if api:
            from django.http import JsonResponse
            return JsonResponse(
                {
                    'success': False,
                    'error': 'payment_required',
                    'message': 'Pagamento pendente. Renove para continuar usando o sistema.',
                    'redirect_url': reverse('saas:escolher_pagamento'),
                },
                status=402,
            )

        if not request.path.startswith('/saas/'):
            messages.warning(request, 'Seu pagamento está pendente. Renove para continuar usando o sistema.')
            return redirect('saas:escolher_pagamento')

    return None

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para identificar e configurar o tenant baseado no subdomínio
    """
    
    def process_request(self, request):
        # Verificar se o usuário é admin do sistema
        if hasattr(request, 'user') and request.user.is_authenticated and is_system_admin(request.user):
            # Admins do sistema têm acesso total, mas ainda precisam de tenant para funcionalidades específicas
            request.is_system_admin = True
            # Continuar processamento para configurar tenant se disponível na sessão
        
        # URLs que não precisam de tenant
        exempt_urls = [
            '/admin/',
            '/saas/',
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/accounts/password_reset/done/',
            '/accounts/password_reset/confirm/',
            '/accounts/password_reset/complete/',
            '/accounts/reset/',
            '/static/',
            '/media/',
        ]
        
        # Verificar se a URL está isenta
        for exempt_url in exempt_urls:
            if request.path.startswith(exempt_url):
                return None
        
        # Extrair subdomínio
        host = request.get_host().split(':')[0]  # Remove porta se houver
        subdomain_parts = host.split('.')
        
        # Se não há subdomínio (localhost ou IP), usar tenant da sessão
        if host.endswith('.up.railway.app') or host.endswith('.railway.app') or len(subdomain_parts) < 3 or subdomain_parts[0] in ['www', 'localhost', '127']:
            # Para desenvolvimento local, usar tenant_id da sessão se disponível
            tenant_id = request.session.get('tenant_id')
            
            # Verificar se usuário está autenticado (pode não estar disponível ainda)
            user_authenticated = hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated
            
            logger.debug(f"tenant_id da sessão: {tenant_id}, usuário autenticado: {user_authenticated}")

            if not tenant_id and user_authenticated:
                try:
                    tenant = (
                        Tenant.objects.select_related('plano')
                        .filter(
                            usuario_admin=request.user,
                            status__in=['ativo', 'trial', 'pendente_pagamento'],
                        )
                        .first()
                    )
                    if tenant:
                        request.session['tenant_id'] = tenant.id
                        tenant_id = tenant.id
                        logger.info(
                            f"Tenant ID {tenant.id} configurado automaticamente na sessão para usuário {request.user.username}"
                        )
                except Exception as e:
                    logger.error(f"Erro ao configurar tenant automaticamente para usuário {request.user.username}: {str(e)}")
            
            if tenant_id:
                try:
                    tenant = Tenant.objects.select_related('plano').get(
                        id=tenant_id,
                        status__in=['ativo', 'trial', 'pendente_pagamento']
                    )
                    
                    # Se o usuário está autenticado, verificar se é o admin do tenant
                    if user_authenticated:
                        # SEGURANÇA: Verificar se o usuário logado é o admin do tenant
                        # Admins do sistema ignoram esta restrição
                        if tenant.usuario_admin == request.user or getattr(request, 'is_system_admin', False) or request.user.is_superuser:
                            resp = _enforce_tenant_billing_state(request, tenant)
                            if resp is not None:
                                return resp

                            if tenant.status == 'trial' and not tenant.is_trial_ativo:
                                try:
                                    Tenant.objects.filter(pk=tenant.pk, status='trial').update(status='pendente_pagamento')
                                    tenant.status = 'pendente_pagamento'
                                except Exception:
                                    pass
                                if not request.path.startswith('/saas/'):
                                    messages.warning(request, 'Seu período de teste expirou. Renove para continuar usando o sistema.')
                                    return redirect('saas:escolher_pagamento')
                            
                            request.tenant = tenant
                            logger.info(f"Tenant da sessão: {tenant.nome_empresa} (ID: {tenant_id}) - Usuário: {request.user.username}")
                            logger.debug(f"request.tenant configurado: {tenant.nome_empresa}")
                        else:
                            # Usuário não é o admin deste tenant, limpar sessão
                            request.session.flush()  # Limpar toda a sessão por segurança
                            logger.warning(f"Tentativa de acesso não autorizado ao tenant {tenant_id} pelo usuário {request.user.username}")
                            if not request.path.startswith('/saas/'):
                                messages.error(request, 'Acesso não autorizado. Faça login novamente.')
                                return redirect('login')
                    else:
                        # Usuário não está autenticado, mas configurar tenant mesmo assim
                        # A verificação de autorização será feita nas views que exigem login
                        request.tenant = tenant
                        logger.debug(f"Tenant configurado para usuário não autenticado: {tenant.nome_empresa} (ID: {tenant_id})")
                        
                except Tenant.DoesNotExist:
                    # Tenant da sessão não existe mais, limpar sessão
                    request.session.flush()  # Limpar toda a sessão por segurança
                    if not request.path.startswith('/saas/'):
                        messages.error(request, 'Sessão expirada. Faça login novamente.')
                        return redirect('login')
            else:
                # Não há tenant_id na sessão
                logger.debug("Sem tenant_id na sessão")
                if user_authenticated and not request.path.startswith('/saas/'):
                    messages.error(request, 'Sua conta não possui uma empresa (tenant) vinculada. Crie sua empresa para continuar.')
                    return redirect('saas:registro')
            return None
        
        subdomain = subdomain_parts[0]
        
        try:
            # Buscar tenant pelo subdomínio
            tenant = Tenant.objects.select_related('plano').get(
                subdominio=subdomain,
                status__in=['ativo', 'trial', 'pendente_pagamento']
            )
            
            resp = _enforce_tenant_billing_state(request, tenant)
            if resp is not None:
                return resp
            
            # Verificar se o tenant está em trial e se expirou
            if tenant.status == 'trial' and not tenant.is_trial_ativo:
                try:
                    Tenant.objects.filter(pk=tenant.pk, status='trial').update(status='pendente_pagamento')
                    tenant.status = 'pendente_pagamento'
                except Exception:
                    pass
                messages.warning(request, 'Seu período de teste expirou. Renove para continuar usando o sistema.')
                return redirect('saas:escolher_pagamento')
            
            # Configurar tenant no request
            request.tenant = tenant
            
            # Log de acesso
            logger.info(f"Acesso ao tenant {tenant.nome_empresa} ({subdomain})")
            
        except Tenant.DoesNotExist:
            # Tenant não encontrado
            logger.warning(f"Tentativa de acesso a subdomínio inexistente: {subdomain}")
            
            if request.path.startswith('/saas/'):
                return None
            
            messages.error(request, 
                'Subdomínio não encontrado ou inativo. Verifique o endereço ou entre em contato conosco.')
            return redirect('login')
        
        except Exception as e:
            # Erro inesperado
            logger.error(f"Erro no TenantMiddleware: {str(e)}")
            
            if request.path.startswith('/saas/'):
                return None
                
            messages.error(request, 
                'Erro temporário. Tente novamente em alguns instantes.')
            return redirect('login')
        
        return None


class TenantDatabaseMiddleware(MiddlewareMixin):
    """
    Middleware para configurar o schema/database do tenant
    """
    
    def process_request(self, request):
        # Definir tenant_id como None por padrão para evitar vazamento
        request.tenant_id = None
        
        # Só processar se há um tenant configurado
        if not hasattr(request, 'tenant'):
            return None
        
        tenant = request.tenant
        
        # Configurar schema do banco (para PostgreSQL com schemas)
        # Ou configurar database específico (para múltiplos databases)
        
        # Exemplo para PostgreSQL com schemas:
        # from django.db import connection
        # with connection.cursor() as cursor:
        #     cursor.execute(f"SET search_path TO {tenant.schema_name}, public")
        
        # Exemplo para múltiplos databases:
        # request.database_alias = f"tenant_{tenant.id}"
        
        # Usar um campo tenant_id para filtrar dados
        request.tenant_id = tenant.id
        
        return None


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    Middleware para segurança adicional do tenant
    """
    
    def process_request(self, request):
        if not hasattr(request, 'tenant'):
            return None
        
        tenant = request.tenant
        
        # Verificar limites de uso
        if hasattr(tenant, 'configuracao'):
            config = tenant.configuracao
            
            # Verificar limite de usuários
            if config.limite_usuarios > 0:
                usuarios_ativos = tenant.usuarios.filter(is_active=True).count()
                if usuarios_ativos >= config.limite_usuarios:
                    request.limite_usuarios_atingido = True
            
            # Verificar limite de imóveis
            if config.limite_imoveis > 0:
                # Assumindo que existe um modelo Imovel com tenant_id
                # imoveis_count = Imovel.objects.filter(tenant_id=tenant.id).count()
                # if imoveis_count >= config.limite_imoveis:
                #     request.limite_imoveis_atingido = True
                pass
        
        # Registrar uso
        try:
            from .models import RegistroUso
            from datetime import date
            registro, created = RegistroUso.objects.get_or_create(
                tenant=tenant,
                data=date.today(),
                defaults={
                    'usuarios_ativos': 1,
                    'imoveis_cadastrados': 0,
                    'contratos_ativos': 0,
                    'api_calls': 1,
                    'storage_usado_mb': 0
                }
            )
            if not created:
                registro.api_calls += 1
                registro.save()
        except Exception as e:
            logger.error(f"Erro ao registrar uso: {str(e)}")
        
        return None
    
    def get_client_ip(self, request):
        """Obter IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar contexto do tenant aos templates
    """
    
    def process_template_response(self, request, response):
        if hasattr(request, 'tenant') and hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            
            tenant = request.tenant
            
            # Adicionar dados do tenant ao contexto
            response.context_data.update({
                'tenant': tenant,
                'tenant_config': getattr(tenant, 'configuracao', None),
                'tenant_colors': {
                    'primary': getattr(tenant.configuracao, 'cor_primaria', '#007bff') if hasattr(tenant, 'configuracao') else '#007bff',
                    'secondary': getattr(tenant.configuracao, 'cor_secundaria', '#6c757d') if hasattr(tenant, 'configuracao') else '#6c757d',
                },
                'tenant_limits': {
                    'usuarios_atingido': getattr(request, 'limite_usuarios_atingido', False),
                    'imoveis_atingido': getattr(request, 'limite_imoveis_atingido', False),
                }
            })
        
        return response


class APITenantMiddleware(MiddlewareMixin):
    """
    Middleware específico para APIs, identifica tenant via header ou token
    """
    
    def process_request(self, request):
        # Só processar para URLs de API
        if not request.path.startswith('/api/'):
            return None
        
        # Tentar identificar tenant via header
        tenant_header = request.META.get('HTTP_X_TENANT_ID')
        if tenant_header:
            try:
                tenant = Tenant.objects.get(
                    id=tenant_header,
                    status__in=['ativo', 'trial']
                )
                resp = _enforce_tenant_billing_state(request, tenant, api=True)
                if resp is not None:
                    return resp
                request.tenant = tenant
                request.tenant_id = tenant.id
                return None
            except Tenant.DoesNotExist:
                pass
        
        # Tentar identificar via subdomínio (mesmo que web)
        host = request.get_host().split(':')[0]
        subdomain_parts = host.split('.')
        
        if len(subdomain_parts) >= 3 and subdomain_parts[0] not in ['www', 'localhost', '127']:
            subdomain = subdomain_parts[0]
            try:
                tenant = Tenant.objects.get(
                    subdominio=subdomain,
                    status__in=['ativo', 'trial']
                )
                resp = _enforce_tenant_billing_state(request, tenant, api=True)
                if resp is not None:
                    return resp
                request.tenant = tenant
                request.tenant_id = tenant.id
                return None
            except Tenant.DoesNotExist:
                pass
        
        # Se chegou até aqui, não foi possível identificar o tenant
        from django.http import JsonResponse
        return JsonResponse({
            'error': 'Tenant não identificado',
            'message': 'Forneça o X-Tenant-ID no header ou use subdomínio válido'
        }, status=400)

class EmailVerificationMiddleware(MiddlewareMixin):
    """
    Middleware para verificar se o usuário tem email verificado
    antes de acessar áreas protegidas do sistema
    """
    
    # URLs que requerem email verificado
    PROTECTED_URLS = [
        '/dashboard/',
        '/imoveis/',
        '/clientes/',
        '/contratos/',
        '/financeiro/',
        '/relatorios/',
        '/configuracoes/',
    ]
    
    # URLs que não requerem verificação (permitidas)
    EXEMPT_URLS = [
        '/admin/',
        '/saas/planos/',
        '/saas/registro/',
        '/saas/email-enviado/',
        '/saas/verificar-email/',
        '/saas/reenviar-email/',
        '/saas/pagamento/',
        '/saas/escolher-pagamento/',
        '/saas/processar-pagamento/',
        '/saas/processar-pagamento-final/',
        '/saas/webhook/',
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/password/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Pular verificação para URLs isentas
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return None
        
        # Verificar se o request tem o atributo user (middleware de auth executado)
        if not hasattr(request, 'user'):
            return None
            
        # Pular verificação se usuário não estiver logado
        if not request.user.is_authenticated:
            return None
        
        # Pular verificação para superusuários
        if request.user.is_superuser:
            return None
        
        # Verificar se a URL atual requer email verificado
        requires_verification = any(
            request.path.startswith(url) for url in self.PROTECTED_URLS
        )
        
        if not requires_verification:
            return None
        
        try:
            from .models import VerificacaoEmail
            from django.http import JsonResponse
            
            # Verificar se o usuário tem verificação de email
            verificacao = VerificacaoEmail.objects.get(usuario=request.user)
            
            if not verificacao.email_verificado:
                # Verificar se é uma requisição AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'email_not_verified',
                        'message': 'Você precisa verificar seu email antes de acessar esta área. Verifique sua caixa de entrada e clique no link de verificação.',
                        'redirect_url': reverse('saas:email_enviado')
                    }, status=403)
                
                messages.warning(
                    request,
                    'Você precisa verificar seu email antes de acessar esta área. '
                    'Verifique sua caixa de entrada e clique no link de verificação.'
                )
                return redirect('saas:email_enviado')
                
        except VerificacaoEmail.DoesNotExist:
            from .models import VerificacaoEmail
            from django.http import JsonResponse
            
            # Se não existe registro de verificação, criar um e enviar email
            verificacao = VerificacaoEmail.objects.create(
                usuario=request.user,
                email_verificado=False
            )
            
            # Tentar enviar email de verificação
            verificacao.enviar_email_verificacao(request)
            
            # Verificar se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'email_not_verified',
                    'message': f'Enviamos um email de verificação para {request.user.email}. Verifique sua caixa de entrada e clique no link para ativar sua conta.',
                    'redirect_url': reverse('saas:email_enviado')
                }, status=403)
            
            messages.warning(
                request,
                f'Enviamos um email de verificação para {request.user.email}. '
                f'Verifique sua caixa de entrada e clique no link para ativar sua conta.'
            )
            return redirect('saas:email_enviado')
        
        return None
