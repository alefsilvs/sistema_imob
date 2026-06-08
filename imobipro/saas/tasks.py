from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import Tenant, PlanoComercial
import logging

logger = logging.getLogger(__name__)

@shared_task
def verificar_trials_expirando():
    """
    Task para verificar trials que estão expirando e enviar notificações
    """
    hoje = timezone.now().date()
    
    # Tenants com trial expirando em 7 dias
    trials_7_dias = Tenant.objects.filter(
        status='trial',
        trial_ate__date=hoje + timedelta(days=7)
    )
    
    # Tenants com trial expirando em 3 dias
    trials_3_dias = Tenant.objects.filter(
        status='trial',
        trial_ate__date=hoje + timedelta(days=3)
    )
    
    # Tenants com trial expirando em 1 dia
    trials_1_dia = Tenant.objects.filter(
        status='trial',
        trial_ate__date=hoje + timedelta(days=1)
    )
    
    # Tenants com trial expirando hoje
    trials_hoje = Tenant.objects.filter(
        status='trial',
        trial_ate__date=hoje
    )
    
    # Enviar notificações
    for tenant in trials_7_dias:
        enviar_notificacao_trial.delay(tenant.id, 7)
    
    for tenant in trials_3_dias:
        enviar_notificacao_trial.delay(tenant.id, 3)
    
    for tenant in trials_1_dia:
        enviar_notificacao_trial.delay(tenant.id, 1)
    
    for tenant in trials_hoje:
        enviar_notificacao_trial.delay(tenant.id, 0)
    
    logger.info(f"Verificação de trials concluída: {len(trials_7_dias + trials_3_dias + trials_1_dia + trials_hoje)} notificações enviadas")

@shared_task
def enviar_notificacao_trial(tenant_id, dias_restantes):
    """
    Enviar notificação por email sobre trial expirando
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        if dias_restantes > 0:
            subject = f"Seu período gratuito expira em {dias_restantes} dia{'s' if dias_restantes > 1 else ''}"
            template = 'saas/emails/trial_expirando.html'
        else:
            subject = "Seu período gratuito expirou hoje"
            template = 'saas/emails/trial_expirado.html'
        
        # Obter planos disponíveis para upgrade
        planos_disponiveis = PlanoComercial.objects.filter(
            ativo=True,
            is_trial=False
        ).order_by('preco_mensal')
        
        context = {
            'tenant': tenant,
            'dias_restantes': dias_restantes,
            'planos_disponiveis': planos_disponiveis,
            'url_planos': f"{settings.SITE_URL}/saas/planos/",
            'url_dashboard': f"{settings.SITE_URL}/",
        }
        
        html_message = render_to_string(template, context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[tenant.usuario_admin.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de trial enviado para {tenant.nome_empresa} ({dias_restantes} dias restantes)")
        
    except Tenant.DoesNotExist:
        logger.error(f"Tenant {tenant_id} não encontrado")
    except Exception as e:
        logger.error(f"Erro ao enviar email de trial para tenant {tenant_id}: {str(e)}")

@shared_task
def suspender_trials_expirados():
    """
    Suspender tenants com trial expirado
    """
    ontem = timezone.now().date() - timedelta(days=1)
    
    trials_expirados = Tenant.objects.filter(
        status='trial',
        trial_ate__date__lt=ontem
    )
    
    count = 0
    for tenant in trials_expirados:
        tenant.status = 'suspenso'
        tenant.save()
        
        # Enviar email de suspensão
        enviar_email_suspensao.delay(tenant.id)
        count += 1
    
    logger.info(f"Suspensos {count} tenants com trial expirado")
    return count

@shared_task
def enviar_email_suspensao(tenant_id):
    """
    Enviar email informando sobre suspensão da conta
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        subject = "Conta suspensa - Período gratuito expirado"
        template = 'saas/emails/conta_suspensa.html'
        
        planos_disponiveis = PlanoComercial.objects.filter(
            ativo=True,
            is_trial=False
        ).order_by('preco_mensal')
        
        context = {
            'tenant': tenant,
            'planos_disponiveis': planos_disponiveis,
            'url_planos': f"{settings.SITE_URL}/saas/planos/",
            'url_suporte': f"{settings.SITE_URL}/contato/",
        }
        
        html_message = render_to_string(template, context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[tenant.usuario_admin.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de suspensão enviado para {tenant.nome_empresa}")
        
    except Tenant.DoesNotExist:
        logger.error(f"Tenant {tenant_id} não encontrado")
    except Exception as e:
        logger.error(f"Erro ao enviar email de suspensão para tenant {tenant_id}: {str(e)}")

@shared_task
def gerar_relatorio_trials():
    """
    Gerar relatório diário de status dos trials
    """
    hoje = timezone.now().date()
    
    # Estatísticas
    total_trials = Tenant.objects.filter(status='trial').count()
    trials_ativos = Tenant.objects.filter(
        status='trial',
        trial_ate__date__gte=hoje
    ).count()
    trials_expirados = Tenant.objects.filter(
        status='trial',
        trial_ate__date__lt=hoje
    ).count()
    
    # Trials expirando nos próximos 7 dias
    trials_expirando = Tenant.objects.filter(
        status='trial',
        trial_ate__date__range=[hoje, hoje + timedelta(days=7)]
    ).count()
    
    # Novos trials hoje
    novos_trials = Tenant.objects.filter(
        status='trial',
        data_criacao__date=hoje
    ).count()
    
    relatorio = {
        'data': hoje.isoformat(),
        'total_trials': total_trials,
        'trials_ativos': trials_ativos,
        'trials_expirados': trials_expirados,
        'trials_expirando_7_dias': trials_expirando,
        'novos_trials_hoje': novos_trials
    }
    
    logger.info(f"Relatório de trials: {relatorio}")
    return relatorio