from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max, Min
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
import csv
import html as html_lib
import json
import logging
import os
import re
from datetime import datetime, timedelta
from .models import (
    TemplateNotificacao, Notificacao, NotificacaoAgendada, 
    CategoriaTemplate, EstatisticaNotificacao
)
from core.models import Inquilino
from contratos.models import Contrato
from saas.models import Tenant

logger = logging.getLogger(__name__)


def _whatsapp_text_from_body(body, formato=None):
    if body is None:
        return ''
    text = str(body)
    if (formato or '').upper() == 'HTML' or '<' in text:
        from django.utils.html import strip_tags
        text = re.sub(r'(?i)<br\s*/?>', '\n', text)
        text = re.sub(r'(?i)</p\s*>', '\n', text)
        text = strip_tags(text)
    text = html_lib.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _resumo_erro_notificacao(notificacao):
    try:
        if notificacao.erro_envio:
            msg = str(notificacao.erro_envio)
        else:
            last = notificacao.log_tentativas[-1] if notificacao.log_tentativas else None
            msg = ''
            if isinstance(last, dict):
                msg = last.get('error_message') or last.get('message') or ''
                if not msg:
                    title = last.get('error_title') or last.get('error_type') or ''
                    msg = title

        m = (msg or '').strip()
        if not m:
            return ''

        if 'HTTPConnectionPool' in m and "port=8080" in m:
            return 'WhatsApp: Evolution API offline (localhost:8080)'
        if 'BadCredentials' in m or 'Username and Password not accepted' in m:
            return 'E-mail: senha/usuário SMTP inválidos (Gmail App Password)'
        if len(m) > 90:
            return m[:87] + '...'
        return m
    except Exception:
        return ''


def enviar_notificacao_individual(notificacao):
    """Envia uma notificação individual por email ou outro canal suportado"""
    try:
        if notificacao.canal == 'WHATSAPP':
            from .whatsapp_service import WhatsAppService

            service = WhatsAppService()
            if not service.check_api_health():
                notificacao.status = 'ERRO'
                notificacao.erro_envio = 'WhatsApp: Evolution API offline (Docker desligado?)'
                notificacao.log_tentativas = notificacao.log_tentativas or []
                notificacao.log_tentativas.append({
                    'timestamp': timezone.now().isoformat(),
                    'status': 'erro',
                    'error_type': 'whatsapp_offline',
                    'error_message': notificacao.erro_envio,
                })
                notificacao.save()
                return False

            st = service.get_status()
            if st.get('status') != 'connected':
                notificacao.status = 'ERRO'
                notificacao.erro_envio = 'WhatsApp: instância desconectada (leia o QR Code no WhatsApp Dashboard)'
                notificacao.log_tentativas = notificacao.log_tentativas or []
                notificacao.log_tentativas.append({
                    'timestamp': timezone.now().isoformat(),
                    'status': 'erro',
                    'error_type': 'whatsapp_disconnected',
                    'error_message': notificacao.erro_envio,
                })
                notificacao.save()
                return False

            res = service.send_message(notificacao.destinatario, notificacao.corpo)
            if res.get('success'):
                notificacao.status = 'ENVIADA'
                notificacao.data_envio = timezone.now()
                notificacao.save()
                return True

            notificacao.status = 'ERRO'
            notificacao.erro_envio = res.get('error') or 'Erro ao enviar WhatsApp'
            notificacao.log_tentativas = notificacao.log_tentativas or []
            notificacao.log_tentativas.append({
                'timestamp': timezone.now().isoformat(),
                'status': 'erro',
                'error_type': 'whatsapp',
                'error_message': notificacao.erro_envio,
            })
            notificacao.save()
            return False

        # Envio via Email (código existente)
        # Verificar se DEFAULT_FROM_EMAIL está configurado
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sistema.com')
        
        send_mail(
            subject=notificacao.assunto,
            message=notificacao.corpo,
            from_email=from_email,
            recipient_list=[notificacao.destinatario],
            html_message=notificacao.corpo_html if notificacao.corpo_html else None,
            fail_silently=False,
        )
        
        notificacao.status = 'ENVIADA'
        notificacao.data_envio = timezone.now()
        notificacao.save()
        return True
            
    except Exception as e:
        # Erro geral
        notificacao.status = 'ERRO'
        notificacao.log_tentativas = notificacao.log_tentativas or []
        notificacao.log_tentativas.append({
            'timestamp': timezone.now().isoformat(),
            'status': 'erro',
            'error_type': 'general',
            'error_message': str(e)
        })
        notificacao.save()
        
        logger.error(f"Erro geral ao enviar notificação: {str(e)}")
        return False


@login_required
def listar_notificacoes(request):
    """Lista todas as notificações"""
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template', 'contrato'
    ).order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    canal = request.GET.get('canal')
    busca = request.GET.get('busca')
    
    if status:
        notificacoes = notificacoes.filter(status=status)
    if canal:
        notificacoes = notificacoes.filter(canal=canal)
    if busca:
        notificacoes = notificacoes.filter(
            Q(assunto__icontains=busca) |
            Q(inquilino__nome__icontains=busca) |
            Q(destinatario__icontains=busca)
        )
    
    paginator = Paginator(notificacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Notificacao.STATUS_CHOICES,
        'canal_choices': Notificacao.CANAL_CHOICES,
    }
    
    return render(request, 'notificacoes/listar.html', context)


@login_required
@ensure_csrf_cookie
def enviar_notificacoes(request):
    """View para enviar notificações"""
    tenant = getattr(request, 'tenant', None)
    if request.method == 'POST':
        template_id = request.POST.get('template')
        inquilinos_ids = request.POST.getlist('inquilinos')
        canal = request.POST.get('canal', 'EMAIL')  # Novo campo
        
        if not template_id or not inquilinos_ids:
            messages.error(request, 'Selecione um template e pelo menos um inquilino.')
            return redirect('notificacoes:enviar')

        if not tenant:
            messages.error(request, 'Tenant não identificado. Refaça o login e selecione sua empresa.')
            return redirect('notificacoes:enviar')
        
        try:
            template = get_object_or_404(TemplateNotificacao, id=template_id)
            inquilinos = Inquilino.objects.filter(id__in=inquilinos_ids, tenant=tenant, ativo=True)

            if canal == 'EMAIL':
                if not getattr(settings, 'EMAIL_HOST_USER', '') or not getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
                    messages.error(request, 'E-mail não está configurado. Configure EMAIL_HOST_USER e EMAIL_HOST_PASSWORD.')
                    return redirect('notificacoes:enviar')
            elif canal == 'WHATSAPP':
                from .whatsapp_service import WhatsAppService
                service = WhatsAppService()
                if not service.check_api_health():
                    messages.error(request, 'WhatsApp: Evolution API offline. Abra o Docker e use o WhatsApp Dashboard para conectar (QR Code).')
                    return redirect('notificacoes:enviar')
                st = service.get_status()
                if st.get('status') != 'connected':
                    messages.error(request, 'WhatsApp: desconectado. Vá em Notificações → WhatsApp Dashboard e leia o QR Code.')
                    return redirect('notificacoes:enviar')
            
            notificacoes_criadas = 0
            puladas_sem_telefone = 0
            puladas_sem_email = 0
            falhas_envio = 0
            falhas_resumo = {}
            
            for inquilino in inquilinos:
                # Determinar destinatário baseado no canal
                if canal == 'SMS' or canal == 'WHATSAPP':
                    if not inquilino.telefone:
                        puladas_sem_telefone += 1
                        continue
                    destinatario = inquilino.telefone
                else:  # EMAIL
                    if not inquilino.email:
                        puladas_sem_email += 1
                        continue
                    destinatario = inquilino.email
                
                # Buscar contrato ativo do inquilino
                contrato = Contrato.objects.filter(
                    inquilino=inquilino, status='ATIVO'
                ).first()
                
                # Contexto para renderização
                contexto = {
                    'inquilino': inquilino,
                    'contrato': contrato,
                    'inquilino_nome': inquilino.nome,
                    'inquilino_cpf': inquilino.cpf_cnpj or 'Não informado',
                    'inquilino_telefone': inquilino.telefone or 'Não informado',
                    'inquilino_email': inquilino.email or 'Não informado',
                    'inquilino_endereco': inquilino.endereco or 'Não informado',
                    'imovel_endereco': getattr(contrato.imovel, 'endereco_completo', 'N/A') if contrato else 'N/A',
                    'valor_aluguel': str(contrato.valor_aluguel) if contrato else '0,00',
                    'data_vencimento': timezone.now().date() + timedelta(days=30),
                    'dias_para_vencer': 30,
                    'valor_devido': contrato.valor_aluguel if contrato else 0,
                    'data_atual': timezone.now().strftime('%d/%m/%Y'),
                }
                
                # Renderizar template
                assunto = template.renderizar_assunto(contexto)
                corpo = template.renderizar_corpo(contexto)

                if canal == 'WHATSAPP':
                    corpo = _whatsapp_text_from_body(corpo, getattr(template, 'formato', None))
                
                # Criar notificação
                notificacao = Notificacao.objects.create(
                    template=template,
                    inquilino=inquilino,
                    canal=canal,  # Usar canal selecionado
                    destinatario=destinatario,
                    assunto=assunto,
                    corpo=corpo,
                    corpo_html=corpo if template.formato == 'HTML' and canal == 'EMAIL' else '',
                    usuario=request.user  # Adicionar usuário
                )
                
                # Enviar notificação
                if enviar_notificacao_individual(notificacao):
                    notificacoes_criadas += 1
                else:
                    falhas_envio += 1
                    ultimo = notificacao.log_tentativas[-1] if notificacao.log_tentativas else None
                    if isinstance(ultimo, dict):
                        title = ultimo.get('error_title') or ultimo.get('error_type') or 'erro'
                        message = ultimo.get('error_message') or ultimo.get('error_message') or ultimo.get('message') or ''
                        key = f"{title}: {message}" if message else title
                        falhas_resumo[key] = falhas_resumo.get(key, 0) + 1
            
            if notificacoes_criadas > 0:
                canal_nome = 'WhatsApp' if canal == 'WHATSAPP' else ('SMS' if canal == 'SMS' else 'E-mail')
                messages.success(
                    request, 
                    f'{notificacoes_criadas} notificações enviadas via {canal_nome} com sucesso!'
                )

                if puladas_sem_telefone or puladas_sem_email:
                    partes = []
                    if puladas_sem_telefone:
                        partes.append(f'{puladas_sem_telefone} sem telefone')
                    if puladas_sem_email:
                        partes.append(f'{puladas_sem_email} sem e-mail')
                    messages.warning(request, 'Alguns inquilinos foram ignorados: ' + ', '.join(partes) + '.')

                if falhas_envio:
                    if falhas_resumo:
                        top = sorted(falhas_resumo.items(), key=lambda x: x[1], reverse=True)[:2]
                        detalhe = ' | '.join([f'{k} (x{v})' for k, v in top])
                        messages.warning(request, f'{falhas_envio} notificações falharam no envio. {detalhe}')
                    else:
                        messages.warning(request, f'{falhas_envio} notificações falharam no envio. Veja o Histórico para detalhes.')
            else:
                if puladas_sem_telefone or puladas_sem_email:
                    partes = []
                    if puladas_sem_telefone:
                        partes.append(f'{puladas_sem_telefone} sem telefone')
                    if puladas_sem_email:
                        partes.append(f'{puladas_sem_email} sem e-mail')
                    messages.warning(request, 'Nenhuma notificação foi enviada. Inquilinos sem contato válido: ' + ', '.join(partes) + '.')
                elif falhas_envio:
                    if falhas_resumo:
                        top = sorted(falhas_resumo.items(), key=lambda x: x[1], reverse=True)[:2]
                        detalhe = ' | '.join([f'{k} (x{v})' for k, v in top])
                        messages.error(request, f'Nenhuma notificação foi enviada. {detalhe}')
                    else:
                        messages.error(request, f'Nenhuma notificação foi enviada. Falha no envio em {falhas_envio} tentativa(s).')
                else:
                    messages.warning(request, 'Nenhuma notificação foi enviada.')
                
        except Exception as e:
            messages.error(request, f'Erro ao enviar notificações: {str(e)}')
            return redirect('notificacoes:enviar')
        
        return redirect('notificacoes:enviar')
    
    # GET request
    templates = TemplateNotificacao.objects.filter(ativo=True).exclude(
        Q(nome__icontains='banca') | Q(nome__icontains='feira')
    )
    if tenant:
        inquilinos = Inquilino.objects.filter(tenant=tenant, ativo=True)
    else:
        inquilinos = Inquilino.objects.none()
    
    # Obter cidades distintas dos inquilinos para o filtro
    cidades_disponiveis = inquilinos.exclude(
        cidade__isnull=True
    ).exclude(cidade='').values_list('cidade', flat=True).distinct().order_by('cidade')
    
    return render(request, 'notificacoes/enviar.html', {
        'templates': templates,
        'inquilinos': inquilinos,
        'cidades_disponiveis': cidades_disponiveis,
    })


@login_required
@require_POST
def executar_robo_cobranca(request):
    return JsonResponse({'success': False, 'error': 'Robô de cobrança foi desativado.'}, status=400)





@login_required
def preview_notificacao(request):
    """Gera preview de uma notificação antes do envio"""
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        inquilino_id = request.POST.get('inquilino_id')
        canal = request.POST.get('canal', 'EMAIL')
        
        try:
            template = get_object_or_404(TemplateNotificacao, id=template_id)
            inquilino = get_object_or_404(Inquilino, id=inquilino_id)
            
            # Buscar contrato ativo
            contrato = Contrato.objects.filter(
                inquilino=inquilino, status='ATIVO'
            ).first()
            
            # Preparar contexto
            contexto = {
                'inquilino': inquilino,
                'contrato': contrato,
                'data_atual': timezone.now().date(),
            }
            
            # Renderizar template
            assunto = template.renderizar_assunto(contexto)
            corpo = template.renderizar_corpo(contexto)
            
            # Determinar destinatário
            if canal == 'EMAIL':
                destinatario = inquilino.email or 'E-mail não cadastrado'
            elif canal in ['SMS', 'WHATSAPP']:
                destinatario = inquilino.telefone or 'Telefone não cadastrado'
            else:
                destinatario = 'Canal inválido'
            
            preview_data = {
                'template_nome': template.nome,
                'inquilino_nome': inquilino.nome,
                'destinatario': destinatario,
                'canal': canal,
                'assunto': assunto,
                'corpo': corpo,
                'contexto_usado': contexto,
            }
            
            return JsonResponse({
                'success': True,
                'preview': preview_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def preview_template(request, template_id):
    """Preview de template com dados de exemplo"""
    template = get_object_or_404(TemplateNotificacao, id=template_id)
    
    # Usar dados de preview do template ou dados padrão
    contexto = template.preview_dados or {
        'inquilino': {
            'nome': 'João da Silva',
            'email': 'joao@email.com',
            'telefone': '(11) 99999-9999'
        },
        'contrato': {
            'numero': '001/2024',
            'valor_aluguel': 1500.00,
            'data_vencimento': timezone.now().date().replace(day=10)
        },
        'data_atual': timezone.now().date()
    }
    
    try:
        assunto = template.renderizar_assunto(contexto)
        corpo = template.renderizar_corpo(contexto)
        
        preview_data = {
            'template': {
                'id': template.id,
                'nome': template.nome,
                'tipo': template.get_tipo_display(),
                'categoria': template.categoria.nome,
            },
            'assunto': assunto,
            'corpo': corpo,
            'contexto': contexto,
        }
        
        return JsonResponse({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao renderizar template: {str(e)}'
        })


@login_required
def preview_lote(request):
    """Preview em lote para múltiplos destinatários"""
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        inquilinos_ids = request.POST.getlist('inquilinos_ids')
        canal = request.POST.get('canal', 'EMAIL')
        
        try:
            template = get_object_or_404(TemplateNotificacao, id=template_id)
            inquilinos = Inquilino.objects.filter(id__in=inquilinos_ids)
            
            previews = []
            
            for inquilino in inquilinos:
                contrato = Contrato.objects.filter(
                    inquilino=inquilino, status='ATIVO'
                ).first()
                
                contexto = {
                    'inquilino': inquilino,
                    'contrato': contrato,
                    'data_atual': timezone.now().date(),
                }
                
                try:
                    assunto = template.renderizar_assunto(contexto)
                    corpo = template.renderizar_corpo(contexto)
                    
                    if canal == 'EMAIL':
                        destinatario = inquilino.email
                        valido = bool(inquilino.email)
                    elif canal in ['SMS', 'WHATSAPP']:
                        destinatario = inquilino.telefone
                        valido = bool(inquilino.telefone)
                    else:
                        destinatario = None
                        valido = False
                    
                    previews.append({
                        'inquilino_id': inquilino.id,
                        'inquilino_nome': inquilino.nome,
                        'destinatario': destinatario,
                        'valido': valido,
                        'assunto': assunto,
                        'corpo': corpo[:200] + '...' if len(corpo) > 200 else corpo,
                        'erro': None
                    })
                    
                except Exception as e:
                    previews.append({
                        'inquilino_id': inquilino.id,
                        'inquilino_nome': inquilino.nome,
                        'destinatario': None,
                        'valido': False,
                        'assunto': None,
                        'corpo': None,
                        'erro': str(e)
                    })
            
            return JsonResponse({
                'success': True,
                'previews': previews,
                'total': len(previews),
                'validos': len([p for p in previews if p['valido']]),
                'invalidos': len([p for p in previews if not p['valido']])
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
@ensure_csrf_cookie
def enviar_notificacoes_avancado(request):
    """View para envio de notificações com filtros avançados"""
    if request.method == 'POST':
        template_id = request.POST.get('template')
        canal = request.POST.get('canal', 'EMAIL')
        inquilinos_ids = request.POST.getlist('inquilinos')
        
        if not template_id or not inquilinos_ids:
            messages.error(request, 'Selecione um template e pelo menos um destinatário.')
            return redirect('notificacoes:enviar_avancado')
        
        try:
            template = get_object_or_404(TemplateNotificacao, id=template_id)
            inquilinos = Inquilino.objects.filter(id__in=inquilinos_ids)
            
            notificacoes_criadas = 0
            notificacoes_enviadas = 0
            
            for inquilino in inquilinos:
                # Buscar contrato ativo se existir
                contrato = Contrato.objects.filter(
                    inquilino=inquilino, 
                    status='ATIVO'
                ).first()
                
                # Preparar contexto para renderização
                contexto = {
                    'inquilino': inquilino,
                    'contrato': contrato,
                    'inquilino_nome': inquilino.nome,
                    'inquilino_cpf': inquilino.cpf_cnpj or 'Não informado',
                    'inquilino_telefone': inquilino.telefone or 'Não informado',
                    'inquilino_email': inquilino.email or 'Não informado',
                    'inquilino_endereco': inquilino.endereco or 'Não informado',
                    'imovel_endereco': getattr(contrato.imovel, 'endereco_completo', 'N/A') if contrato else 'N/A',
                    'valor_aluguel': str(contrato.valor_aluguel) if contrato else '0,00',
                    'data_vencimento': timezone.now().date() + timedelta(days=30),
                    'dias_para_vencer': 30,
                    'valor_devido': contrato.valor_aluguel if contrato else 0,
                    'data_atual': timezone.now().date(),
                }
                
                # Renderizar template
                assunto = template.renderizar_assunto(contexto)
                corpo = template.renderizar_corpo(contexto)
                
                # Determinar destinatário baseado no canal
                if canal == 'EMAIL':
                    if not inquilino.email:
                        continue
                    destinatario = inquilino.email
                elif canal in ['SMS', 'WHATSAPP']:
                    if not inquilino.telefone:
                        continue
                    destinatario = inquilino.telefone
                else:
                    continue
                
                # Criar notificação
                notificacao = Notificacao.objects.create(
                    template=template,
                    inquilino=inquilino,
                    contrato=contrato,
                    canal=canal,
                    destinatario=destinatario,
                    assunto=assunto,
                    corpo=corpo,
                    status='PENDENTE'
                )
                
                notificacoes_criadas += 1
                
                # Tentar enviar
                if enviar_notificacao_individual(notificacao):
                    notificacoes_enviadas += 1
            
            if notificacoes_enviadas > 0:
                messages.success(
                    request, 
                    f'{notificacoes_enviadas} de {notificacoes_criadas} notificações enviadas com sucesso!'
                )
            else:
                messages.warning(
                    request, 
                    'Nenhuma notificação pôde ser enviada. Verifique os dados de contato dos destinatários.'
                )
            
            return redirect('notificacoes:enviar')
            
        except Exception as e:
            messages.error(request, f'Erro ao enviar notificações: {str(e)}')
            return redirect('notificacoes:enviar_avancado')
    
    # GET - Exibir formulário
    templates = TemplateNotificacao.objects.filter(ativo=True).select_related('categoria')
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'notificacoes/enviar_avancado.html', context)


@login_required
def envio_notificacoes_removido(request):
    return redirect('notificacoes:whatsapp_dashboard')


@login_required
def historico_notificacoes(request):
    """Histórico completo de notificações"""
    tenant = getattr(request, 'tenant', None)
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template', 'contrato'
    ).order_by('-created_at')

    if tenant:
        notificacoes = notificacoes.filter(inquilino__tenant=tenant)
    
    # Filtros
    status = request.GET.get('status')
    canal = request.GET.get('canal')
    template_id = request.GET.get('template')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    busca = request.GET.get('busca')
    
    if status:
        notificacoes = notificacoes.filter(status=status)
    if canal:
        notificacoes = notificacoes.filter(canal=canal)
    if template_id:
        notificacoes = notificacoes.filter(template_id=template_id)
    if data_inicio:
        notificacoes = notificacoes.filter(created_at__date__gte=data_inicio)
    if data_fim:
        notificacoes = notificacoes.filter(created_at__date__lte=data_fim)
    if busca:
        notificacoes = notificacoes.filter(
            Q(assunto__icontains=busca) |
            Q(inquilino__nome__icontains=busca) |
            Q(destinatario__icontains=busca)
        )
    
    # Estatísticas
    stats = {
        'total': notificacoes.count(),
        'entregues': notificacoes.filter(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA']).count(),
        'pendentes': notificacoes.filter(status='PENDENTE').count(),
        'erros': notificacoes.filter(status__in=['ERRO', 'REJEITADA']).count(),
    }
    
    paginator = Paginator(notificacoes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for n in page_obj:
        n.erro_resumo = _resumo_erro_notificacao(n)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'templates': TemplateNotificacao.objects.filter(ativo=True).exclude(
            Q(nome__icontains='banca') | Q(nome__icontains='feira')
        ),
        'status_choices': Notificacao.STATUS_CHOICES,
        'canal_choices': Notificacao.CANAL_CHOICES,
    }
    
    return render(request, 'notificacoes/historico.html', context)


@login_required
def detalhes_notificacao(request, notificacao_id):
    """Detalhes de uma notificação específica"""
    notificacao = get_object_or_404(
        Notificacao.objects.select_related('inquilino', 'template', 'contrato'),
        id=notificacao_id
    )
    
    return JsonResponse({
        'id': notificacao.id,
        'assunto': notificacao.assunto,
        'corpo': notificacao.corpo,
        'inquilino': notificacao.inquilino.nome,
        'destinatario': notificacao.destinatario,
        'canal': notificacao.get_canal_display(),
        'status': notificacao.get_status_display(),
        'template': notificacao.template.nome if notificacao.template else 'N/A',
        'data_criacao': notificacao.created_at.strftime('%d/%m/%Y %H:%M'),
        'data_envio': notificacao.data_envio.strftime('%d/%m/%Y %H:%M') if notificacao.data_envio else 'N/A',
        'tentativas': notificacao.tentativas_realizadas,
        'log_tentativas': notificacao.log_tentativas,
        'erro_envio': notificacao.erro_envio,
        'erro_resumo': _resumo_erro_notificacao(notificacao),
    })


# APIs e funções auxiliares
@login_required
def api_templates(request):
    """API para listar templates ativos"""
    templates = TemplateNotificacao.objects.filter(ativo=True).exclude(
        Q(nome__icontains='banca') | Q(nome__icontains='feira')
    ).values(
        'id', 'nome', 'tipo', 'categoria__nome'
    )
    return JsonResponse(list(templates), safe=False)


@login_required
def api_inquilinos(request):
    """API para listar inquilinos"""
    tenant = getattr(request, 'tenant', None)
    if tenant:
        inquilinos = Inquilino.objects.filter(tenant=tenant, ativo=True).values('id', 'nome', 'email', 'telefone')
    else:
        inquilinos = Inquilino.objects.none().values('id', 'nome', 'email', 'telefone')
    return JsonResponse(list(inquilinos), safe=False)


@login_required
def filtrar_destinatarios(request):
    """Filtrar destinatários com critérios avançados"""
    tenant = getattr(request, 'tenant', None)
    if tenant:
        inquilinos = Inquilino.objects.filter(tenant=tenant, ativo=True)
    else:
        inquilinos = Inquilino.objects.none()
    
    # Aplicar filtros
    tipo_contrato = request.GET.get('tipo_contrato')
    status_contrato = request.GET.get('status_contrato')
    cidade = request.GET.get('cidade')
    renda_min = request.GET.get('renda_min')
    renda_max = request.GET.get('renda_max')
    dia_vencimento = request.GET.get('dia_vencimento')
    valor_aluguel_min = request.GET.get('valor_aluguel_min')
    valor_aluguel_max = request.GET.get('valor_aluguel_max')
    busca = request.GET.get('busca')
    
    if tipo_contrato == 'com_contrato':
        inquilinos = inquilinos.filter(contrato__isnull=False)
    elif tipo_contrato == 'sem_contrato':
        inquilinos = inquilinos.filter(contrato__isnull=True)
    
    if status_contrato:
        inquilinos = inquilinos.filter(contrato__status=status_contrato)
    
    if cidade:
        inquilinos = inquilinos.filter(cidade__icontains=cidade)
    
    if renda_min:
        inquilinos = inquilinos.filter(renda_comprovada__gte=renda_min)
    
    if renda_max:
        inquilinos = inquilinos.filter(renda_comprovada__lte=renda_max)
    
    if dia_vencimento:
        inquilinos = inquilinos.filter(contrato__dia_vencimento=dia_vencimento)
    
    if valor_aluguel_min:
        inquilinos = inquilinos.filter(contrato__valor_aluguel__gte=valor_aluguel_min)
    
    if valor_aluguel_max:
        inquilinos = inquilinos.filter(contrato__valor_aluguel__lte=valor_aluguel_max)
    
    if busca:
        inquilinos = inquilinos.filter(
            Q(nome__icontains=busca) |
            Q(email__icontains=busca) |
            Q(telefone__icontains=busca)
        )
    
    # Preparar dados para resposta
    dados = []
    for inquilino in inquilinos.distinct():
        contrato = Contrato.objects.filter(
            inquilino=inquilino, status='ATIVO'
        ).first()
        
        dados.append({
            'id': inquilino.id,
            'nome': inquilino.nome,
            'email': inquilino.email,
            'telefone': inquilino.telefone,
            'cidade': inquilino.cidade,
            'tem_contrato': bool(contrato),
            'valor_aluguel': float(contrato.valor_aluguel) if contrato else None,
            'dia_vencimento': contrato.dia_vencimento if contrato else None,
        })
    
    return JsonResponse({
        'inquilinos': dados,
        'total': len(dados),
        'filtros_aplicados': {
            'tipo': tipo_contrato or 'todos',
            'status': status_contrato or 'todos',
            'cidade': cidade or '',
            'renda_min': renda_min or '',
            'renda_max': renda_max or '',
            'vencimento': dia_vencimento or '',
            'valor_min': valor_aluguel_min or '',
            'valor_max': valor_aluguel_max or '',
            'busca': busca or ''
        }
    })


@login_required
def obter_cidades(request):
    """Obter lista de cidades dos inquilinos"""
    tenant = getattr(request, 'tenant', None)
    if tenant:
        cidades = Inquilino.objects.filter(tenant=tenant, ativo=True).exclude(
            cidade__isnull=True
        ).exclude(
            cidade__exact=''
        ).values_list('cidade', flat=True).distinct().order_by('cidade')
    else:
        cidades = Inquilino.objects.none().values_list('cidade', flat=True)
    
    return JsonResponse({'cidades': list(cidades)})


@login_required
def estatisticas_destinatarios(request):
    """Estatísticas dos destinatários"""
    tenant = getattr(request, 'tenant', None)
    base = Inquilino.objects.filter(tenant=tenant, ativo=True) if tenant else Inquilino.objects.none()
    total_inquilinos = base.count()
    com_email = base.exclude(email__isnull=True).exclude(email__exact='').count()
    com_telefone = base.exclude(telefone__isnull=True).exclude(telefone__exact='').count()
    com_contrato = base.filter(contrato__status='ATIVO').count()
    
    return JsonResponse({
        'total_inquilinos': total_inquilinos,
        'com_email': com_email,
        'com_telefone': com_telefone,
        'com_contrato': com_contrato,
        'sem_contrato': total_inquilinos - com_contrato,
    })


# Funções de agendamento
@login_required
def agendar_notificacao(request):
    """Agendar notificação para envio futuro"""
    if request.method == 'POST':
        # Implementar lógica de agendamento
        pass
    
    tenant = getattr(request, 'tenant', None)
    templates = TemplateNotificacao.objects.filter(ativo=True).exclude(
        Q(nome__icontains='banca') | Q(nome__icontains='feira')
    )
    inquilinos = Inquilino.objects.filter(tenant=tenant, ativo=True) if tenant else Inquilino.objects.none()
    
    context = {
        'templates': templates,
        'inquilinos': inquilinos,
    }
    
    return render(request, 'notificacoes/agendar.html', context)


@login_required
def listar_agendamentos(request):
    """Listar notificações agendadas"""
    agendamentos = NotificacaoAgendada.objects.select_related('template').order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    recorrencia = request.GET.get('recorrencia')
    busca = request.GET.get('busca')
    
    if status:
        agendamentos = agendamentos.filter(status=status)
    if recorrencia:
        agendamentos = agendamentos.filter(recorrencia=recorrencia)
    if busca:
        agendamentos = agendamentos.filter(
            Q(nome_campanha__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    paginator = Paginator(agendamentos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': NotificacaoAgendada.STATUS_CHOICES,
        'recorrencia_choices': NotificacaoAgendada.RECORRENCIA_CHOICES,
    }
    
    return render(request, 'notificacoes/agendamentos.html', context)


@login_required
def criar_agendamento(request):
    """Criar novo agendamento"""
    if request.method == 'POST':
        # Implementar criação de agendamento
        pass
    
    return render(request, 'notificacoes/criar_agendamento.html')


@login_required
def cancelar_agendamento(request, agendamento_id):
    """Cancelar agendamento"""
    agendamento = get_object_or_404(NotificacaoAgendada, id=agendamento_id)
    agendamento.status = 'CANCELADA'
    agendamento.save()
    
    messages.success(request, 'Agendamento cancelado com sucesso!')
    return redirect('notificacoes:listar_agendamentos')


# Funções de gerenciamento
@login_required
def reenviar_notificacao(request, notificacao_id):
    """Reenviar uma notificação específica"""
    if request.method == 'POST':
        try:
            notificacao = get_object_or_404(Notificacao, id=notificacao_id)
            
            if enviar_notificacao_individual(notificacao):
                # Se for requisição AJAX, retorna JSON
                if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Notificação reenviada com sucesso!'
                    })
                
                messages.success(request, 'Notificação reenviada com sucesso!')
            else:
                if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Erro ao reenviar notificação'
                    })
                
                messages.error(request, 'Erro ao reenviar notificação')
                
        except Exception as e:
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao reenviar notificação: {str(e)}'
                })
            
            messages.error(request, f'Erro ao reenviar notificação: {str(e)}')
    
    return redirect('notificacoes:enviar')


@login_required
def excluir_notificacao(request, notificacao_id):
    """Excluir uma notificação específica"""
    if request.method == 'POST':
        try:
            notificacao = get_object_or_404(Notificacao, id=notificacao_id)
            notificacao.delete()
            
            # Se for requisição AJAX, retorna JSON
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Notificação excluída com sucesso!'
                })
            
            # Se for formulário normal, redireciona
            messages.success(request, 'Notificação excluída com sucesso!')
            return redirect('notificacoes:enviar')
            
        except Exception as e:
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao excluir notificação: {str(e)}'
                })
            
            messages.error(request, f'Erro ao excluir notificação: {str(e)}')
            return redirect('notificacoes:enviar')
    
    return redirect('notificacoes:enviar')


@login_required
def reenviar_lote(request):
    """Reenviar notificações em lote"""
    if request.method == 'POST':
        try:
            # Verifica se é requisição AJAX
            is_ajax = request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if is_ajax:
                import json
                data = json.loads(request.body)
                notificacoes_ids = data.get('ids', [])
            else:
                notificacoes_ids = request.POST.getlist('notificacoes')
            
            notificacoes = Notificacao.objects.filter(id__in=notificacoes_ids)
            
            reenviadas = 0
            for notificacao in notificacoes:
                if enviar_notificacao_individual(notificacao):
                    reenviadas += 1
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'reenviadas': reenviadas,
                    'message': f'{reenviadas} notificações reenviadas com sucesso!'
                })
            
            messages.success(request, f'{reenviadas} notificações reenviadas com sucesso!')
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao reenviar notificações: {str(e)}'
                })
            
            messages.error(request, f'Erro ao reenviar notificações: {str(e)}')
    
    return redirect('notificacoes:enviar')


@login_required
def excluir_lote(request):
    """Excluir notificações em lote"""
    if request.method == 'POST':
        try:
            # Verifica se é requisição AJAX
            is_ajax = request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if is_ajax:
                import json
                data = json.loads(request.body)
                notificacoes_ids = data.get('ids', [])
            else:
                notificacoes_ids = request.POST.getlist('notificacoes')
            
            count = Notificacao.objects.filter(id__in=notificacoes_ids).delete()[0]
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'excluidas': count,
                    'message': f'{count} notificações excluídas com sucesso!'
                })
            
            messages.success(request, f'{count} notificações excluídas com sucesso!')
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao excluir notificações: {str(e)}'
                })
            
            messages.error(request, f'Erro ao excluir notificações: {str(e)}')
    
    return redirect('notificacoes:enviar')


@login_required
def limpar_historico(request):
    """Limpar histórico de notificações antigas"""
    if request.method == 'POST':
        try:
            dias = int(request.POST.get('dias', 30))
            data_limite = timezone.now() - timedelta(days=dias)
            
            # Buscar notificações para exclusão
            notificacoes_para_excluir = Notificacao.objects.filter(
                created_at__lt=data_limite,
                status__in=['ENVIADA', 'ENTREGUE', 'ERRO', 'REJEITADA']
            )
            
            count = notificacoes_para_excluir.count()
            
            if count > 0:
                # Excluir em lotes para evitar problemas de memória
                notificacoes_para_excluir.delete()
                messages.success(request, f'{count} notificações antigas removidas com sucesso!')
            else:
                messages.info(request, 'Nenhuma notificação encontrada para remoção.')
                
        except ValueError:
            messages.error(request, 'Número de dias inválido.')
        except Exception as e:
            messages.error(request, f'Erro ao limpar histórico: {str(e)}')
    
    return redirect('notificacoes:enviar')


@login_required
def exportar_historico_csv(request):
    """Exportar histórico para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="historico_notificacoes.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Data/Hora', 'Inquilino', 'Destinatário', 'Canal', 'Assunto', 
        'Status', 'Template', 'Data Envio'
    ])
    
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template'
    ).order_by('-created_at')
    
    for notificacao in notificacoes:
        writer.writerow([
            notificacao.created_at.strftime('%d/%m/%Y %H:%M'),
            notificacao.inquilino.nome,
            notificacao.destinatario,
            notificacao.get_canal_display(),
            notificacao.assunto,
            notificacao.get_status_display(),
            notificacao.template.nome if notificacao.template else 'N/A',
            notificacao.data_envio.strftime('%d/%m/%Y %H:%M') if notificacao.data_envio else 'N/A',
        ])
    
    return response


# Funcionalidades de Estatísticas de Entrega e Abertura de Emails

@login_required
def dashboard_estatisticas(request):
    """Dashboard com métricas de notificações"""
    # Período padrão: últimos 30 dias
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if not data_inicio:
        data_inicio = timezone.now().date() - timedelta(days=30)
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    
    if not data_fim:
        data_fim = timezone.now().date()
    else:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Filtrar notificações do período
    notificacoes = Notificacao.objects.filter(
        created_at__date__gte=data_inicio,
        created_at__date__lte=data_fim
    )
    
    # Métricas gerais
    total_enviadas = notificacoes.count()
    total_entregues = notificacoes.filter(status__in=['ENTREGUE', 'ABERTA', 'CLICADA']).count()
    total_abertas = notificacoes.filter(status__in=['ABERTA', 'CLICADA']).count()
    total_clicadas = notificacoes.filter(status='CLICADA').count()
    total_erros = notificacoes.filter(status__in=['ERRO', 'REJEITADA']).count()
    
    # Calcular taxas
    taxa_entrega = (total_entregues / total_enviadas * 100) if total_enviadas > 0 else 0
    taxa_abertura = (total_abertas / total_entregues * 100) if total_entregues > 0 else 0
    taxa_clique = (total_clicadas / total_abertas * 100) if total_abertas > 0 else 0
    taxa_erro = (total_erros / total_enviadas * 100) if total_enviadas > 0 else 0
    
    # Estatísticas por canal
    stats_por_canal = notificacoes.values('canal').annotate(
        total=Count('id'),
        entregues=Count('id', filter=Q(status__in=['ENTREGUE', 'ABERTA', 'CLICADA'])),
        abertas=Count('id', filter=Q(status__in=['ABERTA', 'CLICADA'])),
        clicadas=Count('id', filter=Q(status='CLICADA')),
        erros=Count('id', filter=Q(status__in=['ERRO', 'REJEITADA']))
    )
    
    # Estatísticas por template
    stats_por_template = notificacoes.select_related('template').values(
        'template__nome', 'template__id'
    ).annotate(
        total=Count('id'),
        entregues=Count('id', filter=Q(status__in=['ENTREGUE', 'ABERTA', 'CLICADA'])),
        abertas=Count('id', filter=Q(status__in=['ABERTA', 'CLICADA'])),
        clicadas=Count('id', filter=Q(status='CLICADA'))
    ).order_by('-total')[:10]
    
    # Dados para gráficos (últimos 7 dias)
    dados_grafico = []
    for i in range(7):
        data = timezone.now().date() - timedelta(days=i)
        notif_dia = notificacoes.filter(created_at__date=data)
        dados_grafico.append({
            'data': data.strftime('%d/%m'),
            'enviadas': notif_dia.count(),
            'entregues': notif_dia.filter(status__in=['ENTREGUE', 'ABERTA', 'CLICADA']).count(),
            'abertas': notif_dia.filter(status__in=['ABERTA', 'CLICADA']).count(),
        })
    dados_grafico.reverse()
    
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'metricas': {
            'total_enviadas': total_enviadas,
            'total_entregues': total_entregues,
            'total_abertas': total_abertas,
            'total_clicadas': total_clicadas,
            'total_erros': total_erros,
            'taxa_entrega': round(taxa_entrega, 2),
            'taxa_abertura': round(taxa_abertura, 2),
            'taxa_clique': round(taxa_clique, 2),
            'taxa_erro': round(taxa_erro, 2),
        },
        'stats_por_canal': stats_por_canal,
        'stats_por_template': stats_por_template,
        'dados_grafico': dados_grafico,
    }
    
    return render(request, 'notificacoes/dashboard_estatisticas.html', context)


@login_required
def rastrear_abertura(request, notificacao_id):
    """Endpoint para rastrear abertura de email"""
    try:
        notificacao = get_object_or_404(Notificacao, id=notificacao_id)
        
        # Atualizar status se ainda não foi aberta
        if notificacao.status in ['ENVIADA', 'ENTREGUE']:
            notificacao.status = 'ABERTA'
            notificacao.data_abertura = timezone.now()
            notificacao.save()
            
            # Criar ou atualizar estatística
            estatistica, created = EstatisticaNotificacao.objects.get_or_create(
                notificacao=notificacao,
                defaults={
                    'data_abertura': timezone.now(),
                    'ip_abertura': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500]
                }
            )
            
            if not created and not estatistica.data_abertura:
                estatistica.data_abertura = timezone.now()
                estatistica.ip_abertura = request.META.get('REMOTE_ADDR')
                estatistica.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                estatistica.save()
        
        # Retornar pixel transparente 1x1
        response = HttpResponse(content_type='image/png')
        # Pixel PNG transparente 1x1 em base64
        pixel_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        response.write(pixel_data)
        return response
        
    except Exception:
        # Em caso de erro, retornar pixel mesmo assim
        response = HttpResponse(content_type='image/png')
        pixel_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        response.write(pixel_data)
        return response


@login_required
def rastrear_clique(request, notificacao_id):
    """Endpoint para rastrear cliques em links do email"""
    try:
        notificacao = get_object_or_404(Notificacao, id=notificacao_id)
        url_destino = request.GET.get('url', '/')
        
        # Atualizar status para clicada
        if notificacao.status in ['ENVIADA', 'ENTREGUE', 'ABERTA']:
            notificacao.status = 'CLICADA'
            notificacao.data_clique = timezone.now()
            notificacao.save()
            
            # Atualizar estatística
            estatistica, created = EstatisticaNotificacao.objects.get_or_create(
                notificacao=notificacao,
                defaults={
                    'data_clique': timezone.now(),
                    'ip_clique': request.META.get('REMOTE_ADDR'),
                    'links_clicados': [url_destino]
                }
            )
            
            if not created:
                estatistica.data_clique = timezone.now()
                estatistica.ip_clique = request.META.get('REMOTE_ADDR')
                if not estatistica.links_clicados:
                    estatistica.links_clicados = []
                if url_destino not in estatistica.links_clicados:
                    estatistica.links_clicados.append(url_destino)
                estatistica.save()
        
        # Redirecionar para URL de destino
        return redirect(url_destino)
        
    except Exception:
        # Em caso de erro, redirecionar para home
        return redirect('/')


@login_required
def estatisticas_detalhadas(request):
    """View para estatísticas detalhadas com filtros avançados"""
    # Filtros
    template_id = request.GET.get('template')
    canal = request.GET.get('canal')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Query base
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template', 'contrato'
    ).prefetch_related('estatisticanotificacao_set')
    
    # Aplicar filtros
    if template_id:
        notificacoes = notificacoes.filter(template_id=template_id)
    if canal:
        notificacoes = notificacoes.filter(canal=canal)
    if status:
        notificacoes = notificacoes.filter(status=status)
    if data_inicio:
        notificacoes = notificacoes.filter(created_at__date__gte=data_inicio)
    if data_fim:
        notificacoes = notificacoes.filter(created_at__date__lte=data_fim)
    
    # Estatísticas por inquilino
    stats_inquilinos = notificacoes.values(
        'inquilino__nome', 'inquilino__id'
    ).annotate(
        total_recebidas=Count('id'),
        total_abertas=Count('id', filter=Q(status__in=['ABERTA', 'CLICADA'])),
        total_clicadas=Count('id', filter=Q(status='CLICADA'))
    ).order_by('-total_recebidas')[:20]
    
    # Horários de maior engajamento
    stats_horarios = notificacoes.filter(
        status__in=['ABERTA', 'CLICADA']
    ).extra(
        select={'hora': 'EXTRACT(hour FROM data_abertura)'}
    ).values('hora').annotate(
        total=Count('id')
    ).order_by('hora')
    
    # Dias da semana com maior engajamento
    stats_dias_semana = notificacoes.filter(
        status__in=['ABERTA', 'CLICADA']
    ).extra(
        select={'dia_semana': 'EXTRACT(dow FROM data_abertura)'}
    ).values('dia_semana').annotate(
        total=Count('id')
    ).order_by('dia_semana')
    
    # Dispositivos mais utilizados (baseado no user agent)
    stats_dispositivos = EstatisticaNotificacao.objects.filter(
        notificacao__in=notificacoes,
        user_agent__isnull=False
    ).extra(
        select={
            'dispositivo': "CASE "
                          "WHEN user_agent LIKE '%Mobile%' THEN 'Mobile' "
                          "WHEN user_agent LIKE '%Tablet%' THEN 'Tablet' "
                          "ELSE 'Desktop' END"
        }
    ).values('dispositivo').annotate(
        total=Count('id')
    ).order_by('-total')
    
    paginator = Paginator(notificacoes.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'stats_inquilinos': stats_inquilinos,
        'stats_horarios': stats_horarios,
        'stats_dias_semana': stats_dias_semana,
        'stats_dispositivos': stats_dispositivos,
        'templates': TemplateNotificacao.objects.filter(ativo=True),
        'canal_choices': Notificacao.CANAL_CHOICES,
        'status_choices': Notificacao.STATUS_CHOICES,
    }
    
    return render(request, 'notificacoes/estatisticas_detalhadas.html', context)


@login_required
def relatorio_performance_templates(request):
    """Relatório de performance dos templates"""
    periodo = request.GET.get('periodo', '30')  # dias
    data_limite = timezone.now() - timedelta(days=int(periodo))
    
    # Estatísticas por template
    templates_stats = TemplateNotificacao.objects.filter(
        ativo=True
    ).annotate(
        total_enviadas=Count(
            'notificacao',
            filter=Q(notificacao__created_at__gte=data_limite)
        ),
        total_entregues=Count(
            'notificacao',
            filter=Q(
                notificacao__created_at__gte=data_limite,
                notificacao__status__in=['ENTREGUE', 'ABERTA', 'CLICADA']
            )
        ),
        total_abertas=Count(
            'notificacao',
            filter=Q(
                notificacao__created_at__gte=data_limite,
                notificacao__status__in=['ABERTA', 'CLICADA']
            )
        ),
        total_clicadas=Count(
            'notificacao',
            filter=Q(
                notificacao__created_at__gte=data_limite,
                notificacao__status='CLICADA'
            )
        )
    ).filter(total_enviadas__gt=0)
    
    # Calcular taxas para cada template
    for template in templates_stats:
        template.taxa_entrega = (
            template.total_entregues / template.total_enviadas * 100
        ) if template.total_enviadas > 0 else 0
        
        template.taxa_abertura = (
            template.total_abertas / template.total_entregues * 100
        ) if template.total_entregues > 0 else 0
        
        template.taxa_clique = (
            template.total_clicadas / template.total_abertas * 100
        ) if template.total_abertas > 0 else 0
    
    # Ordenar por performance (taxa de abertura)
    templates_stats = sorted(
        templates_stats, 
        key=lambda x: x.taxa_abertura, 
        reverse=True
    )
    
    context = {
        'templates_stats': templates_stats,
        'periodo': periodo,
        'data_limite': data_limite,
    }
    
    return render(request, 'notificacoes/relatorio_performance_templates.html', context)


@login_required
def exportar_estatisticas_csv(request):
    """Exportar estatísticas detalhadas para CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estatisticas_notificacoes.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Template', 'Inquilino', 'Canal', 'Status', 'Data Envio', 
        'Data Abertura', 'Data Clique', 'IP Abertura', 'Dispositivo'
    ])
    
    # Filtros (mesmos da view de estatísticas detalhadas)
    template_id = request.GET.get('template')
    canal = request.GET.get('canal')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template'
    ).prefetch_related('estatisticanotificacao_set')
    
    if template_id:
        notificacoes = notificacoes.filter(template_id=template_id)
    if canal:
        notificacoes = notificacoes.filter(canal=canal)
    if status:
        notificacoes = notificacoes.filter(status=status)
    if data_inicio:
        notificacoes = notificacoes.filter(created_at__date__gte=data_inicio)
    if data_fim:
        notificacoes = notificacoes.filter(created_at__date__lte=data_fim)
    
    for notificacao in notificacoes.order_by('-created_at'):
        estatistica = notificacao.estatisticanotificacao_set.first()
        
        # Determinar dispositivo baseado no user agent
        dispositivo = 'N/A'
        if estatistica and estatistica.user_agent:
            ua = estatistica.user_agent.lower()
            if 'mobile' in ua:
                dispositivo = 'Mobile'
            elif 'tablet' in ua:
                dispositivo = 'Tablet'
            else:
                dispositivo = 'Desktop'
        
        writer.writerow([
            notificacao.template.nome if notificacao.template else 'N/A',
            notificacao.inquilino.nome,
            notificacao.get_canal_display(),
            notificacao.get_status_display(),
            notificacao.data_envio.strftime('%d/%m/%Y %H:%M') if notificacao.data_envio else 'N/A',
            estatistica.data_abertura.strftime('%d/%m/%Y %H:%M') if estatistica and estatistica.data_abertura else 'N/A',
            estatistica.data_clique.strftime('%d/%m/%Y %H:%M') if estatistica and estatistica.data_clique else 'N/A',
            estatistica.ip_abertura if estatistica else 'N/A',
            dispositivo,
        ])
    
    return response


# ===== VIEWS PARA GERENCIAR TEMPLATES =====

@login_required
def listar_templates(request):
    """Lista todos os templates de notificação com filtros avançados"""
    search = request.GET.get('search', '')
    categoria_id = request.GET.get('categoria', '')
    formato = request.GET.get('formato', '')
    status = request.GET.get('status', '')
    ordenar = request.GET.get('ordenar', '-created_at')
    uso = request.GET.get('uso', '')
    
    templates = TemplateNotificacao.objects.select_related('categoria')
    
    # Filtro de busca por texto
    if search:
        templates = templates.filter(
            Q(nome__icontains=search) |
            Q(assunto_template__icontains=search) |
            Q(corpo_template__icontains=search)
        )
    
    # Filtro por categoria
    if categoria_id:
        templates = templates.filter(categoria_id=categoria_id)
    
    # Filtro por formato
    if formato:
        templates = templates.filter(formato=formato)
    
    # Filtro por status
    if status == 'ativo':
        templates = templates.filter(ativo=True)
    elif status == 'inativo':
        templates = templates.filter(ativo=False)
    
    # Filtro por uso (baseado em estatísticas)
    if uso:
        # Anotar templates com contagem de uso
        templates = templates.annotate(
            total_usos=Count('notificacao')
        )
        
        if uso == 'mais_usados':
            templates = templates.filter(total_usos__gt=0).order_by('-total_usos')
        elif uso == 'menos_usados':
            templates = templates.filter(total_usos__gt=0).order_by('total_usos')
        elif uso == 'nunca_usados':
            templates = templates.filter(total_usos=0)
    
    # Ordenação
    if ordenar and not uso:  # Se não há filtro de uso, aplicar ordenação normal
        if ordenar in ['-created_at', 'created_at', 'nome', '-nome']:
            templates = templates.order_by(ordenar)
        else:
            templates = templates.order_by('-created_at')
    elif not uso:
        templates = templates.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(templates, 12)  # Aumentado para 12 por página para o layout de cards
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas de uso para todos os templates da página
    templates_stats = {}
    for template in page_obj:
        stats = Notificacao.objects.filter(template=template).aggregate(
            total_enviadas=Count('id'),
            total_entregues=Count('id', filter=Q(status='ENTREGUE')),
            total_lidas=Count('id', filter=Q(status='LIDA'))
        )
        templates_stats[template.id] = stats
    
    context = {
        'page_obj': page_obj,
        'templates_stats': templates_stats,
        'categorias': CategoriaTemplate.objects.all(),
        'search': search,
        'categoria_selecionada': categoria_id,
        'formato_selecionado': formato,
        'formatos': TemplateNotificacao.FORMATO_CHOICES,
    }
    
    return render(request, 'notificacoes/templates/listar.html', context)


@login_required
def criar_template(request):
    """Cria um novo template de notificação"""
    if request.method == 'POST':
        try:
            # Validar dados obrigatórios
            nome = request.POST.get('nome', '').strip()
            categoria_id = request.POST.get('categoria')
            formato = request.POST.get('formato')
            assunto = request.POST.get('assunto', '').strip()
            corpo = request.POST.get('corpo', '').strip()
            
            if not all([nome, categoria_id, formato, corpo]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                return redirect('notificacoes:criar_template')
            
            # Verificar se já existe template com mesmo nome
            if TemplateNotificacao.objects.filter(nome=nome).exists():
                messages.error(request, 'Já existe um template com este nome.')
                return redirect('notificacoes:criar_template')
            
            # Criar template
            template = TemplateNotificacao.objects.create(
                nome=nome,
                categoria_id=categoria_id,
                formato=formato,
                assunto_template=assunto,
                corpo_template=corpo,
                ativo=request.POST.get('ativo') == 'on'
            )
            
            messages.success(request, f'Template "{nome}" criado com sucesso!')
            return redirect('notificacoes:editar_template', template_id=template.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar template: {str(e)}')
    
    context = {
        'categorias': CategoriaTemplate.objects.all(),
        'formatos': TemplateNotificacao.FORMATO_CHOICES,
        'variaveis_disponiveis': [
            '{{ inquilino.nome }}',
            '{{ inquilino.email }}',
            '{{ inquilino.telefone }}',
            '{{ contrato.numero }}',
            '{{ contrato.data_inicio }}',
            '{{ contrato.data_fim }}',
            '{{ contrato.valor_aluguel }}',
            '{{ data_vencimento }}',
            '{{ dias_para_vencer }}',
            '{{ valor_devido }}',
            '{{ data_atual }}',
        ]
    }
    
    return render(request, 'notificacoes/templates/criar.html', context)


@login_required
def editar_template(request, template_id):
    """Edita um template existente"""
    template = get_object_or_404(TemplateNotificacao, id=template_id)
    
    if request.method == 'POST':
        try:
            # Validar dados obrigatórios
            nome = request.POST.get('nome', '').strip()
            categoria_id = request.POST.get('categoria')
            formato = request.POST.get('formato')
            assunto = request.POST.get('assunto', '').strip()
            corpo = request.POST.get('corpo', '').strip()
            
            if not all([nome, categoria_id, formato, corpo]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                return render(request, 'notificacoes/templates/editar.html', {'template': template})
            
            # Verificar se já existe outro template com mesmo nome
            if TemplateNotificacao.objects.filter(nome=nome).exclude(id=template_id).exists():
                messages.error(request, 'Já existe outro template com este nome.')
                return render(request, 'notificacoes/templates/editar.html', {'template': template})
            
            # Atualizar template
            template.nome = nome
            template.categoria_id = categoria_id
            template.formato = formato
            template.assunto_template = assunto
            template.corpo_template = corpo
            template.ativo = request.POST.get('ativo') == 'on'
            template.save()
            
            messages.success(request, f'Template "{nome}" atualizado com sucesso!')
            return redirect('notificacoes:listar_templates')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar template: {str(e)}')
    
    # Estatísticas de uso do template
    stats = Notificacao.objects.filter(template=template).aggregate(
        total_enviadas=Count('id'),
        total_entregues=Count('id', filter=Q(status='ENTREGUE')),
        total_lidas=Count('id', filter=Q(status='LIDA')),
        total_falhas=Count('id', filter=Q(status='FALHA'))
    )
    
    context = {
        'template': template,
        'categorias': CategoriaTemplate.objects.all(),
        'formatos': TemplateNotificacao.FORMATO_CHOICES,
        'stats': stats,
        'variaveis_disponiveis': [
            '{{ inquilino.nome }}',
            '{{ inquilino.email }}',
            '{{ inquilino.telefone }}',
            '{{ contrato.numero }}',
            '{{ contrato.data_inicio }}',
            '{{ contrato.data_fim }}',
            '{{ contrato.valor_aluguel }}',
            '{{ data_vencimento }}',
            '{{ dias_para_vencer }}',
            '{{ valor_devido }}',
            '{{ data_atual }}',
        ]
    }
    
    return render(request, 'notificacoes/templates/editar.html', context)


@login_required
def excluir_template(request, template_id):
    """Exclui um template"""
    template = get_object_or_404(TemplateNotificacao, id=template_id)
    
    if request.method == 'POST':
        try:
            # Verificar se o template está sendo usado
            notificacoes_count = Notificacao.objects.filter(template=template).count()
            agendamentos_count = NotificacaoAgendada.objects.filter(template=template).count()
            
            if notificacoes_count > 0 or agendamentos_count > 0:
                messages.error(
                    request, 
                    f'Não é possível excluir o template "{template.nome}" pois ele possui '
                    f'{notificacoes_count} notificações e {agendamentos_count} agendamentos associados.'
                )
                return redirect('notificacoes:listar_templates')
            
            nome = template.nome
            template.delete()
            messages.success(request, f'Template "{nome}" excluído com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir template: {str(e)}')
    
    return redirect('notificacoes:listar_templates')


@login_required
def duplicar_template(request, template_id):
    """Duplica um template existente"""
    template_original = get_object_or_404(TemplateNotificacao, id=template_id)
    
    try:
        # Criar nome único para o template duplicado
        nome_base = f"{template_original.nome} - Cópia"
        nome_final = nome_base
        contador = 1
        
        while TemplateNotificacao.objects.filter(nome=nome_final).exists():
            nome_final = f"{nome_base} ({contador})"
            contador += 1
        
        # Criar template duplicado
        template_duplicado = TemplateNotificacao.objects.create(
            nome=nome_final,
            categoria=template_original.categoria,
            formato=template_original.formato,
            assunto_template=template_original.assunto_template,
            corpo_template=template_original.corpo_template,
            ativo=False  # Criar como inativo por segurança
        )
        
        messages.success(
            request, 
            f'Template duplicado com sucesso! '
            f'Novo template: "{nome_final}"'
        )
        
        return redirect('notificacoes:editar_template', template_id=template_duplicado.id)
        
    except Exception as e:
        messages.error(request, f'Erro ao duplicar template: {str(e)}')
        return redirect('notificacoes:listar_templates')


@login_required
def testar_template(request, template_id):
    """Testa um template com dados de exemplo"""
    template = get_object_or_404(TemplateNotificacao, id=template_id)
    
    if request.method == 'POST':
        try:
            # Obter inquilino para teste
            inquilino_id = request.POST.get('inquilino_id')
            if not inquilino_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Selecione um inquilino para o teste'
                })
            
            inquilino = get_object_or_404(Inquilino, id=inquilino_id)
            
            # Obter contrato ativo do inquilino
            contrato = Contrato.objects.filter(
                inquilino=inquilino,
                status='ATIVO'
            ).first()
            
            # Criar contexto para renderização
            contexto = {
                'inquilino': inquilino,
                'contrato': contrato,
                'data_vencimento': timezone.now().date() + timedelta(days=30),
                'dias_para_vencer': 30,
                'valor_devido': contrato.valor_aluguel if contrato else 1500.00,
                'data_atual': timezone.now().date(),
            }
            
            # Renderizar template
            assunto_renderizado = Template(template.assunto_template).render(Context(contexto))
            corpo_renderizado = Template(template.corpo_template).render(Context(contexto))
            
            return JsonResponse({
                'success': True,
                'assunto': assunto_renderizado,
                'corpo': corpo_renderizado,
                'formato': template.formato
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao testar template: {str(e)}'
            })
    
    # GET - Mostrar formulário de teste
    inquilinos = Inquilino.objects.filter(ativo=True).order_by('nome')[:50]
    
    context = {
        'template': template,
        'inquilinos': inquilinos
    }
    
    return render(request, 'notificacoes/templates/testar.html', context)


@login_required
def gerenciar_categorias(request):
    """Gerencia categorias de templates"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'criar':
            nome = request.POST.get('nome', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            
            if not nome:
                messages.error(request, 'Nome da categoria é obrigatório.')
            elif CategoriaTemplate.objects.filter(nome=nome).exists():
                messages.error(request, 'Já existe uma categoria com este nome.')
            else:
                CategoriaTemplate.objects.create(
                    nome=nome,
                    descricao=descricao
                )
                messages.success(request, f'Categoria "{nome}" criada com sucesso!')
        
        elif action == 'editar':
            categoria_id = request.POST.get('categoria_id')
            nome = request.POST.get('nome', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            
            if not nome:
                messages.error(request, 'Nome da categoria é obrigatório.')
            else:
                try:
                    categoria = CategoriaTemplate.objects.get(id=categoria_id)
                    if CategoriaTemplate.objects.filter(nome=nome).exclude(id=categoria_id).exists():
                        messages.error(request, 'Já existe outra categoria com este nome.')
                    else:
                        categoria.nome = nome
                        categoria.descricao = descricao
                        categoria.save()
                        messages.success(request, f'Categoria "{nome}" atualizada com sucesso!')
                except CategoriaTemplate.DoesNotExist:
                    messages.error(request, 'Categoria não encontrada.')
        
        elif action == 'excluir':
            categoria_id = request.POST.get('categoria_id')
            try:
                categoria = CategoriaTemplate.objects.get(id=categoria_id)
                
                # Verificar se há templates usando esta categoria
                templates_count = TemplateNotificacao.objects.filter(categoria=categoria).count()
                if templates_count > 0:
                    messages.error(
                        request,
                        f'Não é possível excluir a categoria "{categoria.nome}" '
                        f'pois ela possui {templates_count} templates associados.'
                    )
                else:
                    nome = categoria.nome
                    categoria.delete()
                    messages.success(request, f'Categoria "{nome}" excluída com sucesso!')
                    
            except CategoriaTemplate.DoesNotExist:
                messages.error(request, 'Categoria não encontrada.')
    
    # Listar categorias com estatísticas
    categorias = CategoriaTemplate.objects.annotate(
        total_templates=Count('templatenotificacao')
    ).order_by('nome')
    
    context = {
        'categorias': categorias
    }
    
    return render(request, 'notificacoes/templates/categorias.html', context)


# ===== SISTEMA APRIMORADO DE LOGS E HISTÓRICO =====

@login_required
def logs_detalhados(request):
    """Visualização detalhada de logs de mensagens com análise avançada"""
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template', 'contrato', 'usuario'
    ).order_by('-created_at')
    
    # Filtros avançados
    status = request.GET.get('status')
    canal = request.GET.get('canal')
    template_id = request.GET.get('template')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    busca = request.GET.get('busca')
    erro_tipo = request.GET.get('erro_tipo')
    usuario_id = request.GET.get('usuario')
    
    if status:
        notificacoes = notificacoes.filter(status=status)
    if canal:
        notificacoes = notificacoes.filter(canal=canal)
    if template_id:
        notificacoes = notificacoes.filter(template_id=template_id)
    if data_inicio:
        notificacoes = notificacoes.filter(created_at__date__gte=data_inicio)
    if data_fim:
        notificacoes = notificacoes.filter(created_at__date__lte=data_fim)
    if usuario_id:
        notificacoes = notificacoes.filter(usuario_id=usuario_id)
    if busca:
        notificacoes = notificacoes.filter(
            Q(assunto__icontains=busca) |
            Q(inquilino__nome__icontains=busca) |
            Q(destinatario__icontains=busca) |
            Q(erro_envio__icontains=busca)
        )
    
    # Filtro por tipo de erro
    if erro_tipo:
        notificacoes = notificacoes.filter(
            log_tentativas__contains=[{"error_type": erro_tipo}]
        )
    
    # Estatísticas detalhadas
    stats = {
        'total': notificacoes.count(),
        'enviadas': notificacoes.filter(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA']).count(),
        'pendentes': notificacoes.filter(status='PENDENTE').count(),
        'processando': notificacoes.filter(status='ENVIANDO').count(),
        'erros': notificacoes.filter(status__in=['ERRO', 'REJEITADA']).count(),
        'taxa_sucesso': 0,
        'tempo_medio_envio': None,
        'erros_por_tipo': {},
        'canais_utilizados': {},
        'templates_mais_usados': {},
    }
    
    if stats['total'] > 0:
        stats['taxa_sucesso'] = round((stats['enviadas'] / stats['total']) * 100, 2)
    
    # Análise de erros por tipo
    notificacoes_erro = notificacoes.filter(status__in=['ERRO', 'REJEITADA'])
    for notif in notificacoes_erro:
        if notif.log_tentativas:
            for tentativa in notif.log_tentativas:
                if tentativa.get('status') == 'erro':
                    erro_tipo = tentativa.get('error_type', 'unknown')
                    stats['erros_por_tipo'][erro_tipo] = stats['erros_por_tipo'].get(erro_tipo, 0) + 1
    
    # Análise por canal
    canais_stats = notificacoes.values('canal').annotate(total=Count('id'))
    for canal_stat in canais_stats:
        stats['canais_utilizados'][canal_stat['canal']] = canal_stat['total']
    
    # Templates mais utilizados
    templates_stats = notificacoes.filter(template__isnull=False).values(
        'template__nome'
    ).annotate(total=Count('id')).order_by('-total')[:5]
    for template_stat in templates_stats:
        stats['templates_mais_usados'][template_stat['template__nome']] = template_stat['total']
    
    paginator = Paginator(notificacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'templates': TemplateNotificacao.objects.filter(ativo=True),
        'usuarios': User.objects.filter(is_active=True),
        'status_choices': Notificacao.STATUS_CHOICES,
        'canal_choices': Notificacao.CANAL_CHOICES,
        'tipos_erro': list(stats['erros_por_tipo'].keys()),
    }
    
    return render(request, 'notificacoes/logs_detalhados.html', context)


@login_required
def monitoramento_tempo_real(request):
    """Dashboard de monitoramento em tempo real"""
    # Notificações das últimas 24 horas
    agora = timezone.now()
    ontem = agora - timedelta(hours=24)
    
    notificacoes_recentes = Notificacao.objects.filter(
        created_at__gte=ontem
    ).select_related('inquilino', 'template')
    
    # Estatísticas em tempo real
    stats_tempo_real = {
        'ultima_atualizacao': agora.strftime('%H:%M:%S'),
        'total_24h': notificacoes_recentes.count(),
        'enviadas_24h': notificacoes_recentes.filter(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA']).count(),
        'pendentes_24h': notificacoes_recentes.filter(status='PENDENTE').count(),
        'processando_24h': notificacoes_recentes.filter(status='ENVIANDO').count(),
        'erros_24h': notificacoes_recentes.filter(status__in=['ERRO', 'REJEITADA']).count(),
        'ultimas_10': list(notificacoes_recentes.order_by('-created_at')[:10].values(
            'id', 'assunto', 'inquilino__nome', 'canal', 'status', 'created_at'
        )),
        'atividade_por_hora': {},
        'status_distribuicao': {},
        'canais_atividade': {},
    }
    
    # Atividade por hora (últimas 24 horas)
    for i in range(24):
        hora_inicio = agora - timedelta(hours=i+1)
        hora_fim = agora - timedelta(hours=i)
        count = notificacoes_recentes.filter(
            created_at__gte=hora_inicio,
            created_at__lt=hora_fim
        ).count()
        stats_tempo_real['atividade_por_hora'][f'{hora_inicio.hour:02d}:00'] = count
    
    # Distribuição por status
    status_dist = notificacoes_recentes.values('status').annotate(total=Count('id'))
    for item in status_dist:
        stats_tempo_real['status_distribuicao'][item['status']] = item['total']
    
    # Atividade por canal
    canais_dist = notificacoes_recentes.values('canal').annotate(total=Count('id'))
    for item in canais_dist:
        stats_tempo_real['canais_atividade'][item['canal']] = item['total']
    
    return JsonResponse(stats_tempo_real)


@login_required
def dashboard_monitoramento(request):
    """Dashboard principal de monitoramento"""
    return render(request, 'notificacoes/dashboard_monitoramento.html')


@login_required
def analise_performance(request):
    """Análise detalhada de performance do sistema"""
    # Período de análise (padrão: últimos 30 dias)
    periodo_dias = int(request.GET.get('periodo', 30))
    data_fim = timezone.now().date()
    data_inicio = data_fim - timedelta(days=periodo_dias)
    
    notificacoes = Notificacao.objects.filter(
        created_at__date__gte=data_inicio,
        created_at__date__lte=data_fim
    ).select_related('template', 'inquilino')
    
    # Métricas de performance
    performance_stats = {
        'periodo': f'{data_inicio.strftime("%d/%m/%Y")} - {data_fim.strftime("%d/%m/%Y")}',
        'total_mensagens': notificacoes.count(),
        'taxa_entrega_geral': 0,
        'tempo_medio_processamento': None,
        'picos_atividade': [],
        'performance_por_canal': {},
        'performance_por_template': {},
        'tendencia_erros': {},
        'horarios_pico': {},
    }
    
    if performance_stats['total_mensagens'] > 0:
        # Taxa de entrega geral
        enviadas = notificacoes.filter(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA']).count()
        performance_stats['taxa_entrega_geral'] = round((enviadas / performance_stats['total_mensagens']) * 100, 2)
        
        # Performance por canal
        for canal_choice in Notificacao.CANAL_CHOICES:
            canal = canal_choice[0]
            canal_notifs = notificacoes.filter(canal=canal)
            canal_total = canal_notifs.count()
            if canal_total > 0:
                canal_enviadas = canal_notifs.filter(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA']).count()
                canal_erros = canal_notifs.filter(status__in=['ERRO', 'REJEITADA']).count()
                performance_stats['performance_por_canal'][canal] = {
                    'total': canal_total,
                    'enviadas': canal_enviadas,
                    'erros': canal_erros,
                    'taxa_sucesso': round((canal_enviadas / canal_total) * 100, 2),
                    'taxa_erro': round((canal_erros / canal_total) * 100, 2),
                }
        
        # Performance por template (top 10)
        templates_stats = notificacoes.filter(template__isnull=False).values(
            'template__nome', 'template__id'
        ).annotate(
            total=Count('id'),
            enviadas=Count('id', filter=Q(status__in=['ENVIADA', 'ENTREGUE', 'ABERTA', 'CLICADA'])),
            erros=Count('id', filter=Q(status__in=['ERRO', 'REJEITADA']))
        ).order_by('-total')[:10]
        
        for template_stat in templates_stats:
            template_nome = template_stat['template__nome']
            total = template_stat['total']
            enviadas = template_stat['enviadas']
            erros = template_stat['erros']
            performance_stats['performance_por_template'][template_nome] = {
                'total': total,
                'enviadas': enviadas,
                'erros': erros,
                'taxa_sucesso': round((enviadas / total) * 100, 2) if total > 0 else 0,
                'taxa_erro': round((erros / total) * 100, 2) if total > 0 else 0,
            }
        
        # Análise de horários de pico
        for hora in range(24):
            hora_notifs = notificacoes.filter(created_at__hour=hora).count()
            performance_stats['horarios_pico'][f'{hora:02d}:00'] = hora_notifs
    
    context = {
        'stats': performance_stats,
        'periodo_opcoes': [7, 15, 30, 60, 90],
        'periodo_selecionado': periodo_dias,
    }
    
    return render(request, 'notificacoes/analise_performance.html', context)


@login_required
def relatorio_erros_detalhado(request):
    """Relatório detalhado de erros com sugestões de correção"""
    # Período de análise
    periodo_dias = int(request.GET.get('periodo', 7))
    data_fim = timezone.now().date()
    data_inicio = data_fim - timedelta(days=periodo_dias)
    
    notificacoes_erro = Notificacao.objects.filter(
        created_at__date__gte=data_inicio,
        created_at__date__lte=data_fim,
        status__in=['ERRO', 'REJEITADA']
    ).select_related('template', 'inquilino', 'usuario')
    
    # Análise de erros
    erros_analysis = {
        'total_erros': notificacoes_erro.count(),
        'erros_por_tipo': {},
        'erros_por_canal': {},
        'erros_por_template': {},
        'erros_recorrentes': [],
        'sugestoes_correcao': {},
        'tendencia_erros': {},
    }
    
    # Análise por tipo de erro
    for notif in notificacoes_erro:
        if notif.log_tentativas:
            for tentativa in notif.log_tentativas:
                if tentativa.get('status') == 'erro':
                    erro_tipo = tentativa.get('error_type', 'unknown')
                    erro_msg = tentativa.get('error_message', 'Erro desconhecido')
                    
                    if erro_tipo not in erros_analysis['erros_por_tipo']:
                        erros_analysis['erros_por_tipo'][erro_tipo] = {
                            'count': 0,
                            'mensagens': [],
                            'sugestao': tentativa.get('suggestion', 'Verifique a configuração')
                        }
                    
                    erros_analysis['erros_por_tipo'][erro_tipo]['count'] += 1
                    if erro_msg not in erros_analysis['erros_por_tipo'][erro_tipo]['mensagens']:
                        erros_analysis['erros_por_tipo'][erro_tipo]['mensagens'].append(erro_msg)
    
    # Análise por canal
    erros_canal = notificacoes_erro.values('canal').annotate(total=Count('id'))
    for item in erros_canal:
        erros_analysis['erros_por_canal'][item['canal']] = item['total']
    
    # Análise por template
    erros_template = notificacoes_erro.filter(template__isnull=False).values(
        'template__nome'
    ).annotate(total=Count('id')).order_by('-total')[:10]
    for item in erros_template:
        erros_analysis['erros_por_template'][item['template__nome']] = item['total']
    
    # Sugestões de correção baseadas nos tipos de erro mais comuns
    sugestoes_padrao = {
        'WhatsAppConfigurationError': 'Verifique as configurações da Evolution API (URL, chave de API, nome da instância)',
        'WhatsAppPhoneNumberError': 'Verifique se os números de telefone estão no formato correto (+55XXXXXXXXXXX)',
        'WhatsAppMessageError': 'Verifique se a mensagem não contém caracteres especiais ou é muito longa',
        'WhatsAppRateLimitError': 'Reduza a frequência de envio de mensagens ou implemente um sistema de fila',
        'general': 'Erro geral - verifique os logs do sistema e a conectividade de rede',
    }
    
    for tipo_erro, dados in erros_analysis['erros_por_tipo'].items():
        erros_analysis['sugestoes_correcao'][tipo_erro] = sugestoes_padrao.get(
            tipo_erro, 'Consulte a documentação ou entre em contato com o suporte'
        )
    
    context = {
        'erros_analysis': erros_analysis,
        'periodo_dias': periodo_dias,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'notificacoes_erro': notificacoes_erro[:50],  # Últimos 50 erros para detalhamento
    }
    
    return render(request, 'notificacoes/relatorio_erros.html', context)


@login_required
def exportar_logs_avancado(request):
    """Exportação avançada de logs com filtros personalizados"""
    # Aplicar filtros
    notificacoes = Notificacao.objects.select_related(
        'inquilino', 'template', 'contrato', 'usuario'
    ).order_by('-created_at')
    
    # Filtros da query string
    filtros = {
        'status': request.GET.get('status'),
        'canal': request.GET.get('canal'),
        'template_id': request.GET.get('template'),
        'data_inicio': request.GET.get('data_inicio'),
        'data_fim': request.GET.get('data_fim'),
        'formato': request.GET.get('formato', 'csv'),  # csv, json, xlsx
    }
    
    # Aplicar filtros
    if filtros['status']:
        notificacoes = notificacoes.filter(status=filtros['status'])
    if filtros['canal']:
        notificacoes = notificacoes.filter(canal=filtros['canal'])
    if filtros['template_id']:
        notificacoes = notificacoes.filter(template_id=filtros['template_id'])
    if filtros['data_inicio']:
        notificacoes = notificacoes.filter(created_at__date__gte=filtros['data_inicio'])
    if filtros['data_fim']:
        notificacoes = notificacoes.filter(created_at__date__lte=filtros['data_fim'])
    
    # Limitar a 10000 registros para evitar sobrecarga
    notificacoes = notificacoes[:10000]
    
    if filtros['formato'] == 'json':
        # Exportar como JSON
        dados = []
        for notif in notificacoes:
            dados.append({
                'id': notif.id,
                'data_criacao': notif.created_at.isoformat(),
                'data_envio': notif.data_envio.isoformat() if notif.data_envio else None,
                'inquilino': notif.inquilino.nome,
                'destinatario': notif.destinatario,
                'canal': notif.canal,
                'status': notif.status,
                'assunto': notif.assunto,
                'template': notif.template.nome if notif.template else None,
                'tentativas': notif.tentativas_realizadas,
                'log_tentativas': notif.log_tentativas,
                'erro_envio': notif.erro_envio,
                'usuario': notif.usuario.username,
            })
        
        response = JsonResponse(dados, safe=False)
        response['Content-Disposition'] = f'attachment; filename="logs_notificacoes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    else:
        # Exportar como CSV (padrão)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="logs_notificacoes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Data Criação', 'Data Envio', 'Inquilino', 'Destinatário', 
            'Canal', 'Status', 'Assunto', 'Template', 'Tentativas', 
            'Último Erro', 'Usuário', 'Detalhes Log'
        ])
        
        for notif in notificacoes:
            ultimo_erro = ''
            if notif.log_tentativas:
                for tentativa in reversed(notif.log_tentativas):
                    if tentativa.get('status') == 'erro':
                        ultimo_erro = tentativa.get('error_message', '')
                        break
            
            writer.writerow([
                notif.id,
                notif.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                notif.data_envio.strftime('%d/%m/%Y %H:%M:%S') if notif.data_envio else '',
                notif.inquilino.nome,
                notif.destinatario,
                notif.get_canal_display(),
                notif.get_status_display(),
                notif.assunto,
                notif.template.nome if notif.template else '',
                notif.tentativas_realizadas,
                ultimo_erro,
                notif.usuario.username,
                json.dumps(notif.log_tentativas, ensure_ascii=False) if notif.log_tentativas else ''
            ])
        
        return response


@login_required
def limpar_logs_antigos(request):
    """Limpeza de logs antigos com confirmação"""
    if request.method == 'POST':
        dias_manter = int(request.POST.get('dias_manter', 90))
        data_corte = timezone.now() - timedelta(days=dias_manter)
        
        # Contar registros que serão removidos
        count_remover = Notificacao.objects.filter(created_at__lt=data_corte).count()
        
        if request.POST.get('confirmar') == 'sim':
            # Executar limpeza
            Notificacao.objects.filter(created_at__lt=data_corte).delete()
            messages.success(request, f'{count_remover} registros de log foram removidos com sucesso.')
            return redirect('notificacoes:logs_detalhados')
        else:
            # Mostrar confirmação
            context = {
                'count_remover': count_remover,
                'dias_manter': dias_manter,
                'data_corte': data_corte,
            }
            return render(request, 'notificacoes/confirmar_limpeza.html', context)
    
    return render(request, 'notificacoes/limpar_logs.html')


@login_required
def whatsapp_dashboard(request):
    """View para o dashboard principal do WhatsApp"""
    host = (request.get_host() or '').split(':')[0].lower()
    is_railway = (
        host.endswith('.railway.app')
        or host.endswith('.up.railway.app')
        or any(os.getenv(k) for k in ('RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_DEPLOYMENT_ID'))
    )
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                tenant = None
        if not tenant:
            tenant = Tenant.objects.filter(usuario_admin=request.user).first()
            if tenant:
                request.session['tenant_id'] = tenant.id
                request.tenant = tenant

    status_filtro = (request.GET.get('status') or 'ATIVO').upper()
    if status_filtro not in {'ATIVO', 'INATIVO', 'TODOS'}:
        status_filtro = 'ATIVO'

    q = (request.GET.get('q') or '').strip()
    com_telefone = (request.GET.get('com_telefone') or '').strip() == '1'
    com_contrato = (request.GET.get('com_contrato') or '').strip() == '1'
    inclui_sem_tenant = (request.GET.get('inclui_sem_tenant') or '1').strip() == '1'

    wa_config_geral = None
    wa_config_boas_vindas = None
    wa_config_aluguel = None
    wa_config_iptu = None
    wa_config_contrato_vencendo = None
    inquilinos_base = Inquilino.objects.none()
    inquilinos = Inquilino.objects.none()
    wa_excluded_ids = []
    wa_excluded_inquilinos = Inquilino.objects.none()
    dashboard_error = None

    if request.user.is_superuser:
        if tenant and inclui_sem_tenant:
            inquilinos_base = Inquilino.objects.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        elif tenant:
            inquilinos_base = Inquilino.objects.filter(tenant=tenant)
        else:
            inquilinos_base = Inquilino.objects.all()
    else:
        if tenant:
            inquilinos_base = Inquilino.objects.filter(tenant=tenant)
        else:
            inquilinos_base = Inquilino.objects.none()

    try:
        from django.db.utils import OperationalError, ProgrammingError
        from .models import WhatsAppMensagemConfig
        if tenant:
            wa_config_geral = WhatsAppMensagemConfig.objects.filter(tenant=tenant, tipo='GERAL').first()
            wa_config_boas_vindas = WhatsAppMensagemConfig.objects.filter(tenant=tenant, tipo='BOAS_VINDAS').first()
            wa_config_aluguel = WhatsAppMensagemConfig.objects.filter(tenant=tenant, tipo='COBRANCA_ALUGUEL').first()
            wa_config_iptu = WhatsAppMensagemConfig.objects.filter(tenant=tenant, tipo='COBRANCA_IPTU').first()
            wa_config_contrato_vencendo = WhatsAppMensagemConfig.objects.filter(tenant=tenant, tipo='CONTRATO_VENCENDO').first()
        elif request.user.is_superuser:
            wa_config_geral = WhatsAppMensagemConfig.objects.filter(tenant__isnull=True, tipo='GERAL').first()
            wa_config_boas_vindas = WhatsAppMensagemConfig.objects.filter(tenant__isnull=True, tipo='BOAS_VINDAS').first()
            wa_config_aluguel = WhatsAppMensagemConfig.objects.filter(tenant__isnull=True, tipo='COBRANCA_ALUGUEL').first()
            wa_config_iptu = WhatsAppMensagemConfig.objects.filter(tenant__isnull=True, tipo='COBRANCA_IPTU').first()
            wa_config_contrato_vencendo = WhatsAppMensagemConfig.objects.filter(tenant__isnull=True, tipo='CONTRATO_VENCENDO').first()
    except (OperationalError, ProgrammingError) as e:
        dashboard_error = None
        if tenant:
            cfg = tenant.configuracoes or {}
            session_cfg = cfg.get('whatsapp_configs') or {}
        else:
            session_cfg = request.session.get('whatsapp_configs') or {}
        wa_config_geral = {'mensagem': session_cfg.get('GERAL', '')}
        wa_config_boas_vindas = {'mensagem': session_cfg.get('BOAS_VINDAS', '')}
        wa_config_aluguel = {'mensagem': session_cfg.get('COBRANCA_ALUGUEL', '')}
        wa_config_iptu = {'mensagem': session_cfg.get('COBRANCA_IPTU', '')}
        wa_config_contrato_vencendo = {'mensagem': session_cfg.get('CONTRATO_VENCENDO', '')}

    if not tenant and not request.user.is_superuser:
        session_cfg = request.session.get('whatsapp_configs') or {}
        wa_config_geral = {'mensagem': session_cfg.get('GERAL', '')}
        wa_config_boas_vindas = {'mensagem': session_cfg.get('BOAS_VINDAS', '')}
        wa_config_aluguel = {'mensagem': session_cfg.get('COBRANCA_ALUGUEL', '')}
        wa_config_iptu = {'mensagem': session_cfg.get('COBRANCA_IPTU', '')}
        wa_config_contrato_vencendo = {'mensagem': session_cfg.get('CONTRATO_VENCENDO', '')}

    if q:
        inquilinos_base = inquilinos_base.filter(Q(nome__icontains=q) | Q(telefone__icontains=q))

    if com_telefone:
        inquilinos_base = inquilinos_base.exclude(Q(telefone__isnull=True) | Q(telefone=''))

    if com_contrato:
        inquilinos_base = inquilinos_base.filter(contrato__status='ATIVO').distinct()

    try:
        excluded = set()
        if tenant:
            cfg = tenant.configuracoes or {}
            excluded = set(cfg.get('whatsapp_excecoes_inquilinos', []) or [])
        else:
            excluded = set(request.session.get('whatsapp_excecoes_inquilinos', []) or [])
        wa_excluded_ids = sorted({int(x) for x in excluded if str(x).isdigit()})
    except Exception:
        wa_excluded_ids = []

    if status_filtro == 'ATIVO':
        inquilinos_base = inquilinos_base.filter(ativo=True)
    elif status_filtro == 'INATIVO':
        inquilinos_base = inquilinos_base.filter(ativo=False)

    if wa_excluded_ids:
        wa_excluded_inquilinos = inquilinos_base.filter(id__in=wa_excluded_ids)
        inquilinos = inquilinos_base.exclude(id__in=wa_excluded_ids)
    else:
        wa_excluded_inquilinos = Inquilino.objects.none()
        inquilinos = inquilinos_base

    wa_total_base = inquilinos_base.count()
    wa_total_excluded = wa_excluded_inquilinos.count() if wa_excluded_ids else 0
    wa_total_visiveis = inquilinos.count()

    wa_msg_geral = _wa_get_cfg_message(request, tenant, 'GERAL')
    wa_msg_boas_vindas = _wa_get_cfg_message(request, tenant, 'BOAS_VINDAS')
    wa_msg_aluguel = _wa_get_cfg_message(request, tenant, 'COBRANCA_ALUGUEL')
    wa_msg_iptu = _wa_get_cfg_message(request, tenant, 'COBRANCA_IPTU')
    wa_msg_contrato_vencendo = _wa_get_cfg_message(request, tenant, 'CONTRATO_VENCENDO')
    wa_templates = {
        'GERAL': wa_msg_geral or '',
        'BOAS_VINDAS': wa_msg_boas_vindas or '',
        'COBRANCA_ALUGUEL': wa_msg_aluguel or '',
        'COBRANCA_IPTU': wa_msg_iptu or '',
        'CONTRATO_VENCENDO': wa_msg_contrato_vencendo or '',
    }
    
    context = {
        'tenant': tenant,
        'tenant_required': False,
        'is_railway': is_railway,
        'whatsapp_dashboard_error': dashboard_error,
        'inquilinos': inquilinos,
        'inquilinos_base': inquilinos_base,
        'wa_status_filtro': status_filtro,
        'wa_q': q,
        'wa_com_telefone': com_telefone,
        'wa_com_contrato': com_contrato,
        'wa_inclui_sem_tenant': inclui_sem_tenant,
        'wa_excluded_ids': wa_excluded_ids,
        'wa_excluded_inquilinos': wa_excluded_inquilinos,
        'wa_total_base': wa_total_base,
        'wa_total_excluded': wa_total_excluded,
        'wa_total_visiveis': wa_total_visiveis,
        'wa_has_msg_geral': bool((wa_msg_geral or '').strip()),
        'wa_has_msg_boas_vindas': bool((wa_msg_boas_vindas or '').strip()),
        'wa_has_msg_aluguel': bool((wa_msg_aluguel or '').strip()),
        'wa_has_msg_iptu': bool((wa_msg_iptu or '').strip()),
        'wa_has_msg_contrato_vencendo': bool((wa_msg_contrato_vencendo or '').strip()),
        'wa_templates_json': json.dumps(wa_templates),
        'wa_config_geral': wa_config_geral,
        'wa_config_boas_vindas': wa_config_boas_vindas,
        'wa_config_aluguel': wa_config_aluguel,
        'wa_config_iptu': wa_config_iptu,
        'wa_config_contrato_vencendo': wa_config_contrato_vencendo,
    }
    
    return render(request, 'notificacoes/whatsapp_dashboard.html', context)


@login_required
def whatsapp_conectar(request):
    """View para a aba de conexão do WhatsApp (Legado)"""
    return redirect('notificacoes:whatsapp_dashboard')

# ==============================================================================
# API DO NOVO DASHBOARD WHATSAPP (EVOLUTION API)
# ==============================================================================
from django.http import JsonResponse
from .whatsapp_service import WhatsAppService

@login_required
@require_POST
def api_whatsapp_excecoes(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                tenant = None
        if not tenant:
            tenant = Tenant.objects.filter(usuario_admin=request.user).first()
            if tenant:
                request.session['tenant_id'] = tenant.id
                request.tenant = tenant

    inquilino_id = request.POST.get('inquilino_id')
    action = (request.POST.get('action') or 'add').strip().lower()
    if not inquilino_id or not str(inquilino_id).isdigit():
        return JsonResponse({'success': False, 'error': 'inquilino_id inválido'}, status=400)
    if action not in {'add', 'remove'}:
        return JsonResponse({'success': False, 'error': 'action inválida'}, status=400)

    inquilino_id_int = int(inquilino_id)
    if tenant:
        if not Inquilino.objects.filter(id=inquilino_id_int, tenant=tenant).exists():
            return JsonResponse({'success': False, 'error': 'Inquilino não encontrado'}, status=404)
    elif not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Tenant não identificado'}, status=400)
    else:
        if not Inquilino.objects.filter(id=inquilino_id_int).exists():
            return JsonResponse({'success': False, 'error': 'Inquilino não encontrado'}, status=404)

    if tenant:
        cfg = tenant.configuracoes or {}
        excluded = set(cfg.get('whatsapp_excecoes_inquilinos', []) or [])
        if action == 'add':
            excluded.add(inquilino_id_int)
        else:
            excluded.discard(inquilino_id_int)
        cfg['whatsapp_excecoes_inquilinos'] = sorted({int(x) for x in excluded if str(x).isdigit()})
        tenant.configuracoes = cfg
        tenant.save(update_fields=['configuracoes'])
        ids = cfg.get('whatsapp_excecoes_inquilinos', [])
    else:
        excluded = set(request.session.get('whatsapp_excecoes_inquilinos', []) or [])
        if action == 'add':
            excluded.add(inquilino_id_int)
        else:
            excluded.discard(inquilino_id_int)
        ids = sorted({int(x) for x in excluded if str(x).isdigit()})
        request.session['whatsapp_excecoes_inquilinos'] = ids
        request.session.modified = True

    return JsonResponse({'success': True, 'excluded_ids': ids})

@login_required
def api_whatsapp_status(request):
    """Retorna o status atual da conexão com o WhatsApp"""
    service = WhatsAppService()
    host = (request.get_host() or '').split(':')[0].lower()
    is_railway = (
        host.endswith('.railway.app')
        or host.endswith('.up.railway.app')
        or any(os.getenv(k) for k in ('RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_DEPLOYMENT_ID'))
    )
    last_ok_ts = request.session.get('wa_last_send_ok_ts')
    last_ok_recent = False
    try:
        if last_ok_ts:
            last_ok_recent = (timezone.now().timestamp() - float(last_ok_ts)) <= 90
    except Exception:
        last_ok_recent = False
    try:
        if not service.check_api_health():
            if last_ok_recent:
                return JsonResponse({'success': True, 'connected': True, 'status': 'connected', 'message': 'Conectado'})
            diag = None
            try:
                diag = service.docker_diagnostics()
            except Exception:
                diag = None

            api_url = getattr(service, 'api_url', None)
            last_err = getattr(service, 'last_health_error', None)
            message = 'A Evolution API não está rodando.'
            if api_url:
                message = f'Falha ao conectar na Evolution API ({api_url}).'
            if last_err:
                message = message + f' {last_err}'
            if diag and diag.get('message') and not is_railway:
                message = diag.get('message')
            return JsonResponse({
                'success': False,
                'connected': False,
                'status': 'offline',
                'message': message,
                'auto_started': False,
                'can_auto_start': (not is_railway),
                'api_url': api_url,
            })

        res = service.get_status()
        if res.get('status') == 'connected':
            return JsonResponse({'success': True, 'connected': True, 'status': 'connected', 'message': 'Conectado', 'owner': res.get('owner') or ''})
        if res.get('status') == 'connecting':
            return JsonResponse({'success': True, 'connected': False, 'status': 'connecting', 'message': 'Conectando...', 'owner': res.get('owner') or ''})
        if res.get('status') in {'error'} and last_ok_recent:
            return JsonResponse({'success': True, 'connected': True, 'status': 'connected', 'message': 'Conectado', 'owner': res.get('owner') or ''})
        if res.get('status') in {'disconnected'} and last_ok_recent:
            return JsonResponse({'success': True, 'connected': True, 'status': 'connected', 'message': 'Conectado', 'owner': res.get('owner') or ''})
        return JsonResponse({'success': True, 'connected': False, 'status': 'disconnected', 'message': 'Desconectado', 'owner': res.get('owner') or ''})
    except Exception as e:
        if last_ok_recent:
            return JsonResponse({'success': True, 'connected': True, 'status': 'connected', 'message': 'Conectado'})
        return JsonResponse({'success': False, 'connected': False, 'status': 'error', 'message': 'Erro ao consultar status', 'error': str(e)})

@login_required
def api_whatsapp_qrcode(request):
    """Retorna o QR Code em base64"""
    service = WhatsAppService()
    res = service.get_qrcode()
    
    if res.get('success'):
        return JsonResponse({'success': True, 'qrcode': res.get('qrcode')})
    return JsonResponse({'success': False, 'error': res.get('error')})

@login_required
def api_whatsapp_logout(request):
    """Desconecta a instância do WhatsApp"""
    if request.method == 'POST':
        service = WhatsAppService()
        res = service.logout()
        return JsonResponse(res)
    return JsonResponse({'success': False, 'error': 'Método não permitido'})

@login_required
def api_whatsapp_send_test(request):
    """Envia uma mensagem de teste a partir do Dashboard"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            telefone = data.get('telefone')
            mensagem = data.get('mensagem')
            
            if not telefone or not mensagem:
                return JsonResponse({'success': False, 'error': 'Telefone e mensagem são obrigatórios'})
                
            service = WhatsAppService()
            res = service.send_message(telefone, mensagem)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


def _wa_format_brl(value):
    try:
        from decimal import Decimal as _D
        v = _D(str(value))
    except Exception:
        return ''
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _wa_next_due_date(dia_vencimento, today):
    try:
        dia = int(dia_vencimento)
        if dia < 1:
            dia = 1
        if dia > 28:
            dia = 28
    except Exception:
        dia = 10
    year = today.year
    month = today.month
    if today.day > dia:
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    from datetime import date as _date
    return _date(year, month, dia)


def _wa_get_cfg_message(request, tenant, tipo):
    if tenant:
        cfg = tenant.configuracoes or {}
        wa_cfg = cfg.get('whatsapp_configs') or {}
        if wa_cfg.get(tipo):
            return wa_cfg.get(tipo)
    wa_cfg = request.session.get('whatsapp_configs') or {}
    if wa_cfg.get(tipo):
        return wa_cfg.get(tipo)
    try:
        from .models import WhatsAppMensagemConfig
        qs = WhatsAppMensagemConfig.objects.filter(tipo=tipo)
        if tenant:
            qs = qs.filter(tenant=tenant)
        else:
            qs = qs.filter(tenant__isnull=True)
        obj = qs.first()
        return obj.mensagem if obj else ''
    except Exception:
        return ''


@login_required
@require_POST
def api_whatsapp_send_campaign(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                tenant = None
        if not tenant:
            tenant = Tenant.objects.filter(usuario_admin=request.user).first()
            if tenant:
                request.session['tenant_id'] = tenant.id
                request.tenant = tenant

    import json
    try:
        data = json.loads(request.body or '{}')
    except Exception:
        data = {}
    tipo = (data.get('tipo') or '').strip().upper()
    if tipo not in {'GERAL', 'BOAS_VINDAS', 'COBRANCA_ALUGUEL', 'COBRANCA_IPTU', 'CONTRATO_VENCENDO'}:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'}, status=400)

    msg_tpl = _wa_get_cfg_message(request, tenant, tipo)
    if not msg_tpl:
        return JsonResponse({'success': False, 'error': 'Mensagem não configurada para este tipo.'}, status=400)

    try:
        excluded = set()
        if tenant:
            cfg = tenant.configuracoes or {}
            excluded = set(cfg.get('whatsapp_excecoes_inquilinos', []) or [])
        else:
            excluded = set(request.session.get('whatsapp_excecoes_inquilinos', []) or [])
        excluded_ids = {int(x) for x in excluded if str(x).isdigit()}
    except Exception:
        excluded_ids = set()

    status_filtro = (data.get('status') or 'ATIVO').upper()
    if status_filtro not in {'ATIVO', 'INATIVO', 'TODOS'}:
        status_filtro = 'ATIVO'

    q = (data.get('q') or '').strip()
    com_telefone = str(data.get('com_telefone') or '').strip() == '1'
    com_contrato = str(data.get('com_contrato') or '').strip() == '1'
    inclui_sem_tenant = str(data.get('inclui_sem_tenant') or '1').strip() == '1'

    qs = Inquilino.objects.all()
    if request.user.is_superuser:
        if tenant and inclui_sem_tenant:
            qs = qs.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        elif tenant:
            qs = qs.filter(tenant=tenant)
        else:
            qs = qs
    else:
        if tenant:
            qs = qs.filter(tenant=tenant)
        else:
            return JsonResponse({'success': False, 'error': 'Tenant não identificado.'}, status=400)

    if status_filtro == 'ATIVO':
        qs = qs.filter(ativo=True)
    elif status_filtro == 'INATIVO':
        qs = qs.filter(ativo=False)

    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(telefone__icontains=q))

    if com_telefone:
        qs = qs.exclude(Q(telefone__isnull=True) | Q(telefone=''))

    if com_contrato:
        qs = qs.filter(contrato__status='ATIVO').distinct()

    if excluded_ids:
        qs = qs.exclude(id__in=excluded_ids)

    limit = data.get('limit')
    try:
        limit = int(limit) if limit is not None else 10
    except Exception:
        limit = 10
    if limit <= 0 or limit > 100:
        limit = 10

    destinatarios = list(qs.order_by('nome')[:limit])

    service = WhatsAppService()
    if not service.check_api_health():
        return JsonResponse({'success': False, 'error': 'WhatsApp: Evolution API offline.'}, status=400)
    st = service.get_status()
    if st.get('status') != 'connected':
        return JsonResponse({'success': False, 'error': 'WhatsApp: desconectado. Leia o QR Code.'}, status=400)

    from datetime import date as _date
    today = _date.today()
    enviadas = 0
    puladas_sem_tel = 0
    erros = 0
    for inq in destinatarios:
        telefone = (inq.telefone or '').strip()
        if not telefone:
            puladas_sem_tel += 1
            continue

        contrato = Contrato.objects.filter(inquilino=inq, status='ATIVO').select_related('imovel').first()
        venc = ''
        valor = ''
        data_fim = ''
        dias = ''
        imovel_desc = ''
        if contrato:
            venc = _wa_next_due_date(getattr(contrato, 'dia_vencimento', 10), today).strftime('%d/%m/%Y')
            valor = _wa_format_brl(getattr(contrato, 'valor_aluguel', ''))
            try:
                if getattr(contrato, 'data_fim', None):
                    data_fim = contrato.data_fim.strftime('%d/%m/%Y')
                    dias = str((contrato.data_fim - today).days)
            except Exception:
                pass
            try:
                if getattr(contrato, 'imovel', None):
                    imovel_desc = str(contrato.imovel)
            except Exception:
                pass
        mensagem = msg_tpl
        mensagem = mensagem.replace('{NOME}', inq.nome or '')
        mensagem = mensagem.replace('{VALOR}', valor)
        mensagem = mensagem.replace('{VENCIMENTO}', venc)
        mensagem = mensagem.replace('{DATA_FIM}', data_fim)
        mensagem = mensagem.replace('{DIAS}', dias)
        mensagem = mensagem.replace('{IMOVEL}', imovel_desc)

        res = service.send_message(telefone, mensagem)
        if res.get('success'):
            enviadas += 1
            request.session['wa_last_send_ok_ts'] = timezone.now().timestamp()
            request.session.modified = True
        else:
            erros += 1

    return JsonResponse({'success': True, 'enviadas': enviadas, 'erros': erros, 'puladas_sem_telefone': puladas_sem_tel, 'limit': limit})


@login_required
@require_POST
def api_whatsapp_send_selected(request):
    try:
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            tenant_id = request.session.get('tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                    request.tenant = tenant
                except Tenant.DoesNotExist:
                    tenant = None
            if not tenant:
                tenant = Tenant.objects.filter(usuario_admin=request.user).first()
                if tenant:
                    request.session['tenant_id'] = tenant.id
                    request.tenant = tenant

        try:
            data = json.loads(request.body or '{}')
        except Exception:
            data = {}

        tipo = (data.get('tipo') or '').strip().upper()
        if tipo not in {'GERAL', 'BOAS_VINDAS', 'COBRANCA_ALUGUEL', 'COBRANCA_IPTU', 'CONTRATO_VENCENDO'}:
            return JsonResponse({'success': False, 'error': 'Tipo inválido'}, status=400)

        ids = data.get('inquilino_ids') or []
        if not isinstance(ids, list):
            return JsonResponse({'success': False, 'error': 'inquilino_ids inválido'}, status=400)
        try:
            ids = [int(x) for x in ids if str(x).isdigit()]
        except Exception:
            ids = []
        ids = list(dict.fromkeys(ids))
        if not ids:
            return JsonResponse({'success': False, 'error': 'Selecione pelo menos 1 inquilino'}, status=400)
        if len(ids) > 200:
            return JsonResponse({'success': False, 'error': 'Limite de 200 inquilinos por envio'}, status=400)

        mensagem_custom = (data.get('mensagem') or '').strip()
        msg_tpl = mensagem_custom or _wa_get_cfg_message(request, tenant, tipo)
        if not msg_tpl:
            return JsonResponse({'success': False, 'error': 'Mensagem não configurada para este tipo.'}, status=400)

        qs = Inquilino.objects.filter(id__in=ids)
        if request.user.is_superuser:
            if tenant:
                qs = qs.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        else:
            if tenant:
                qs = qs.filter(tenant=tenant)
            else:
                return JsonResponse({'success': False, 'error': 'Tenant não identificado.'}, status=400)

        destinatarios = list(qs.order_by('nome'))
        found_ids = {x.id for x in destinatarios}
        missing_ids = [x for x in ids if x not in found_ids]

        service = WhatsAppService()
        try:
            if not service.check_api_health():
                return JsonResponse({'success': False, 'error': 'WhatsApp: Evolution API offline.'}, status=400)
        except Exception:
            logger.exception('WhatsApp healthcheck error')
            return JsonResponse({'success': False, 'error': 'WhatsApp: falha ao consultar a Evolution API.'}, status=400)

        try:
            st = service.get_status()
        except Exception:
            logger.exception('WhatsApp get_status error')
            return JsonResponse({'success': False, 'error': 'WhatsApp: falha ao consultar status da instância.'}, status=400)
        if st.get('status') != 'connected':
            return JsonResponse({'success': False, 'error': 'WhatsApp: desconectado. Leia o QR Code.'}, status=400)

        from datetime import date as _date
        today = _date.today()
        owner_digits = ''
        try:
            owner_digits = (service.get_owner_digits() or '').strip()
        except Exception:
            owner_digits = ''
        if owner_digits:
            request.session['wa_owner_digits'] = owner_digits
            request.session.modified = True
        enviadas = 0
        puladas_sem_tel = 0
        erros = 0
        results = []

        for inq in destinatarios:
            try:
                telefone = (inq.telefone or '').strip()
                if not telefone:
                    puladas_sem_tel += 1
                    results.append({'inquilino_id': inq.id, 'nome': inq.nome, 'ok': False, 'error': 'Sem telefone'})
                    continue

                telefone_formatado = ''
                contrato = Contrato.objects.filter(inquilino=inq, status='ATIVO').select_related('imovel').first()
                venc = ''
                valor = ''
                data_fim = ''
                dias = ''
                imovel_desc = ''
                if contrato:
                    venc = _wa_next_due_date(getattr(contrato, 'dia_vencimento', 10), today).strftime('%d/%m/%Y')
                    if tipo == 'COBRANCA_IPTU':
                        valor = _wa_format_brl(getattr(contrato, 'valor_iptu', ''))
                    else:
                        valor = _wa_format_brl(getattr(contrato, 'valor_aluguel', ''))
                    try:
                        if getattr(contrato, 'data_fim', None):
                            data_fim = contrato.data_fim.strftime('%d/%m/%Y')
                            dias = str((contrato.data_fim - today).days)
                    except Exception:
                        pass
                    try:
                        if getattr(contrato, 'imovel', None):
                            imovel_desc = str(contrato.imovel)
                    except Exception:
                        pass

                mensagem = msg_tpl
                mensagem = mensagem.replace('{NOME}', inq.nome or '')
                mensagem = mensagem.replace('{VALOR}', valor)
                mensagem = mensagem.replace('{VENCIMENTO}', venc)
                mensagem = mensagem.replace('{DATA_FIM}', data_fim)
                mensagem = mensagem.replace('{DIAS}', dias)
                mensagem = mensagem.replace('{IMOVEL}', imovel_desc)

                try:
                    try:
                        telefone_formatado = service.format_phone(telefone)
                    except Exception:
                        telefone_formatado = ''
                    if owner_digits and telefone_formatado and (telefone_formatado.endswith(owner_digits) or owner_digits.endswith(telefone_formatado)):
                        erros += 1
                        results.append({
                            'inquilino_id': inq.id,
                            'nome': inq.nome,
                            'ok': False,
                            'error': 'Destino é o mesmo número conectado na instância. Para testar, envie para outro número.',
                            'to': telefone_formatado,
                        })
                        continue
                    res = service.send_message(telefone, mensagem)
                except Exception:
                    logger.exception('WhatsApp send_message error')
                    res = {'success': False, 'error': 'Falha ao chamar Evolution API'}

                if res.get('success'):
                    enviadas += 1
                    request.session['wa_last_send_ok_ts'] = timezone.now().timestamp()
                    request.session.modified = True
                    evo = res.get('response') or {}
                    evo_id = None
                    if isinstance(evo, dict):
                        key = evo.get('key')
                        if isinstance(key, dict):
                            evo_id = key.get('id') or key.get('remoteJid')
                        else:
                            evo_id = key
                        evo_id = evo_id or evo.get('messageId') or evo.get('id')
                    results.append({
                        'inquilino_id': inq.id,
                        'nome': inq.nome,
                        'ok': True,
                        'to': telefone_formatado,
                        'evo_id': evo_id,
                        'wa_exists': res.get('exists'),
                        'wa_jid': res.get('jid') or '',
                    })
                else:
                    erros += 1
                    err = res.get('error') or res.get('message') or 'Falha ao enviar'
                    results.append({
                        'inquilino_id': inq.id,
                        'nome': inq.nome,
                        'ok': False,
                        'error': err,
                        'to': telefone_formatado,
                        'wa_exists': res.get('exists'),
                        'wa_jid': res.get('jid') or '',
                    })
            except Exception:
                erros += 1
                logger.exception('Erro ao montar/enviar mensagem WhatsApp para inquilino_id=%s', getattr(inq, 'id', None))
                results.append({'inquilino_id': getattr(inq, 'id', None), 'nome': getattr(inq, 'nome', ''), 'ok': False, 'error': 'Erro interno ao enviar'})

        if missing_ids:
            for mid in missing_ids[:50]:
                results.append({'inquilino_id': mid, 'nome': '', 'ok': False, 'error': 'Não encontrado'})

        return JsonResponse({
            'success': True,
            'enviadas': enviadas,
            'erros': erros,
            'puladas_sem_telefone': puladas_sem_tel,
            'total_selecionados': len(ids),
            'total_encontrados': len(destinatarios),
            'results': results[:200],
            'debug': ({
                'instance': getattr(service, 'instance_name', ''),
                'api_url': getattr(service, 'api_url', ''),
                'owner': owner_digits,
            } if request.user.is_superuser else None),
        })
    except Exception as e:
        logger.exception('Erro interno em api_whatsapp_send_selected')
        payload = {'success': False, 'error': 'Erro interno ao enviar (servidor).'}
        if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_superuser:
            payload['debug'] = str(e)
        return JsonResponse(payload, status=500)


@login_required
def api_whatsapp_start_docker(request):
    service = WhatsAppService()
    host = (request.get_host() or '').split(':')[0].lower()
    is_railway = (
        host.endswith('.railway.app')
        or host.endswith('.up.railway.app')
        or any(os.getenv(k) for k in ('RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PUBLIC_DOMAIN', 'RAILWAY_DEPLOYMENT_ID'))
    )
    if is_railway:
        return JsonResponse({'success': True, 'started': False, 'message': 'No Railway não é possível iniciar Docker automaticamente. Crie um serviço Evolution API no Railway e configure EVOLUTION_API_URL/EVOLUTION_API_KEY.'})
    diag = None
    try:
        diag = service.docker_diagnostics()
    except Exception:
        diag = None

    opened = service.start_docker_desktop()
    compose_started = service.start_evolution_compose_async()
    started = bool(opened or compose_started)

    message = 'Abrindo Docker Desktop e iniciando Evolution... aguarde 1–2 minutos e recarregue.'
    if diag and diag.get('message'):
        message = diag.get('message')
        if 'fechado' in message.lower():
            message = message + ' O sistema tentou abrir automaticamente; se não abrir, execute o Docker Desktop como Administrador.'

    return JsonResponse({'success': True, 'started': started, 'message': message})


@login_required
def api_whatsapp_config_save(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

    from .models import WhatsAppMensagemConfig

    tenant = getattr(request, 'tenant', None)
    if not tenant:
        tenant_id = request.session.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                tenant = None
        if not tenant:
            tenant = Tenant.objects.filter(usuario_admin=request.user).first()
            if tenant:
                request.session['tenant_id'] = tenant.id
                request.tenant = tenant
        if not tenant and not request.user.is_superuser:
            if request.FILES.get('anexo'):
                return JsonResponse({'success': False, 'error': 'Anexo requer tenant identificado.'}, status=400)
            tipo = (request.POST.get('tipo') or '').strip()
            mensagem = request.POST.get('mensagem') or ''
            tipos_validos = {'GERAL', 'BOAS_VINDAS', 'COBRANCA_ALUGUEL', 'COBRANCA_IPTU', 'CONTRATO_VENCENDO'}
            if tipo not in tipos_validos:
                return JsonResponse({'success': False, 'error': 'Tipo inválido'}, status=400)
            session_cfg = request.session.get('whatsapp_configs') or {}
            session_cfg[tipo] = mensagem
            request.session['whatsapp_configs'] = session_cfg
            request.session.modified = True
            return JsonResponse({'success': True, 'tipo': tipo, 'anexo_url': None})
    tipo = (request.POST.get('tipo') or '').strip()
    mensagem = request.POST.get('mensagem') or ''
    anexo = request.FILES.get('anexo')

    tipos_validos = {'GERAL', 'BOAS_VINDAS', 'COBRANCA_ALUGUEL', 'COBRANCA_IPTU', 'CONTRATO_VENCENDO'}
    if tipo not in tipos_validos:
        return JsonResponse({'success': False, 'error': 'Tipo inválido'}, status=400)

    try:
        cfg, _ = WhatsAppMensagemConfig.objects.get_or_create(
            tenant=tenant if tenant else None,
            tipo=tipo,
            defaults={'mensagem': mensagem},
        )
        cfg.mensagem = mensagem
        if anexo:
            cfg.anexo = anexo
        cfg.save()
        anexo_url = cfg.anexo.url if cfg.anexo else None
        return JsonResponse({'success': True, 'tipo': tipo, 'anexo_url': anexo_url})
    except Exception:
        if anexo:
            return JsonResponse({'success': False, 'error': 'Anexo indisponível no momento.'}, status=400)
        if tenant:
            cfg = tenant.configuracoes or {}
            wa_cfg = cfg.get('whatsapp_configs') or {}
            wa_cfg[tipo] = mensagem
            cfg['whatsapp_configs'] = wa_cfg
            tenant.configuracoes = cfg
            tenant.save(update_fields=['configuracoes'])
            return JsonResponse({'success': True, 'tipo': tipo, 'anexo_url': None})
        session_cfg = request.session.get('whatsapp_configs') or {}
        session_cfg[tipo] = mensagem
        request.session['whatsapp_configs'] = session_cfg
        request.session.modified = True
        return JsonResponse({'success': True, 'tipo': tipo, 'anexo_url': None})

