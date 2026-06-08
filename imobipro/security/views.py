from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import timedelta
import os
import json
import csv
import pyotp
import qrcode
import io
import base64
from .models import MasterUser, SecurityLog, LoginAttempt, BlockedIP, SystemSetting
from .utils import (
    get_client_ip, log_security_event, generate_hardware_fingerprint,
    check_password_strength, generate_secure_token, is_suspicious_activity,
    generate_backup_codes, validate_backup_code
)
from .forms import MasterUserCreationForm, SecuritySettingsForm, TwoFactorSetupForm
from .reports import SecurityReportGenerator, generate_security_dashboard_data

def is_master_user(user):
    """
    Verifica se o usuário é um master user
    """
    return user.is_authenticated and hasattr(user, 'master_profile')

@login_required
@user_passes_test(is_master_user)
def security_dashboard(request):
    """
    Dashboard principal de segurança
    """
    # Estatísticas de segurança
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    
    stats = {
        'total_logs': SecurityLog.objects.count(),
        'today_logs': SecurityLog.objects.filter(timestamp__date=today).count(),
        'week_critical': SecurityLog.objects.filter(
            timestamp__gte=week_ago,
            severity='CRITICAL'
        ).count(),
        'blocked_ips': BlockedIP.objects.filter(blocked_until__gt=timezone.now()).count(),
        'failed_logins_today': LoginAttempt.objects.filter(
            timestamp__date=today,
            success=False
        ).count()
    }
    
    # Logs recentes
    recent_logs = SecurityLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Tentativas de login recentes
    recent_attempts = LoginAttempt.objects.order_by('-timestamp')[:10]
    
    # IPs bloqueados
    blocked_ips = BlockedIP.objects.filter(blocked_until__gt=timezone.now())[:10]
    
    context = {
        'stats': stats,
        'recent_logs': recent_logs,
        'recent_attempts': recent_attempts,
        'blocked_ips': blocked_ips,
    }
    
    return render(request, 'security/dashboard.html', context)

@login_required
@user_passes_test(is_master_user)
def security_logs(request):
    """
    Visualização de logs de segurança
    """
    from django.http import HttpResponse
    import csv
    from datetime import datetime, timedelta
    
    logs = SecurityLog.objects.select_related('user').order_by('-timestamp')
    
    # Filtros
    severity = request.GET.get('severity')
    event_type = request.GET.get('event_type')
    user_id = request.GET.get('user')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if severity:
        logs = logs.filter(severity=severity)
    
    if event_type:
        logs = logs.filter(event_type=event_type)
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    if search:
        logs = logs.filter(
            Q(ip_address__icontains=search) |
            Q(description__icontains=search) |
            Q(user_agent__icontains=search)
        )
    
    # Exportação CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="security_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Severidade', 'Tipo de Evento', 'Usuário', 'IP', 'Descrição', 'User Agent'])
        
        for log in logs[:1000]:  # Limitar a 1000 registros para performance
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.get_severity_display(),
                log.get_event_type_display() or log.event_type,
                log.user.username if log.user else 'N/A',
                log.ip_address or 'N/A',
                log.description,
                log.user_agent or 'N/A'
            ])
        
        return response
    
    # Estatísticas para as últimas 24 horas
    last_24h = datetime.now() - timedelta(hours=24)
    critical_count = SecurityLog.objects.filter(
        timestamp__gte=last_24h,
        severity='CRITICAL'
    ).count()
    
    high_count = SecurityLog.objects.filter(
        timestamp__gte=last_24h,
        severity='HIGH'
    ).count()
    
    unique_ips = SecurityLog.objects.filter(
        timestamp__gte=last_24h
    ).values('ip_address').distinct().count()
    
    # Paginação
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opções para filtros
    severities = SecurityLog.objects.values_list('severity', flat=True).distinct()
    event_types = SecurityLog.objects.values_list('event_type', flat=True).distinct()
    users = User.objects.filter(securitylog__isnull=False).distinct()
    
    context = {
        'page_obj': page_obj,
        'severities': severities,
        'event_types': event_types,
        'users': users,
        'current_filters': {
            'severity': severity,
            'event_type': event_type,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        },
        'critical_count': critical_count,
        'high_count': high_count,
        'unique_ips': unique_ips,
    }
    
    return render(request, 'security/logs.html', context)

@login_required
@user_passes_test(is_master_user)
def blocked_ips_view(request):
    """
    Gerenciamento de IPs bloqueados
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        ip_id = request.POST.get('ip_id')
        
        if action == 'unblock' and ip_id:
            blocked_ip = get_object_or_404(BlockedIP, id=ip_id)
            blocked_ip.blocked_until = timezone.now()
            blocked_ip.save()
            
            log_security_event(
                request,
                'IP_UNBLOCKED',
                f'IP desbloqueado manualmente: {blocked_ip.ip_address}',
                severity='MEDIUM'
            )
            
            messages.success(request, f'IP {blocked_ip.ip_address} desbloqueado com sucesso.')
        
        elif action == 'block':
            ip_address = request.POST.get('ip_address')
            reason = request.POST.get('reason', 'Bloqueio manual')
            hours = int(request.POST.get('hours', 24))
            
            if ip_address:
                BlockedIP.objects.update_or_create(
                    ip_address=ip_address,
                    defaults={
                        'reason': reason,
                        'blocked_until': timezone.now() + timedelta(hours=hours)
                    }
                )
                
                log_security_event(
                    request,
                    'IP_BLOCKED_MANUAL',
                    f'IP bloqueado manualmente: {ip_address}',
                    severity='MEDIUM'
                )
                
                messages.success(request, f'IP {ip_address} bloqueado por {hours} horas.')
        
        return redirect('security:blocked_ips')
    
    # Listar IPs bloqueados
    blocked_ips = BlockedIP.objects.order_by('-created_at')
    active_blocks = blocked_ips.filter(blocked_until__gt=timezone.now())
    expired_blocks = blocked_ips.filter(blocked_until__lte=timezone.now())[:20]
    
    context = {
        'active_blocks': active_blocks,
        'expired_blocks': expired_blocks,
    }
    
    return render(request, 'security/blocked_ips.html', context)

def master_login(request):
    """
    Login específico para usuário master
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        totp_code = request.POST.get('totp_code')
        
        ip_address = get_client_ip(request)
        
        # Verificar se IP está bloqueado
        try:
            blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
            if blocked_ip.is_blocked():
                messages.error(request, 'Seu IP está bloqueado. Tente novamente mais tarde.')
                return render(request, 'security/master_login.html')
        except BlockedIP.DoesNotExist:
            pass
        
        user = authenticate(request, username=username, password=password)
        
        if user and hasattr(user, 'master_profile'):
            master_user = user.master_profile
            
            # Verificar IP autorizado
            if not master_user.is_ip_authorized(ip_address):
                log_security_event(
                    request,
                    'MASTER_UNAUTHORIZED_IP',
                    f'Tentativa de login master de IP não autorizado: {ip_address}',
                    severity='CRITICAL'
                )
                messages.error(request, 'IP não autorizado para acesso master.')
                return render(request, 'security/master_login.html')
            
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
                        'MASTER_HARDWARE_MISMATCH',
                        f'Hardware fingerprint não confere para usuário master',
                        severity='CRITICAL'
                    )
                    messages.error(request, 'Hardware não autorizado.')
                    return render(request, 'security/master_login.html')
            
            # Verificar 2FA se habilitado
            if master_user.two_factor_enabled:
                if not totp_code:
                    messages.error(request, 'Código 2FA é obrigatório.')
                    return render(request, 'security/master_login.html')
                
                # Verificar se é um código de backup
                is_backup_code = len(totp_code.replace('-', '').replace(' ', '')) == 8
                
                if is_backup_code:
                    # Validar código de backup
                    if not validate_backup_code(master_user, totp_code):
                        log_security_event(
                            request,
                            'MASTER_BACKUP_CODE_FAILED',
                            f'Código de backup inválido para usuário master',
                            severity='HIGH'
                        )
                        messages.error(request, 'Código de backup inválido ou já utilizado.')
                        return render(request, 'security/master_login.html')
                    
                    # Log do uso de código de backup
                    log_security_event(
                        request,
                        'MASTER_BACKUP_CODE_USED',
                        f'Código de backup utilizado para login master',
                        severity='MEDIUM'
                    )
                else:
                    # Validar código TOTP normal
                    totp = pyotp.TOTP(master_user.two_factor_secret)
                    if not totp.verify(totp_code):
                        log_security_event(
                            request,
                            'MASTER_2FA_FAILED',
                            f'Código 2FA inválido para usuário master',
                            severity='HIGH'
                        )
                        messages.error(request, 'Código 2FA inválido.')
                        return render(request, 'security/master_login.html')
            
            # Login bem-sucedido
            login(request, user)
            
            log_security_event(
                request,
                'MASTER_LOGIN_SUCCESS',
                f'Login master bem-sucedido',
                severity='MEDIUM'
            )
            
            return redirect('security:dashboard')
        
        else:
            log_security_event(
                request,
                'MASTER_LOGIN_FAILED',
                f'Tentativa de login master falhada para: {username}',
                severity='HIGH'
            )
            messages.error(request, 'Credenciais inválidas.')
    
    return render(request, 'security/master_login.html')

@login_required
@user_passes_test(is_master_user)
def setup_2fa(request):
    """
    Configuração de autenticação de dois fatores
    """
    master_user = request.user.master_profile
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            # Gerar novo secret
            secret = pyotp.random_base32()
            master_user.two_factor_secret = secret
            
            # Gerar QR Code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=request.user.username,
                issuer_name="Sistema Imobiliário"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            
            context = {
                'secret': secret,
                'qr_code': qr_code_data,
                'step': 'verify'
            }
            
            return render(request, 'security/setup_2fa.html', context)
        
        elif action == 'verify':
            secret = request.POST.get('secret')
            code = request.POST.get('code')
            
            totp = pyotp.TOTP(secret)
            if totp.verify(code):
                # Gerar códigos de backup
                backup_codes = generate_backup_codes()
                
                master_user.two_factor_secret = secret
                master_user.two_factor_enabled = True
                master_user.backup_codes = backup_codes
                master_user.save()
                
                log_security_event(
                    request,
                    'MASTER_2FA_ENABLED',
                    f'2FA habilitado para usuário master',
                    severity='MEDIUM'
                )
                
                # Exibir códigos de backup
                context = {
                    'backup_codes': backup_codes,
                    'step': 'backup_codes'
                }
                return render(request, 'security/setup_2fa.html', context)
            else:
                messages.error(request, 'Código inválido. Tente novamente.')
                context = {
                    'secret': secret,
                    'step': 'verify'
                }
                return render(request, 'security/setup_2fa.html', context)
        
        elif action == 'disable':
            master_user.two_factor_enabled = False
            master_user.two_factor_secret = ''
            master_user.save()
            
            log_security_event(
                request,
                'MASTER_2FA_DISABLED',
                f'2FA desabilitado para usuário master',
                severity='MEDIUM'
            )
            
            messages.success(request, '2FA desabilitado.')
            return redirect('security:dashboard')
    
    context = {
        'two_factor_enabled': master_user.two_factor_enabled,
        'step': 'setup'
    }
    
    return render(request, 'security/setup_2fa.html', context)

@login_required
@user_passes_test(is_master_user)
def system_settings(request):
    """
    Configurações do sistema de segurança
    """
    if request.method == 'POST':
        # Atualizar configurações
        for key, value in request.POST.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                SystemSetting.set_setting(setting_key, value)
        
        log_security_event(
            request,
            'SYSTEM_SETTINGS_CHANGED',
            f'Configurações do sistema alteradas',
            severity='MEDIUM'
        )
        
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('security:system_settings')
    
    # Carregar configurações atuais
    settings_data = {
        'max_login_attempts': SystemSetting.get_setting('max_login_attempts', 5),
        'lockout_duration': SystemSetting.get_setting('lockout_duration', 60),
        'session_timeout': SystemSetting.get_setting('session_timeout', 30),
        'password_min_length': SystemSetting.get_setting('password_min_length', 8),
        'require_2fa': SystemSetting.get_setting('require_2fa', False),
        'log_retention_days': SystemSetting.get_setting('log_retention_days', 90),
    }
    
    context = {
        'settings': settings_data
    }
    
    return render(request, 'security/system_settings.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def api_security_status(request):
    """
    API para verificar status de segurança
    """
    if not request.user.is_authenticated or not hasattr(request.user, 'master_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        dashboard_data = generate_security_dashboard_data()
        return JsonResponse({
            'status': 'success',
            **dashboard_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def security_reports(request):
    """View para relatórios de segurança avançados"""
    if not is_master_user(request.user):
        messages.error(request, 'Acesso negado. Apenas usuários master podem acessar relatórios.')
        return redirect('security:dashboard')
    
    # Parâmetros de data
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('type', 'summary')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = timezone.now()
    
    # Gerar relatório
    generator = SecurityReportGenerator(start_date, end_date)
    
    # Exportação JSON
    if request.GET.get('export') == 'json':
        response = HttpResponse(
            generator.export_to_json(),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="security_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json"'
        return response
    
    # Dados do relatório baseado no tipo
    if report_type == 'summary':
        report_data = generator.get_security_summary()
    elif report_type == 'threats':
        report_data = generator.get_threat_analysis()
    elif report_type == 'performance':
        report_data = generator.get_performance_metrics()
    elif report_type == 'compliance':
        report_data = generator.get_compliance_report()
    elif report_type == 'timeline':
        report_data = generator.get_daily_timeline()
    else:
        report_data = generator.generate_full_report()
    
    context = {
        'report_data': report_data,
        'report_type': report_type,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'available_types': [
            ('summary', 'Resumo Geral'),
            ('threats', 'Análise de Ameaças'),
            ('performance', 'Métricas de Performance'),
            ('compliance', 'Conformidade e Auditoria'),
            ('timeline', 'Timeline Diária'),
            ('full', 'Relatório Completo'),
        ]
    }
    
    return render(request, 'security/reports.html', context)


@csrf_exempt
def api_security_alerts(request):
    """API para alertas de segurança em tempo real"""
    if not request.user.is_authenticated or not is_master_user(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # Últimos alertas críticos (últimos 10 minutos)
    recent_time = timezone.now() - timedelta(minutes=10)
    
    alerts = SecurityLog.objects.filter(
        timestamp__gte=recent_time,
        severity__in=['CRITICAL', 'HIGH']
    ).order_by('-timestamp')[:20]
    
    alert_data = []
    for alert in alerts:
        alert_data.append({
            'id': alert.id,
            'timestamp': alert.timestamp.isoformat(),
            'severity': alert.severity,
            'event_type': alert.event_type,
            'description': alert.description,
            'ip_address': alert.ip_address,
            'user': alert.user.username if alert.user else None,
            'metadata': alert.metadata,
        })
    
    return JsonResponse({
        'alerts': alert_data,
        'count': len(alert_data),
        'last_updated': timezone.now().isoformat(),
    })
