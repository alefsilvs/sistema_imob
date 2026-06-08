from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('security')

# Lista de emails dos administradores do sistema
ADMIN_EMAILS = [
    'alef63134@gmail.com',
    'yousefhilal@hotmail.com'
]

def is_system_admin(user):
    """
    Verifica se o usuário é um administrador do sistema.
    Administradores têm acesso gratuito a todos os planos.
    
    IMPORTANTE: Esta função deve ser usada com extremo cuidado.
    Logs de auditoria são gerados para todos os acessos de admin.
    
    Args:
        user: Instância do modelo User ou email string
    
    Returns:
        bool: True se for admin, False caso contrário
    """
    if isinstance(user, User):
        email = user.email
        user_id = user.id
        username = user.username
    elif isinstance(user, str):
        email = user
        user_id = 'N/A'
        username = 'N/A'
    else:
        return False
    
    is_admin = email.lower() in [admin_email.lower() for admin_email in ADMIN_EMAILS]
    
    # Log de auditoria para tentativas de verificação de admin
    if is_admin:
        logger.debug(
            f"ADMIN ACCESS GRANTED - User: {username} (ID: {user_id}) | Email: {email} | "
            f"Timestamp: {timezone.now()} | Function: is_system_admin"
        )
    
    return is_admin

def get_admin_tenant_for_user(user):
    """
    Retorna um tenant especial para administradores do sistema.
    Permite acesso completo sem restrições de plano.
    
    CRÍTICO: Esta função concede acesso ilimitado. Uso deve ser auditado.
    
    Args:
        user: Instância do modelo User
    
    Returns:
        dict: Configurações de tenant para admin ou None
    """
    if not is_system_admin(user):
        logger.info(
            f"ADMIN TENANT ACCESS DENIED - User: {user.username} (ID: {user.id}) | "
            f"Email: {user.email} | Timestamp: {timezone.now()}"
        )
        return None
    
    # Log crítico para acesso de tenant admin
    logger.critical(
        f"ADMIN TENANT ACCESS GRANTED - User: {user.username} (ID: {user.id}) | "
        f"Email: {user.email} | Timestamp: {timezone.now()} | "
        f"Function: get_admin_tenant_for_user | UNLIMITED ACCESS GRANTED"
    )
    
    # Configurações especiais para admins
    return {
        'is_admin': True,
        'unlimited_access': True,
        'max_usuarios': 999999,
        'max_imoveis': 999999,
        'max_contratos': 999999,
        'storage_gb': 999999,
        'api_calls_mes': 999999,
        'suporte_prioritario': True,
        'backup_automatico': True,
        'subdominio_personalizado': True
    }

def bypass_tenant_restrictions(user):
    """
    Verifica se o usuário deve ter as restrições de tenant ignoradas.
    
    CRÍTICO: Esta função permite bypass completo de segurança de tenant.
    Deve ser usada apenas em casos extremamente específicos.
    
    Args:
        user: Instância do modelo User
    
    Returns:
        bool: True se deve ignorar restrições, False caso contrário
    """
    is_bypass = is_system_admin(user)
    
    if is_bypass:
        logger.critical(
            f"TENANT RESTRICTIONS BYPASSED - User: {user.username} (ID: {user.id}) | "
            f"Email: {user.email} | Timestamp: {timezone.now()} | "
            f"Function: bypass_tenant_restrictions | SECURITY BYPASS ACTIVE"
        )
    
    return is_bypass
