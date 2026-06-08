import hashlib
import platform
import psutil
import socket
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import SecurityLog


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email") or kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None

        UserModel = get_user_model()
        normalized_username = str(username).strip()

        lookups = []
        if "@" in normalized_username:
            lookups.append({"email__iexact": normalized_username})
            lookups.append({f"{UserModel.USERNAME_FIELD}__iexact": normalized_username})
        else:
            lookups.append({f"{UserModel.USERNAME_FIELD}__iexact": normalized_username})
            lookups.append({"email__iexact": normalized_username})

        user = None
        for lookup in lookups:
            try:
                user = UserModel._default_manager.get(**lookup)
                break
            except UserModel.DoesNotExist:
                continue
            except UserModel.MultipleObjectsReturned:
                return None

        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

def get_client_ip(request):
    """
    Obtém o IP real do cliente, considerando proxies
    """
    if request is None:
        return '127.0.0.1'  # IP padrão quando request é None
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'

def get_user_agent(request):
    """
    Obtém o user agent do cliente
    """
    return request.META.get('HTTP_USER_AGENT', '')

def generate_hardware_fingerprint():
    """
    Gera uma impressão digital única do hardware
    """
    try:
        # Informações do sistema
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine(),
            'node': platform.node(),
            'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                   for elements in range(0,2*6,2)][::-1]),
        }
        
        # Informações de hardware (se disponível)
        try:
            system_info['cpu_count'] = psutil.cpu_count()
            system_info['memory_total'] = psutil.virtual_memory().total
            system_info['disk_total'] = psutil.disk_usage('/').total if platform.system() != 'Windows' else psutil.disk_usage('C:').total
        except:
            pass
        
        # Criar hash da impressão digital
        fingerprint_string = '|'.join([f"{k}:{v}" for k, v in sorted(system_info.items())])
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
    except Exception:
        # Fallback para um identificador básico
        fallback = f"{platform.platform()}|{uuid.getnode()}"
        return hashlib.sha256(fallback.encode()).hexdigest()[:32]

def get_hardware_fingerprint(request):
    """
    Obtém impressão digital do hardware baseada no request e sistema
    """
    try:
        # Informações do cliente
        client_info = {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
        }
        
        # Informações do servidor (como proxy para hardware)
        server_fingerprint = generate_hardware_fingerprint()
        
        # Combinar informações
        combined = f"{server_fingerprint}|{client_info['user_agent']}|{client_info['accept_language']}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    except Exception:
        # Fallback simples
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        return hashlib.sha256(user_agent.encode()).hexdigest()[:32]

def log_security_event(request, event_type, description, severity='LOW', metadata=None):
    """
    Registra um evento de segurança
    """
    try:
        user = request.user if request.user.is_authenticated else None
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        SecurityLog.objects.create(
            user=user,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            metadata=metadata or {}
        )
        
        # Enviar alerta por email para eventos críticos
        if severity in ['HIGH', 'CRITICAL']:
            send_security_alert(event_type, description, ip_address, user)
    
    except Exception as e:
        # Log de fallback em caso de erro
        print(f"Erro ao registrar evento de segurança: {e}")

def send_security_alert(event_type, description, ip_address, user=None):
    """
    Envia alerta de segurança por email
    """
    try:
        subject = f"[ALERTA DE SEGURANÇA] {event_type}"
        message = f"""
        ALERTA DE SEGURANÇA DETECTADO
        
        Tipo: {event_type}
        Descrição: {description}
        IP: {ip_address}
        Usuário: {user.username if user else 'Anônimo'}
        Data/Hora: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
        
        Este é um alerta automático do sistema de segurança.
        """
        
        # Enviar para administradores
        admin_emails = [user.email for user in User.objects.filter(is_superuser=True, email__isnull=False)]
        
        if admin_emails and hasattr(settings, 'EMAIL_HOST'):
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            )
    
    except Exception as e:
        print(f"Erro ao enviar alerta de segurança: {e}")

def check_password_strength(password):
    """
    Verifica a força de uma senha
    """
    score = 0
    feedback = []
    
    # Comprimento
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append("Senha deve ter pelo menos 8 caracteres")
    
    # Caracteres maiúsculos
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Inclua pelo menos uma letra maiúscula")
    
    # Caracteres minúsculos
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Inclua pelo menos uma letra minúscula")
    
    # Números
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Inclua pelo menos um número")
    
    # Caracteres especiais
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        feedback.append("Inclua pelo menos um caractere especial")
    
    # Sequências comuns
    common_sequences = ['123', 'abc', 'qwe', 'asd', 'zxc']
    if any(seq in password.lower() for seq in common_sequences):
        score -= 1
        feedback.append("Evite sequências comuns")
    
    # Palavras comuns
    common_words = ['password', 'senha', 'admin', 'user', 'login']
    if any(word in password.lower() for word in common_words):
        score -= 1
        feedback.append("Evite palavras comuns")
    
    # Classificação
    if score >= 5:
        strength = 'FORTE'
    elif score >= 3:
        strength = 'MÉDIA'
    else:
        strength = 'FRACA'
    
    return {
        'score': max(0, score),
        'strength': strength,
        'feedback': feedback
    }

def generate_secure_token(length=32):
    """
    Gera um token seguro
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_backup_codes(count=10):
    """
    Gera códigos de backup para 2FA
    """
    import secrets
    import string
    
    codes = []
    for _ in range(count):
        # Gerar código de 8 caracteres (4 grupos de 2)
        code = ''.join(secrets.choice(string.digits) for _ in range(8))
        formatted_code = f"{code[:2]}-{code[2:4]}-{code[4:6]}-{code[6:8]}"
        codes.append(formatted_code)
    
    return codes

def validate_backup_code(master_user, code):
    """
    Valida e consome um código de backup
    """
    if not master_user.backup_codes:
        return False
    
    # Normalizar o código (remover hífens e espaços)
    normalized_code = code.replace('-', '').replace(' ', '').strip()
    
    for backup_code in master_user.backup_codes:
        normalized_backup = backup_code.replace('-', '').replace(' ', '').strip()
        if normalized_code == normalized_backup:
            # Remover o código usado da lista
            master_user.backup_codes.remove(backup_code)
            master_user.save()
            return True
    
    return False

def is_suspicious_activity(request, user):
    """
    Detecta atividade suspeita baseada em padrões
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Verificar múltiplos IPs para o mesmo usuário em pouco tempo
    recent_logs = SecurityLog.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(minutes=30)
    ).values_list('ip_address', flat=True).distinct()
    
    if len(recent_logs) > 3:
        return True, "Múltiplos IPs em pouco tempo"
    
    # Verificar user agents muito diferentes
    recent_user_agents = SecurityLog.objects.filter(
        user=user,
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).values_list('user_agent', flat=True).distinct()
    
    if len(recent_user_agents) > 2:
        return True, "Múltiplos user agents"
    
    # Verificar horários incomuns (fora do horário comercial)
    current_hour = timezone.now().hour
    if current_hour < 6 or current_hour > 22:
        return True, "Acesso fora do horário comercial"
    
    return False, None

def validate_ip_whitelist(ip_address, whitelist):
    """
    Valida se um IP está na whitelist
    """
    import ipaddress
    
    try:
        ip = ipaddress.ip_address(ip_address)
        
        for allowed_ip in whitelist:
            try:
                # Verificar se é uma rede (CIDR)
                if '/' in allowed_ip:
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if ip in network:
                        return True
                else:
                    # Verificar IP exato
                    if ip == ipaddress.ip_address(allowed_ip):
                        return True
            except:
                continue
        
        return False
    
    except:
        return False

def get_geolocation(ip_address):
    """
    Obtém localização aproximada do IP (requer serviço externo)
    """
    # Implementação básica - pode ser expandida com serviços como GeoIP
    try:
        import requests
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
    except:
        pass
    
    return None

def cleanup_old_logs(days=90):
    """
    Remove logs antigos para manter a performance
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = SecurityLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
    return deleted_count
