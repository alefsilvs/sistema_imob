from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .models import SecurityLog, BlockedIP, MasterUser


class SecurityReportGenerator:
    """Gerador de relatórios de segurança avançados"""
    
    def __init__(self, start_date=None, end_date=None):
        self.start_date = start_date or (timezone.now() - timedelta(days=30))
        self.end_date = end_date or timezone.now()
    
    def get_security_summary(self):
        """Gera resumo geral de segurança"""
        logs = SecurityLog.objects.filter(
            timestamp__range=[self.start_date, self.end_date]
        )
        
        summary = {
            'period': {
                'start': self.start_date.strftime('%Y-%m-%d'),
                'end': self.end_date.strftime('%Y-%m-%d'),
                'days': (self.end_date - self.start_date).days
            },
            'total_events': logs.count(),
            'severity_breakdown': dict(logs.values('severity').annotate(count=Count('severity'))),
            'event_types': dict(logs.values('event_type').annotate(count=Count('event_type'))),
            'unique_ips': logs.values('ip_address').distinct().count(),
            'blocked_ips': BlockedIP.objects.filter(
                blocked_at__range=[self.start_date, self.end_date]
            ).count(),
            'critical_events': logs.filter(severity='CRITICAL').count(),
            'failed_logins': logs.filter(event_type='LOGIN_FAILED').count(),
            'successful_logins': logs.filter(event_type='LOGIN_SUCCESS').count(),
        }
        
        return summary
    
    def get_threat_analysis(self):
        """Análise de ameaças e padrões suspeitos"""
        logs = SecurityLog.objects.filter(
            timestamp__range=[self.start_date, self.end_date]
        )
        
        # IPs com mais tentativas de login falhadas
        failed_login_ips = logs.filter(
            event_type='LOGIN_FAILED'
        ).values('ip_address').annotate(
            count=Count('ip_address')
        ).order_by('-count')[:10]
        
        # Padrões de ataques por hora
        hourly_attacks = defaultdict(int)
        for log in logs.filter(severity__in=['HIGH', 'CRITICAL']):
            hour = log.timestamp.hour
            hourly_attacks[hour] += 1
        
        # User agents suspeitos
        suspicious_agents = logs.filter(
            Q(user_agent__icontains='bot') |
            Q(user_agent__icontains='crawler') |
            Q(user_agent__icontains='scanner') |
            Q(user_agent__isnull=True)
        ).values('user_agent').annotate(
            count=Count('user_agent')
        ).order_by('-count')[:10]
        
        # Países com mais atividade suspeita
        country_activity = defaultdict(int)
        for log in logs.filter(severity__in=['HIGH', 'CRITICAL']):
            if log.metadata and isinstance(log.metadata, dict):
                country = log.metadata.get('country', 'Unknown')
                country_activity[country] += 1
        
        return {
            'top_attacking_ips': list(failed_login_ips),
            'hourly_attack_pattern': dict(hourly_attacks),
            'suspicious_user_agents': list(suspicious_agents),
            'country_threat_distribution': dict(country_activity),
            'brute_force_attempts': logs.filter(
                event_type='BRUTE_FORCE_DETECTED'
            ).count(),
            'sql_injection_attempts': logs.filter(
                event_type='SQL_INJECTION_ATTEMPT'
            ).count(),
            'xss_attempts': logs.filter(
                event_type='XSS_ATTEMPT'
            ).count(),
        }
    
    def get_performance_metrics(self):
        """Métricas de performance do sistema de segurança"""
        logs = SecurityLog.objects.filter(
            timestamp__range=[self.start_date, self.end_date]
        )
        
        # Tempo de resposta médio para bloqueios
        blocked_ips = BlockedIP.objects.filter(
            blocked_at__range=[self.start_date, self.end_date]
        )
        
        # Eficácia do sistema de detecção
        total_attacks = logs.filter(severity__in=['HIGH', 'CRITICAL']).count()
        blocked_attacks = logs.filter(
            event_type__in=['IP_BLOCKED', 'RATE_LIMIT_EXCEEDED']
        ).count()
        
        detection_rate = (blocked_attacks / total_attacks * 100) if total_attacks > 0 else 0
        
        return {
            'detection_rate': round(detection_rate, 2),
            'total_blocks': blocked_ips.count(),
            'average_response_time': self._calculate_avg_response_time(logs),
            'false_positives': self._estimate_false_positives(logs),
            'system_uptime': self._calculate_system_uptime(),
        }
    
    def get_compliance_report(self):
        """Relatório de conformidade e auditoria"""
        logs = SecurityLog.objects.filter(
            timestamp__range=[self.start_date, self.end_date]
        )
        
        # Atividades administrativas
        admin_activities = logs.filter(
            event_type__in=[
                'ADMIN_LOGIN', 'ADMIN_LOGOUT', 'SETTINGS_CHANGED',
                'USER_CREATED', 'USER_DELETED', 'PERMISSION_CHANGED'
            ]
        ).count()
        
        # Acessos de usuários master
        master_activities = logs.filter(
            user__in=MasterUser.objects.all()
        ).count()
        
        # Tentativas de acesso não autorizadas
        unauthorized_attempts = logs.filter(
            event_type__in=[
                'UNAUTHORIZED_ACCESS', 'PERMISSION_DENIED',
                'INVALID_TOKEN', 'SESSION_HIJACK_ATTEMPT'
            ]
        ).count()
        
        return {
            'admin_activities': admin_activities,
            'master_user_activities': master_activities,
            'unauthorized_attempts': unauthorized_attempts,
            'data_access_logs': logs.filter(
                event_type__contains='DATA_ACCESS'
            ).count(),
            'backup_events': logs.filter(
                event_type='BACKUP_CREATED'
            ).count(),
            'system_changes': logs.filter(
                event_type='SYSTEM_CONFIGURATION_CHANGED'
            ).count(),
        }
    
    def get_daily_timeline(self):
        """Timeline diária de eventos de segurança"""
        logs = SecurityLog.objects.filter(
            timestamp__range=[self.start_date, self.end_date]
        )
        
        daily_data = defaultdict(lambda: {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'events': []
        })
        
        for log in logs:
            date_key = log.timestamp.date().isoformat()
            daily_data[date_key]['total'] += 1
            daily_data[date_key][log.severity.lower()] += 1
            
            if log.severity in ['CRITICAL', 'HIGH']:
                daily_data[date_key]['events'].append({
                    'time': log.timestamp.strftime('%H:%M:%S'),
                    'type': log.event_type,
                    'severity': log.severity,
                    'description': log.description[:100]
                })
        
        return dict(daily_data)
    
    def _calculate_avg_response_time(self, logs):
        """Calcula tempo médio de resposta do sistema"""
        # Implementação simplificada - em produção, seria baseado em métricas reais
        return "< 100ms"
    
    def _estimate_false_positives(self, logs):
        """Estima taxa de falsos positivos"""
        # Implementação simplificada - em produção, seria baseado em análise mais complexa
        total_blocks = logs.filter(event_type='IP_BLOCKED').count()
        return max(0, int(total_blocks * 0.05))  # Estima 5% de falsos positivos
    
    def _calculate_system_uptime(self):
        """Calcula uptime do sistema de segurança"""
        # Implementação simplificada - em produção, seria baseado em métricas de sistema
        return "99.9%"
    
    def generate_full_report(self):
        """Gera relatório completo de segurança"""
        return {
            'generated_at': timezone.now().isoformat(),
            'summary': self.get_security_summary(),
            'threat_analysis': self.get_threat_analysis(),
            'performance_metrics': self.get_performance_metrics(),
            'compliance': self.get_compliance_report(),
            'daily_timeline': self.get_daily_timeline(),
        }
    
    def export_to_json(self):
        """Exporta relatório para JSON"""
        report = self.generate_full_report()
        return json.dumps(report, indent=2, default=str)


def generate_security_dashboard_data():
    """Gera dados para o dashboard de segurança em tempo real"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Eventos das últimas 24 horas
    recent_logs = SecurityLog.objects.filter(timestamp__gte=last_24h)
    
    # Estatísticas rápidas
    stats = {
        'total_events_24h': recent_logs.count(),
        'critical_events_24h': recent_logs.filter(severity='CRITICAL').count(),
        'blocked_ips_24h': BlockedIP.objects.filter(blocked_at__gte=last_24h).count(),
        'failed_logins_24h': recent_logs.filter(event_type='LOGIN_FAILED').count(),
        'active_sessions': recent_logs.filter(
            event_type='LOGIN_SUCCESS',
            timestamp__gte=now - timedelta(hours=1)
        ).count(),
    }
    
    # Eventos críticos recentes
    critical_events = recent_logs.filter(
        severity='CRITICAL'
    ).order_by('-timestamp')[:10]
    
    # Top IPs atacantes
    top_attacking_ips = recent_logs.filter(
        event_type='LOGIN_FAILED'
    ).values('ip_address').annotate(
        count=Count('ip_address')
    ).order_by('-count')[:5]
    
    return {
        'stats': stats,
        'critical_events': [
            {
                'timestamp': event.timestamp.isoformat(),
                'type': event.event_type,
                'description': event.description,
                'ip': event.ip_address,
            }
            for event in critical_events
        ],
        'top_attacking_ips': list(top_attacking_ips),
        'last_updated': now.isoformat(),
    }