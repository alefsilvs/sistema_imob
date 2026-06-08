from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import json
import uuid

from .models import PlanoAssinatura, AssinaturaUsuario, HistoricoPagamento, ConfiguracaoSistema, PagamentoAssinatura
from .pagamento_service import PagamentoService

def planos_assinatura(request):
    """
    Exibe os planos de assinatura disponíveis
    """
    planos = PlanoAssinatura.objects.filter(ativo=True).order_by('preco')
    
    # Verificar se o usuário já tem assinatura
    assinatura_atual = None
    if request.user.is_authenticated:
        try:
            assinatura_atual = AssinaturaUsuario.objects.get(usuario=request.user)
        except AssinaturaUsuario.DoesNotExist:
            pass
    
    context = {
        'planos': planos,
        'assinatura_atual': assinatura_atual,
    }
    
    return render(request, 'assinaturas/planos.html', context)

@login_required
def assinar_plano(request, plano_id):
    """
    Inicia o processo de assinatura de um plano
    """
    plano = get_object_or_404(PlanoAssinatura, id=plano_id, ativo=True)
    
    # Verificar se o usuário já tem assinatura
    try:
        assinatura_atual = AssinaturaUsuario.objects.get(usuario=request.user)
        if assinatura_atual.esta_ativa:
            messages.warning(request, 'Você já possui uma assinatura ativa.')
            return redirect('assinaturas:minha_assinatura')
    except AssinaturaUsuario.DoesNotExist:
        pass
    
    if request.method == 'POST':
        metodo_pagamento = request.POST.get('metodo_pagamento', 'PIX')
        
        # Verificar se é plano gratuito
        if plano.preco == 0:
            # Plano gratuito - ativar diretamente
            if hasattr(request.user, 'assinatura'):
                assinatura = request.user.assinatura
                assinatura.plano = plano
                assinatura.renovar()
                assinatura.valor_pago = 0
                assinatura.forma_pagamento = 'Gratuito'
                assinatura.status = 'ATIVA'
                assinatura.save()
            else:
                assinatura = AssinaturaUsuario.objects.create(
                    usuario=request.user,
                    plano=plano,
                    valor_pago=0,
                    forma_pagamento='Gratuito',
                    status='ATIVA'
                )
            
            # Criar registro de pagamento gratuito
            HistoricoPagamento.objects.create(
                assinatura=assinatura,
                valor=0,
                forma_pagamento='Gratuito',
                status='APROVADO',
                data_pagamento=timezone.now(),
                data_vencimento=timezone.now() + timezone.timedelta(days=30),
                referencia_externa=str(uuid.uuid4())
            )
            
            messages.success(request, 'Plano gratuito ativado com sucesso! Aproveite seus 7 dias.')
            return redirect('core:dashboard')
        
        else:
            # Plano pago - verificar se forma de pagamento foi selecionada
            if not metodo_pagamento or metodo_pagamento.strip() == '':
                messages.error(request, 'Por favor, selecione uma forma de pagamento.')
                return render(request, 'assinaturas/confirmar_assinatura.html', {'plano': plano})
            
            # Criar nova assinatura
            if hasattr(request.user, 'assinatura'):
                assinatura = request.user.assinatura
                assinatura.plano = plano
                assinatura.renovar()
                assinatura.valor_pago = plano.preco
                assinatura.forma_pagamento = 'Pendente'
                assinatura.save()
            else:
                assinatura = AssinaturaUsuario.objects.create(
                    usuario=request.user,
                    plano=plano,
                    valor_pago=plano.preco,
                    forma_pagamento='Pendente'
                )
            
            # Criar registro de pagamento
            pagamento = HistoricoPagamento.objects.create(
                assinatura=assinatura,
                valor=plano.preco,
                forma_pagamento=metodo_pagamento.upper(),
                data_vencimento=timezone.now() + timezone.timedelta(days=1),
                referencia_externa=str(uuid.uuid4())
            )
            
            return redirect('assinaturas:pagamento', pagamento_id=pagamento.id)
    
    context = {
        'plano': plano,
    }
    
    return render(request, 'assinaturas/confirmar_assinatura.html', context)

@login_required
def pagamento(request, pagamento_id):
    """
    Página de pagamento
    """
    pagamento = get_object_or_404(HistoricoPagamento, id=pagamento_id, assinatura__usuario=request.user)
    
    # Usar o serviço de pagamento para gerar dados do PIX
    pix_data = PagamentoService.gerar_pix_qrcode(
        valor=float(pagamento.valor),
        descricao=f"Assinatura {pagamento.assinatura.plano.nome} - ImobilPro"
    )
    
    context = {
        'pagamento': pagamento,
        'pix_data': pix_data,
    }
    
    return render(request, 'assinaturas/pagamento.html', context)

@csrf_exempt
@require_POST
def webhook_pagamento(request):
    """
    Webhook para receber confirmações de pagamento
    """
    try:
        data = json.loads(request.body)
        
        # Usar o serviço de pagamento para processar webhook
        pagamento = PagamentoService.processar_webhook_pagamento(data)
        
        if pagamento:
            return JsonResponse({
                'status': 'success',
                'pagamento_id': pagamento.id,
                'status_pagamento': pagamento.status
            })
        else:
            return JsonResponse({
                'status': 'error', 
                'message': 'Pagamento não encontrado'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'JSON inválido'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        })

@login_required
def confirmar_pagamento(request, pagamento_id):
    """
    Simula confirmação manual de pagamento (para testes)
    """
    pagamento = get_object_or_404(HistoricoPagamento, id=pagamento_id, assinatura__usuario=request.user)
    
    if pagamento.status == 'PENDENTE':
        pagamento.status = 'APROVADO'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()
        
        # Ativar assinatura
        assinatura = pagamento.assinatura
        assinatura.status = 'ATIVA'
        assinatura.forma_pagamento = 'PIX'
        assinatura.save()
        
        messages.success(request, 'Pagamento confirmado! Sua assinatura está ativa.')
        return redirect('core:dashboard')
    
    messages.error(request, 'Pagamento já foi processado.')
    return redirect('assinaturas:minha_assinatura')

@login_required
def minha_assinatura(request):
    """
    Exibe informações da assinatura do usuário
    """
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        
        # Verificar se a assinatura está próxima do vencimento
        dias_restantes = (assinatura.data_fim - timezone.now().date()).days
        alerta_vencimento = dias_restantes <= 7
        
        context = {
            'assinatura': assinatura,
            'dias_restantes': dias_restantes,
            'alerta_vencimento': alerta_vencimento
        }
        
    except AssinaturaUsuario.DoesNotExist:
        context = {
            'assinatura': None,
            'planos_disponiveis': PlanoAssinatura.objects.filter(ativo=True)
        }
    
    return render(request, 'assinaturas/minha_assinatura.html', context)

def bloqueio_acesso(request):
    """
    Página de bloqueio para usuários sem assinatura ativa
    """
    config = ConfiguracaoSistema.objects.first()
    assinatura_atual = None
    
    if request.user.is_authenticated:
        try:
            assinatura_atual = AssinaturaUsuario.objects.filter(
                usuario=request.user
            ).order_by('-data_fim').first()
        except AssinaturaUsuario.DoesNotExist:
            pass
    
    context = {
        'config': config,
        'assinatura_atual': assinatura_atual
    }
    
    return render(request, 'assinaturas/bloqueio.html', context)

@login_required
def upgrade_plano(request):
    """
    Página de upgrade de planos
    """
    planos = PlanoAssinatura.objects.filter(ativo=True).order_by('preco')
    assinatura_atual = None
    
    try:
        assinatura_atual = AssinaturaUsuario.objects.get(
            usuario=request.user,
            status='ATIVA'
        )
    except AssinaturaUsuario.DoesNotExist:
        pass
    
    context = {
        'planos': planos,
        'assinatura_atual': assinatura_atual
    }
    
    return render(request, 'assinaturas/upgrade.html', context)

@login_required
def cancelar_assinatura(request):
    """
    Cancela a assinatura do usuário
    """
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        
        if request.method == 'POST':
            motivo = request.POST.get('motivo', '')
            assinatura.cancelar(motivo)
            messages.success(request, 'Assinatura cancelada com sucesso.')
            return redirect('assinaturas:planos')
        
        context = {'assinatura': assinatura}
        return render(request, 'assinaturas/cancelar_assinatura.html', context)
    
    except AssinaturaUsuario.DoesNotExist:
        messages.error(request, 'Você não possui assinatura ativa.')
        return redirect('assinaturas:planos')

def acesso_bloqueado(request):
    """
    Página exibida quando o acesso está bloqueado
    """
    config = ConfiguracaoSistema.objects.first()
    planos = PlanoAssinatura.objects.filter(ativo=True).order_by('preco')
    
    assinatura = None
    if request.user.is_authenticated:
        try:
            assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        except AssinaturaUsuario.DoesNotExist:
            pass
    
    context = {
        'config': config,
        'planos': planos,
        'assinatura': assinatura,
    }
    
    return render(request, 'assinaturas/bloqueado.html', context)

@login_required
def renovar_assinatura(request):
    """
    Renova a assinatura atual ou permite escolher novo plano
    """
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        
        if request.method == 'POST':
            novo_plano_id = request.POST.get('plano_id')
            if novo_plano_id:
                novo_plano = get_object_or_404(PlanoAssinatura, id=novo_plano_id, ativo=True)
                return redirect('assinaturas:assinar', plano_id=novo_plano.id)
            else:
                # Renovar com o mesmo plano
                return redirect('assinaturas:assinar', plano_id=assinatura.plano.id)
        
        planos = PlanoAssinatura.objects.filter(ativo=True).order_by('preco')
        
        context = {
            'assinatura': assinatura,
            'planos': planos,
        }
        
        return render(request, 'assinaturas/renovar.html', context)
    
    except AssinaturaUsuario.DoesNotExist:
        messages.error(request, 'Você não possui assinatura.')
        return redirect('assinaturas:planos')

@login_required
def historico_pagamentos(request):
    """
    Exibe o histórico de pagamentos do usuário
    """
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        pagamentos = HistoricoPagamento.objects.filter(assinatura=assinatura).order_by('-created_at')
    except AssinaturaUsuario.DoesNotExist:
        pagamentos = []
    
    context = {
        'pagamentos': pagamentos,
    }
    
    return render(request, 'assinaturas/historico_pagamentos.html', context)

# ===== VIEWS ESPECÍFICAS PARA PAGAMENTOS DE ASSINATURA =====

@login_required
def criar_pagamento_assinatura(request, plano_id):
    """
    Cria um novo pagamento de assinatura usando o modelo PagamentoAssinatura
    """
    plano = get_object_or_404(PlanoAssinatura, id=plano_id, ativo=True)
    
    # Verificar se o usuário já tem assinatura
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        tipo_pagamento = 'RENOVACAO' if assinatura.esta_ativa else 'ASSINATURA_NOVA'
    except AssinaturaUsuario.DoesNotExist:
        # Criar nova assinatura
        assinatura = AssinaturaUsuario.objects.create(
            usuario=request.user,
            plano=plano,
            status='TRIAL' if plano.is_trial else 'ATIVA',
            valor_pago=plano.preco
        )
        tipo_pagamento = 'ASSINATURA_NOVA'
    
    if request.method == 'POST':
        metodo_pagamento = request.POST.get('metodo_pagamento', 'PIX')
        
        # Calcular período de cobertura
        periodo_inicio = timezone.now()
        if plano.duracao_dias > 0:
            periodo_fim = periodo_inicio + timedelta(days=plano.duracao_dias)
        else:
            periodo_fim = periodo_inicio + timedelta(days=36500)  # Vitalício
        
        # Criar pagamento de assinatura
        pagamento_assinatura = PagamentoAssinatura.objects.create(
            assinatura=assinatura,
            plano=plano,
            valor_original=plano.preco,
            metodo_pagamento=metodo_pagamento,
            tipo_pagamento=tipo_pagamento,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            nome_pagador=request.user.get_full_name() or request.user.username,
            email_pagador=request.user.email,
            ip_origem=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return redirect('assinaturas:processar_pagamento_assinatura', token=pagamento_assinatura.token_pagamento)
    
    context = {
        'plano': plano,
        'assinatura': assinatura if 'assinatura' in locals() else None,
        'tipo_pagamento': tipo_pagamento if 'tipo_pagamento' in locals() else 'ASSINATURA_NOVA'
    }
    
    return render(request, 'assinaturas/criar_pagamento.html', context)

@login_required
def processar_pagamento_assinatura(request, token):
    """
    Processa o pagamento de assinatura
    """
    pagamento = get_object_or_404(PagamentoAssinatura, token_pagamento=token, assinatura__usuario=request.user)
    
    if pagamento.esta_expirado:
        messages.error(request, 'Este pagamento expirou. Inicie um novo processo de pagamento.')
        return redirect('assinaturas:planos')
    
    if pagamento.status != 'PENDENTE':
        messages.info(request, f'Este pagamento já foi processado. Status: {pagamento.get_status_display()}')
        return redirect('assinaturas:minha_assinatura')
    
    # Gerar dados do PIX se for o método escolhido
    pix_data = None
    if pagamento.metodo_pagamento == 'PIX':
        try:
            pix_data = PagamentoService.gerar_pix_qrcode(
                valor=float(pagamento.valor_final),
                descricao=f"Assinatura {pagamento.plano.nome} - {pagamento.get_tipo_pagamento_display()}"
            )
        except Exception as e:
            messages.error(request, f'Erro ao gerar PIX: {str(e)}')
    
    context = {
        'pagamento': pagamento,
        'pix_data': pix_data,
    }
    
    return render(request, 'assinaturas/processar_pagamento.html', context)

@csrf_exempt
@require_POST
def webhook_pagamento_assinatura(request):
    """
    Webhook específico para pagamentos de assinatura
    """
    try:
        data = json.loads(request.body)
        token_pagamento = data.get('token_pagamento')
        status = data.get('status')
        transaction_id = data.get('transaction_id')
        
        if not token_pagamento:
            return JsonResponse({'status': 'error', 'message': 'Token de pagamento não fornecido'})
        
        try:
            pagamento = PagamentoAssinatura.objects.get(token_pagamento=token_pagamento)
        except PagamentoAssinatura.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Pagamento não encontrado'})
        
        if status == 'APROVADO' and pagamento.status == 'PENDENTE':
            pagamento.marcar_como_pago(
                transaction_id=transaction_id,
                gateway_response=data
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Pagamento aprovado e assinatura ativada',
                'pagamento_id': str(pagamento.id)
            })
        
        elif status in ['REJEITADO', 'CANCELADO']:
            pagamento.status = status
            pagamento.ultimo_erro = data.get('erro', 'Pagamento rejeitado/cancelado')
            pagamento.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Status atualizado para {status}'
            })
        
        return JsonResponse({'status': 'info', 'message': 'Nenhuma ação necessária'})
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def confirmar_pagamento_assinatura(request, token):
    """
    Confirmação manual de pagamento de assinatura (para testes)
    """
    pagamento = get_object_or_404(PagamentoAssinatura, token_pagamento=token, assinatura__usuario=request.user)
    
    if pagamento.status == 'PENDENTE':
        pagamento.marcar_como_pago()
        messages.success(request, 'Pagamento confirmado! Sua assinatura foi ativada/renovada.')
    else:
        messages.info(request, f'Pagamento já processado. Status: {pagamento.get_status_display()}')
    
    return redirect('assinaturas:minha_assinatura')

@login_required
def listar_pagamentos_assinatura(request):
    """
    Lista todos os pagamentos de assinatura do usuário
    """
    try:
        assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
        pagamentos = PagamentoAssinatura.objects.filter(assinatura=assinatura).order_by('-created_at')
    except AssinaturaUsuario.DoesNotExist:
        pagamentos = PagamentoAssinatura.objects.none()
    
    context = {
        'pagamentos': pagamentos,
    }
    
    return render(request, 'assinaturas/listar_pagamentos.html', context)

@login_required
def relatorio_pagamentos_assinatura(request):
    """
    Relatório detalhado de pagamentos de assinatura (apenas para staff)
    """
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('core:dashboard')
    
    # Filtros
    status_filtro = request.GET.get('status', '')
    metodo_filtro = request.GET.get('metodo', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    pagamentos = PagamentoAssinatura.objects.all().order_by('-created_at')
    
    if status_filtro:
        pagamentos = pagamentos.filter(status=status_filtro)
    
    if metodo_filtro:
        pagamentos = pagamentos.filter(metodo_pagamento=metodo_filtro)
    
    if data_inicio:
        pagamentos = pagamentos.filter(data_criacao__date__gte=data_inicio)
    
    if data_fim:
        pagamentos = pagamentos.filter(data_criacao__date__lte=data_fim)
    
    # Estatísticas
    total_pagamentos = pagamentos.count()
    total_aprovados = pagamentos.filter(status='APROVADO').count()
    total_pendentes = pagamentos.filter(status='PENDENTE').count()
    valor_total = sum(p.valor_pago or 0 for p in pagamentos.filter(status='APROVADO'))
    
    context = {
        'pagamentos': pagamentos[:100],  # Limitar a 100 registros
        'total_pagamentos': total_pagamentos,
        'total_aprovados': total_aprovados,
        'total_pendentes': total_pendentes,
        'valor_total': valor_total,
        'status_choices': PagamentoAssinatura.STATUS_CHOICES,
        'metodo_choices': PagamentoAssinatura.METODO_CHOICES,
        'filtros': {
            'status': status_filtro,
            'metodo': metodo_filtro,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'assinaturas/relatorio_pagamentos.html', context)
