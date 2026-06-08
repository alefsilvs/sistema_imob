from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Avg, Sum, F, ExpressionWrapper, DecimalField, DurationField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Inquilino, Proprietario
from .forms import InquilinoForm, ProprietarioForm
from saas.models import Tenant
from datetime import date, timedelta
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

from saas.admin_utils import is_system_admin
from saas.models import VerificacaoEmail

class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser or is_system_admin(request.user) or hasattr(request.user, 'master_profile'):
                return redirect('core:dashboard')
            try:
                verificacao = VerificacaoEmail.objects.filter(usuario=request.user).first()
                if verificacao and not verificacao.email_verificado:
                    logout(request)
            except Exception:
                pass
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if not (user.is_superuser or is_system_admin(user) or hasattr(user, 'master_profile')):
            try:
                verificacao = VerificacaoEmail.objects.filter(usuario=user).first()
                if verificacao and not verificacao.email_verificado:
                    self.request.session['registro_pendente'] = {'user_id': user.id, 'email': user.email}
                    messages.error(self.request, 'Confirme seu e-mail para entrar.')
                    return redirect('saas:email_enviado')
            except Exception:
                pass
        return super().form_valid(form)

def home(request):
    """Página inicial pública; autentica redireciona para dashboard"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    # Renderiza landing page pública
    return render(request, 'core/home.html', {
        'title': 'ImobiPro — Plataforma de Gestão Imobiliária'
    })

@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    tenant = getattr(request, 'tenant', None)
    try:
        from imoveis.models import Imovel
        from contratos.models import Contrato
        from financeiro.models import Parcela, Repasse, IPTU
    except Exception:
        Imovel = None
        Contrato = None
        Parcela = None
        Repasse = None
        IPTU = None

    today = timezone.now().date()
    start_month = date(today.year, today.month, 1)
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)

    imovel_qs = Imovel.objects.none() if not Imovel else Imovel.objects.all()
    contrato_qs = Contrato.objects.none() if not Contrato else Contrato.objects.all()
    inquilino_qs = Inquilino.objects.all()
    parcela_qs = Parcela.objects.none() if not Parcela else Parcela.objects.all()
    repasse_qs = Repasse.objects.none() if not Repasse else Repasse.objects.all()
    iptu_qs = IPTU.objects.none() if not IPTU else IPTU.objects.all()

    if tenant:
        if Imovel:
            imovel_qs = imovel_qs.filter(tenant=tenant)
        if Contrato:
            contrato_qs = contrato_qs.filter(tenant=tenant)
        inquilino_qs = inquilino_qs.filter(tenant=tenant)
        if Parcela:
            parcela_qs = parcela_qs.filter(contrato__tenant=tenant)
        if Repasse:
            repasse_qs = repasse_qs.filter(proprietario__tenant=tenant)
        if IPTU:
            iptu_qs = iptu_qs.filter(imovel__tenant=tenant)
    elif request.user.is_superuser:
        pass
    else:
        imovel_qs = Imovel.objects.none() if Imovel else imovel_qs
        contrato_qs = Contrato.objects.none() if Contrato else contrato_qs
        inquilino_qs = Inquilino.objects.none()
        parcela_qs = Parcela.objects.none() if Parcela else parcela_qs
        repasse_qs = Repasse.objects.none() if Repasse else repasse_qs
        iptu_qs = IPTU.objects.none() if IPTU else iptu_qs

    total_imoveis = imovel_qs.count()
    contratos_vigentes = contrato_qs.filter(status='ATIVO').count() if Contrato else 0
    total_inquilinos = inquilino_qs.count()

    imoveis_ocupados = imovel_qs.filter(status='OCUPADO').count() if Imovel else 0
    imoveis_disponiveis = imovel_qs.filter(status='DISPONIVEL', disponivel=True).count() if Imovel else 0
    taxa_ocupacao = (imoveis_ocupados / total_imoveis * 100) if total_imoveis else 0

    valor_medio_aluguel = imovel_qs.aggregate(v=Avg('valor_aluguel')).get('v') if Imovel else Decimal('0')
    if valor_medio_aluguel is None:
        valor_medio_aluguel = Decimal('0')

    tempo_medio_locacao = 0
    if Contrato:
        dur_expr = ExpressionWrapper(F('data_fim') - F('data_inicio'), output_field=DurationField())
        avg_dur = contrato_qs.filter(status='ATIVO').aggregate(v=Avg(dur_expr)).get('v')
        if avg_dur:
            tempo_medio_locacao = round(avg_dur.days / 30)

    contratos_vencendo_qs = contrato_qs.filter(
        status='ATIVO',
        data_fim__gte=today,
        data_fim__lte=today + timedelta(days=30),
    ).select_related('imovel', 'inquilino').order_by('data_fim')[:10] if Contrato else []
    contratos_vencendo_lista = list(contratos_vencendo_qs) if contratos_vencendo_qs else []
    for contrato in contratos_vencendo_lista:
        contrato.dias_restantes = (contrato.data_fim - today).days

    total_expr = (
        F('valor_aluguel') +
        F('valor_condominio') +
        F('valor_iptu') +
        F('valor_seguro') +
        F('valor_outros') +
        F('valor_multa') +
        F('valor_juros') -
        F('valor_desconto')
    )
    total_expr = ExpressionWrapper(total_expr, output_field=DecimalField(max_digits=12, decimal_places=2))
    zero = Value(Decimal('0.00'), output_field=DecimalField(max_digits=12, decimal_places=2))

    receita_recebida = parcela_qs.filter(
        status='PAGO',
        data_pagamento__gte=start_month,
        data_pagamento__lt=next_month,
    ).aggregate(v=Coalesce(Sum(Coalesce('valor_pago', total_expr)), zero)).get('v') if Parcela else Decimal('0')

    financeiro_a_receber_mes = parcela_qs.filter(
        status__in=['PENDENTE', 'VENCIDO'],
        data_vencimento__gte=start_month,
        data_vencimento__lt=next_month,
    ).aggregate(v=Coalesce(Sum(total_expr), zero)).get('v') if Parcela else Decimal('0')

    valor_inadimplencia = parcela_qs.filter(
        status='PENDENTE',
        data_vencimento__lt=today,
    ).aggregate(v=Coalesce(Sum(total_expr), zero)).get('v') if Parcela else Decimal('0')

    inadimplencia_total = parcela_qs.filter(status='PENDENTE', data_vencimento__lt=today).count() if Parcela else 0

    base_inad_qs = parcela_qs.filter(
        data_vencimento__gte=today - timedelta(days=30),
        data_vencimento__lte=today,
    ).exclude(status='CANCELADO') if Parcela else None
    base_inad_total = base_inad_qs.count() if base_inad_qs is not None else 0
    inadimplencia_percentual = (inadimplencia_total / base_inad_total * 100) if base_inad_total else 0

    parcelas_vencidas = inadimplencia_total

    parcelas_proximas_lista = list(
        parcela_qs.filter(
            status='PENDENTE',
            data_vencimento__gte=today,
            data_vencimento__lte=today + timedelta(days=7),
        ).select_related('contrato', 'contrato__inquilino').order_by('data_vencimento')[:8]
    ) if Parcela else []

    pagamentos_recentes_lista = list(
        parcela_qs.filter(
            status='PAGO',
            data_pagamento__isnull=False,
        ).select_related('contrato', 'contrato__inquilino').order_by('-data_pagamento')[:8]
    ) if Parcela else []

    repasses_pendentes = repasse_qs.filter(status='PENDENTE').count() if Repasse else 0

    iptus_vencendo_qs = iptu_qs.filter(
        status='PENDENTE',
        data_vencimento_vista__gte=today,
        data_vencimento_vista__lte=today + timedelta(days=30),
    ).select_related('imovel').order_by('data_vencimento_vista')[:10] if IPTU else []
    iptus_vencendo_lista = list(iptus_vencendo_qs) if iptus_vencendo_qs else []
    for iptu in iptus_vencendo_lista:
        iptu.dias_restantes = (iptu.data_vencimento_vista - today).days
    iptus_vencendo = len(iptus_vencendo_lista)

    context = {
        'title': 'Dashboard',
        'total_imoveis': total_imoveis,
        'contratos_vigentes': contratos_vigentes,
        'contratos_ativos': contratos_vigentes,
        'total_inquilinos': total_inquilinos,
        'inquilinos_imoveis': total_inquilinos,
        'receita_recebida': receita_recebida,
        'parcelas_vencidas': parcelas_vencidas,
        'inadimplencia_percentual': inadimplencia_percentual,
        'inadimplencia_total': inadimplencia_total,
        'valor_inadimplencia': valor_inadimplencia,
        'taxa_ocupacao': taxa_ocupacao,
        'imoveis_disponiveis': imoveis_disponiveis,
        'valor_medio_aluguel': valor_medio_aluguel,
        'tempo_medio_locacao': tempo_medio_locacao,
        'receita_liquida': receita_recebida,
        'margem_lucro': 0,
        'roi_mensal': 0,
        'despesas_mes': 0,
        'contratos_vencendo_lista': contratos_vencendo_lista,
        'iptus_vencendo': iptus_vencendo,
        'iptus_vencendo_lista': iptus_vencendo_lista,
        'financeiro_recebido_mes': receita_recebida,
        'financeiro_a_receber_mes': financeiro_a_receber_mes,
        'financeiro_em_atraso': valor_inadimplencia,
        'repasses_pendentes': repasses_pendentes,
        'parcelas_proximas_lista': parcelas_proximas_lista,
        'pagamentos_recentes_lista': pagamentos_recentes_lista,
    }
    return render(request, 'core/dashboard.html', context)

@csrf_exempt
@require_POST
def save_editable_changes(request):
    """API para salvar alterações de elementos editáveis"""
    try:
        data = json.loads(request.body)
        element_id = data.get('element_id')
        content = data.get('content')
        element_type = data.get('element_type')
        
        # Log das alterações para auditoria
        logger.info(f"Elemento editado - ID: {element_id}, Tipo: {element_type}, Usuário: {request.user.username}")
        
        return JsonResponse({'success': True, 'message': 'Alterações salvas com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao salvar alterações: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

# ===== VIEWS PARA INQUILINOS =====

@login_required
def listar_inquilinos(request):
    """Lista todos os inquilinos do tenant"""
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

    if tenant:
        inquilinos = Inquilino.objects.filter(tenant=tenant)
    elif request.user.is_superuser:
        inquilinos = Inquilino.objects.all()
    else:
        inquilinos = Inquilino.objects.none()
    
    # Filtros
    tipo_filtro = request.GET.get('tipo')
    search = request.GET.get('search')
    if search:
        inquilinos = inquilinos.filter(
            Q(nome__icontains=search) |
            Q(email__icontains=search) |
            Q(telefone__icontains=search) |
            Q(cpf_cnpj__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(inquilinos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'tipo_filtro': 'imoveis' if tipo_filtro == 'imoveis' else None,
        'titulo': 'Inquilinos' if tipo_filtro != 'imoveis' else 'Inquilinos (Imóveis)',
    }
    return render(request, 'core/inquilinos/listar.html', context)

@login_required
def cadastrar_inquilino(request):
    """Cadastrar novo inquilino"""
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
        messages.error(request, 'Sessão do tenant não encontrada. Faça login novamente.')
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = InquilinoForm(request.POST)
        if form.is_valid():
            inquilino = form.save(commit=False)
            if tenant:
                inquilino.tenant = tenant
            inquilino.save()
            
            # Se for uma requisição AJAX, retorna JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'inquilino': {
                        'id': inquilino.id,
                        'nome': inquilino.nome
                    }
                })
                
            messages.success(request, 'Inquilino cadastrado com sucesso!')
            return redirect('core:listar_inquilinos')
        else:
            # Se for uma requisição AJAX, retorna os erros em JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Erro de validação nos dados informados.',
                    'errors': form.errors.get_json_data()
                })
            messages.error(request, 'Erro ao cadastrar inquilino. Verifique os dados informados.')
    else:
        form = InquilinoForm()
        # Filtrar fiadores por tenant
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['fiador'].queryset = Inquilino.objects.filter(tenant=request.tenant)
    
    return render(request, 'core/inquilinos/form.html', {'form': form, 'title': 'Cadastrar Inquilino'})

@login_required
def detalhes_inquilino(request, pk):
    """Detalhes de um inquilino específico"""
    if hasattr(request, 'tenant') and request.tenant:
        inquilino = get_object_or_404(Inquilino, pk=pk, tenant=request.tenant)
    else:
        inquilino = get_object_or_404(Inquilino, pk=pk)
    
    context = {
        'inquilino': inquilino,
    }
    return render(request, 'core/inquilinos/detalhar.html', context)

@login_required
def editar_inquilino(request, pk):
    """Editar inquilino"""
    if hasattr(request, 'tenant') and request.tenant:
        inquilino = get_object_or_404(Inquilino, pk=pk, tenant=request.tenant)
    else:
        inquilino = get_object_or_404(Inquilino, pk=pk)
    
    if request.method == 'POST':
        form = InquilinoForm(request.POST, instance=inquilino)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inquilino atualizado com sucesso!')
            return redirect('core:detalhes_inquilino', pk=pk)
        else:
            messages.error(request, 'Erro ao atualizar inquilino.')
    else:
        form = InquilinoForm(instance=inquilino)
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['fiador'].queryset = Inquilino.objects.filter(tenant=request.tenant)
    
    context = {
        'form': form,
        'inquilino': inquilino,
        'title': f'Editar Inquilino - {inquilino.nome}',
    }
    return render(request, 'core/inquilinos/form.html', context)

@login_required
def excluir_inquilino(request, pk):
    """Excluir inquilino"""
    if hasattr(request, 'tenant') and request.tenant:
        inquilino = get_object_or_404(Inquilino, pk=pk, tenant=request.tenant)
    else:
        inquilino = get_object_or_404(Inquilino, pk=pk)
    
    if request.method == 'POST':
        inquilino.delete()
        messages.success(request, 'Inquilino excluído com sucesso!')
        return redirect('core:listar_inquilinos')
    
    context = {
        'inquilino': inquilino,
    }
    return render(request, 'core/inquilinos/confirmar_exclusao.html', context)

# ===== VIEWS PARA PROPRIETÁRIOS =====

@login_required
def listar_proprietarios(request):
    """Lista todos os proprietários do tenant"""
    # Filtrar por tenant se disponível
    if hasattr(request, 'tenant') and request.tenant:
        proprietarios = Proprietario.objects.filter(tenant=request.tenant, ativo=True)
    else:
        proprietarios = Proprietario.objects.none()
    
    # Filtros
    search = request.GET.get('search')
    if search:
        proprietarios = proprietarios.filter(
            Q(nome__icontains=search) |
            Q(email__icontains=search) |
            Q(telefone__icontains=search) |
            Q(cpf_cnpj__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(proprietarios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'core/proprietarios/listar.html', context)

@login_required
def cadastrar_proprietario(request):
    """Cadastrar novo proprietário"""
    if request.method == 'POST':
        form = ProprietarioForm(request.POST)
        if form.is_valid():
            proprietario = form.save(commit=False)
            if hasattr(request, 'tenant') and request.tenant:
                proprietario.tenant = request.tenant
            proprietario.save()
            
            # Se for uma requisição AJAX (Cadastro Rápido), retorna JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'proprietario': {
                        'id': proprietario.id,
                        'nome': proprietario.nome
                    }
                })
            
            messages.success(request, 'Proprietário cadastrado com sucesso!')
            return redirect('core:listar_proprietarios')
        else:
            # Se for uma requisição AJAX, retorna os erros em JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Erro de validação nos dados informados.',
                    'errors': form.errors.get_json_data()
                })
            messages.error(request, 'Erro ao cadastrar proprietário.')
    else:
        form = ProprietarioForm()
    
    return render(request, 'core/proprietarios/form.html', {'form': form, 'title': 'Cadastrar Proprietário'})

@login_required
def detalhes_proprietario(request, pk):
    """Detalhes de um proprietário específico"""
    if hasattr(request, 'tenant') and request.tenant:
        proprietario = get_object_or_404(Proprietario, pk=pk, tenant=request.tenant)
    else:
        proprietario = get_object_or_404(Proprietario, pk=pk)
    
    context = {
        'proprietario': proprietario,
    }
    return render(request, 'core/proprietarios/detalhes.html', context)

@login_required
def editar_proprietario(request, pk):
    """Editar proprietário"""
    if hasattr(request, 'tenant') and request.tenant:
        proprietario = get_object_or_404(Proprietario, pk=pk, tenant=request.tenant)
    else:
        proprietario = get_object_or_404(Proprietario, pk=pk)
    
    if request.method == 'POST':
        form = ProprietarioForm(request.POST, instance=proprietario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proprietário atualizado com sucesso!')
            return redirect('core:detalhes_proprietario', pk=pk)
        else:
            messages.error(request, 'Erro ao atualizar proprietário.')
    else:
        form = ProprietarioForm(instance=proprietario)
    
    context = {
        'form': form,
        'proprietario': proprietario,
        'title': f'Editar Proprietário - {proprietario.nome}',
    }
    return render(request, 'core/proprietarios/form.html', context)

@login_required
def excluir_proprietario(request, pk):
    """Excluir proprietário"""
    if hasattr(request, 'tenant') and request.tenant:
        proprietario = get_object_or_404(Proprietario, pk=pk, tenant=request.tenant)
    else:
        proprietario = get_object_or_404(Proprietario, pk=pk)
    
    if request.method == 'POST':
        try:
            proprietario.delete()
            messages.success(request, 'Proprietário excluído com sucesso!')
            return redirect('core:listar_proprietarios')
        except IntegrityError:
            if proprietario.ativo:
                proprietario.ativo = False
                proprietario.save(update_fields=['ativo'])
            messages.warning(
                request,
                'Não foi possível excluir este proprietário porque existem dados vinculados. Ele foi desativado.'
            )
            return redirect('core:listar_proprietarios')
    
    context = {
        'proprietario': proprietario,
    }
    return render(request, 'core/proprietarios/confirmar_exclusao.html', context)

# ===== OUTRAS VIEWS =====

@login_required
def perfil(request):
    """Perfil do usuário"""
    return render(request, 'core/perfil.html')

@login_required
def configuracoes(request):
    """Configurações do sistema"""
    return render(request, 'core/configuracoes.html')

@login_required
def sobre_sistema(request):
    """Página sobre o sistema"""
    return render(request, 'core/sobre_sistema.html')
