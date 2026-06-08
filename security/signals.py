from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import SecurityLog, LoginAttempt, BlockedIP, MasterUser
from .utils import get_client_ip, log_security_event, is_suspicious_activity, send_security_alert

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """
    Registra login bem-sucedido
    """
    ip_address = get_client_ip(request)
    
    # Registrar tentativa de login bem-sucedida
    LoginAttempt.objects.create(
        ip_address=ip_address,
        username=user.username,
        success=True,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Log de segurança
    log_security_event(
        request,
        'LOGIN_SUCCESS',
        f'Login bem-sucedido para usuário: {user.username}',
        severity='LOW'
    )
    
    # Verificar atividade suspeita
    is_suspicious, reason = is_suspicious_activity(request, user)
    if is_suspicious:
        log_security_event(
            request,
            'SUSPICIOUS_ACTIVITY',
            f'Atividade suspeita detectada: {reason}',
            severity='MEDIUM'
        )
    
    # Verificações especiais para usuário master
    if hasattr(user, 'master_profile'):
        master_user = user.master_profile
        
        # Verificar se é o primeiro login do dia
        today = timezone.now().date()
        last_login_today = SecurityLog.objects.filter(
            user=user,
            event_type='LOGIN_SUCCESS',
            timestamp__date=today
        ).exists()
        
        if not last_login_today:
            log_security_event(
                request,
                'MASTER_FIRST_LOGIN',
                f'Primeiro login do dia para usuário master',
                severity='MEDIUM'
            )
        
        # Atualizar último acesso
        master_user.last_login_ip = ip_address
        master_user.last_activity = timezone.now()
        master_user.save()

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Registra tentativa de login falhada
    """
    if request is None:
        return  # Não processar se request é None
        
    ip_address = get_client_ip(request)
    username = credentials.get('username', '')
    
    # Registrar tentativa de login falhada
    LoginAttempt.objects.create(
        ip_address=ip_address,
        username=username,
        success=False,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )
    
    # Log de segurança
    log_security_event(
        request,
        'LOGIN_FAILED',
        f'Tentativa de login falhada para usuário: {username}',
        severity='MEDIUM'
    )
    
    # Verificar se deve bloquear IP
    failed_attempts = LoginAttempt.get_failed_attempts(ip_address, minutes=60)
    
    if failed_attempts >= 5:
        # Bloquear IP por 1 hora
        blocked_ip, created = BlockedIP.objects.get_or_create(
            ip_address=ip_address,
            defaults={
                'reason': f'Muitas tentativas de login falhadas ({failed_attempts})',
                'blocked_until': timezone.now() + timedelta(hours=1)
            }
        )
        
        if created:
            log_security_event(
                request,
                'IP_AUTO_BLOCKED',
                f'IP bloqueado automaticamente por {failed_attempts} tentativas falhadas',
                severity='HIGH'
            )
    
    # Alerta especial para tentativas no usuário master
    try:
        master_user = User.objects.get(username=username, master_profile__isnull=False)
        log_security_event(
            request,
            'MASTER_LOGIN_ATTEMPT',
            f'Tentativa de login no usuário master de IP: {ip_address}',
            severity='CRITICAL'
        )
    except User.DoesNotExist:
        pass

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """
    Registra logout
    """
    if user:
        log_security_event(
            request,
            'LOGOUT',
            f'Logout do usuário: {user.username}',
            severity='LOW'
        )
        
        # Atualizar última atividade para usuário master
        if hasattr(user, 'master_profile'):
            master_user = user.master_profile
            master_user.last_activity = timezone.now()
            master_user.save()

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Registra criação e modificação de usuários
    """
    if created:
        # Novo usuário criado
        SecurityLog.objects.create(
            user=None,  # Sistema
            event_type='USER_CREATED',
            description=f'Novo usuário criado: {instance.username}',
            severity='MEDIUM',
            metadata={'new_user_id': instance.id}
        )
    else:
        # Usuário modificado
        SecurityLog.objects.create(
            user=None,  # Sistema
            event_type='USER_MODIFIED',
            description=f'Usuário modificado: {instance.username}',
            severity='LOW',
            metadata={'user_id': instance.id}
        )

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Registra exclusão de usuários
    """
    SecurityLog.objects.create(
        user=None,  # Sistema
        event_type='USER_DELETED',
        description=f'Usuário excluído: {instance.username}',
        severity='HIGH',
        metadata={'deleted_user_id': instance.id}
    )

@receiver(pre_save, sender=MasterUser)
def validate_master_user_changes(sender, instance, **kwargs):
    """
    Valida mudanças no usuário master
    """
    if instance.pk:  # Usuário existente sendo modificado
        try:
            old_instance = MasterUser.objects.get(pk=instance.pk)
            
            # Verificar mudanças críticas
            critical_changes = []
            
            if old_instance.hardware_fingerprint != instance.hardware_fingerprint:
                critical_changes.append('hardware_fingerprint')
            
            if old_instance.authorized_ips != instance.authorized_ips:
                critical_changes.append('authorized_ips')
            
            if old_instance.security_level != instance.security_level:
                critical_changes.append('security_level')
            
            if critical_changes:
                SecurityLog.objects.create(
                    user=instance.user,
                    event_type='MASTER_CONFIG_CHANGED',
                    description=f'Configurações críticas do master alteradas: {", ".join(critical_changes)}',
                    severity='CRITICAL',
                    metadata={'changed_fields': critical_changes}
                )
        
        except MasterUser.DoesNotExist:
            pass

@receiver(post_save, sender=MasterUser)
def log_master_user_changes(sender, instance, created, **kwargs):
    """
    Registra mudanças no usuário master
    """
    if created:
        SecurityLog.objects.create(
            user=instance.user,
            event_type='MASTER_USER_CREATED',
            description=f'Usuário master criado: {instance.user.username}',
            severity='CRITICAL',
            metadata={
                'security_level': instance.security_level,
                'two_factor_enabled': instance.two_factor_enabled
            }
        )
        
        # Enviar alerta
        send_security_alert(
            'MASTER_USER_CREATED',
            f'Novo usuário master criado: {instance.user.username}',
            'Sistema',
            instance.user
        )

@receiver(post_save, sender=SecurityLog)
def process_security_log(sender, instance, created, **kwargs):
    """
    Processa logs de segurança para detectar padrões
    """
    if created and instance.severity in ['HIGH', 'CRITICAL']:
        # Verificar se há muitos eventos de alta severidade recentemente
        recent_high_severity = SecurityLog.objects.filter(
            severity__in=['HIGH', 'CRITICAL'],
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        if recent_high_severity >= 5:
            SecurityLog.objects.create(
                user=None,
                event_type='SECURITY_PATTERN_DETECTED',
                description=f'Padrão de segurança detectado: {recent_high_severity} eventos de alta severidade em 15 minutos',
                severity='CRITICAL',
                metadata={'event_count': recent_high_severity}
            )

# Signal personalizado para limpeza automática
from django.core.management import call_command
from django.db.models.signals import post_migrate

@receiver(post_migrate)
def setup_periodic_tasks(sender, **kwargs):
    """
    Configura tarefas periódicas após migração
    """
    if sender.name == 'security':
        # Aqui você pode configurar tarefas periódicas usando Celery ou similar
        # Por enquanto, apenas registramos que o sistema foi inicializado
        SecurityLog.objects.create(
            user=None,
            event_type='SYSTEM_INITIALIZED',
            description='Sistema de segurança inicializado',
            severity='LOW'
        )