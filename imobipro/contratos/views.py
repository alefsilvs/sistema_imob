from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Contrato, ReajusteContrato
from .forms import ContratoForm, ReajusteForm
from saas.mixins import TenantViewMixin
from saas.models import Tenant
from django.db import IntegrityError

def _resolve_tenant(request):
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return tenant

    tenant_id = None
    try:
        tenant_id = request.session.get('tenant_id')
    except Exception:
        tenant_id = None

    if tenant_id:
        try:
            tenant = Tenant.objects.select_related('plano').filter(id=tenant_id).first()
        except Exception:
            tenant = None
        if tenant:
            request.tenant = tenant
            return tenant

    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        try:
            if getattr(user, 'is_superuser', False):
                tenant = Tenant.objects.select_related('plano').filter(usuario_admin=user).first() or Tenant.objects.select_related('plano').first()
            else:
                tenant = Tenant.objects.select_related('plano').filter(usuario_admin=user).first()
        except Exception:
            tenant = None

        if tenant:
            try:
                request.session['tenant_id'] = tenant.id
                request.session.modified = True
            except Exception:
                pass
            request.tenant = tenant
            return tenant

    return None

@login_required
def listar_contratos(request):
    # Filtrar por tenant se disponível
    tenant = _resolve_tenant(request)
    if not tenant:
        messages.error(request, 'Tenant não identificado. Crie sua empresa para continuar.')
        return redirect('saas:registro')
    if tenant:
        tenant_q = (
            Q(tenant=tenant)
            | Q(tenant__isnull=True, imovel__tenant=tenant)
            | Q(tenant__isnull=True, inquilino__tenant=tenant)
        )
        contratos = Contrato.objects.filter(tenant_q).select_related('imovel', 'inquilino')
    else:
        contratos = Contrato.objects.none()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        contratos = contratos.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        contratos = contratos.filter(
            Q(numero__icontains=search) |
            Q(inquilino__nome__icontains=search) |
            Q(imovel__endereco__icontains=search)
        )
    
    paginator = Paginator(contratos, 20)
    page = request.GET.get('page')
    contratos = paginator.get_page(page)
    
    context = {
        'contratos': contratos,
        'status_choices': Contrato.STATUS_CHOICES,
    }
    return render(request, 'contratos/listar.html', context)

@login_required
def cadastrar_contrato(request):
    tenant = _resolve_tenant(request)
    if not tenant and not getattr(request.user, 'is_superuser', False):
        messages.error(request, 'Tenant não identificado. Faça login novamente.')
        return redirect('contratos:listar')

    if request.method == 'POST':
        form = ContratoForm(request.POST)
        if tenant:
            from imoveis.models import Imovel
            from core.models import Inquilino
            form.fields['imovel'].queryset = Imovel.objects.filter(tenant=tenant)
            form.fields['inquilino'].queryset = Inquilino.objects.filter(tenant=tenant)
        if form.is_valid():
            contrato = form.save(commit=False)
            if tenant:
                contrato.tenant = tenant
            try:
                contrato.save()
            except IntegrityError:
                form.add_error('numero', 'Já existe um contrato com este número.')
                return render(request, 'contratos/cadastrar.html', {'form': form})
            messages.success(request, 'Contrato cadastrado com sucesso!')
            return redirect('contratos:detalhar', pk=contrato.pk)
    else:
        form = ContratoForm()
        if tenant:
            from imoveis.models import Imovel
            from core.models import Inquilino
            form.fields['imovel'].queryset = Imovel.objects.filter(tenant=tenant)
            form.fields['inquilino'].queryset = Inquilino.objects.filter(tenant=tenant)

    return render(request, 'contratos/cadastrar.html', {'form': form})

@login_required
def detalhes_contrato(request, pk):
    tenant = _resolve_tenant(request)
    if tenant:
        tenant_q = (
            Q(tenant=tenant)
            | Q(tenant__isnull=True, imovel__tenant=tenant)
            | Q(tenant__isnull=True, inquilino__tenant=tenant)
        )
        contrato = get_object_or_404(Contrato.objects.filter(tenant_q), pk=pk)
    elif getattr(request.user, 'is_superuser', False):
        contrato = get_object_or_404(Contrato, pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('contratos:listar')
    reajustes = contrato.reajustes.all()[:5]
    parcelas = contrato.parcelas.all()[:10]
    
    return render(request, 'contratos/detalhar.html', {
        'contrato': contrato,
        'reajustes': reajustes,
        'parcelas': parcelas
    })

@login_required
def editar_contrato(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    tenant = _resolve_tenant(request)
    if tenant:
        tenant_q = (
            Q(tenant=tenant)
            | Q(tenant__isnull=True, imovel__tenant=tenant)
            | Q(tenant__isnull=True, inquilino__tenant=tenant)
        )
        contrato = get_object_or_404(Contrato.objects.filter(tenant_q), pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('contratos:listar_contratos')
    if request.method == 'POST':
        form = ContratoForm(request.POST, instance=contrato)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error('numero', 'Já existe um contrato com este número.')
                return render(request, 'contratos/editar.html', {'form': form, 'contrato': contrato})
            messages.success(request, 'Contrato atualizado com sucesso!')
            return redirect('contratos:detalhar', pk=pk)
    else:
        form = ContratoForm(instance=contrato)
        if tenant:
            from imoveis.models import Imovel
            from core.models import Inquilino
            form.fields['imovel'].queryset = Imovel.objects.filter(tenant=tenant)
            form.fields['inquilino'].queryset = Inquilino.objects.filter(tenant=tenant)

    return render(request, 'contratos/editar.html', {'form': form, 'contrato': contrato})

@login_required
def excluir_contrato(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    tenant = _resolve_tenant(request)
    if tenant:
        tenant_q = (
            Q(tenant=tenant)
            | Q(tenant__isnull=True, imovel__tenant=tenant)
            | Q(tenant__isnull=True, inquilino__tenant=tenant)
        )
        contrato = get_object_or_404(Contrato.objects.filter(tenant_q), pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('contratos:listar_contratos')

    if request.method == 'POST':
        try:
            parcelas_count = contrato.parcelas.count()
            reajustes_count = contrato.reajustes.count()

            if parcelas_count > 0 or reajustes_count > 0:
                messages.warning(
                    request,
                    f'Atenção: O contrato {contrato.numero} possui {parcelas_count} parcelas e {reajustes_count} reajustes associados que também serão excluídos.'
                )

            numero = contrato.numero
            contrato.delete()
            messages.success(request, f'Contrato {numero} excluído com sucesso!')
            return redirect('contratos:listar')

        except Exception as e:
            messages.error(request, f'Erro ao excluir contrato: {str(e)}')
            return redirect('contratos:detalhar', pk=pk)

    parcelas_count = contrato.parcelas.count()
    reajustes_count = contrato.reajustes.count()

    context = {
        'contrato': contrato,
        'parcelas_count': parcelas_count,
        'reajustes_count': reajustes_count,
    }

    return render(request, 'contratos/confirmar_exclusao.html', context)

@login_required
def listar_reajustes(request):
    reajustes = ReajusteContrato.objects.select_related('contrato').all()
    
    paginator = Paginator(reajustes, 20)
    page = request.GET.get('page')
    reajustes = paginator.get_page(page)
    
    return render(request, 'contratos/reajustes/listar.html', {'reajustes': reajustes})

@login_required
def cadastrar_reajuste(request, contrato_pk):
    # Filtrar por tenant para evitar vazamento de dados
    tenant = _resolve_tenant(request)
    if tenant:
        tenant_q = (
            Q(tenant=tenant)
            | Q(tenant__isnull=True, imovel__tenant=tenant)
            | Q(tenant__isnull=True, inquilino__tenant=tenant)
        )
        contrato = get_object_or_404(Contrato.objects.filter(tenant_q), pk=contrato_pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('contratos:listar_contratos')

    if request.method == 'POST':
        form = ReajusteForm(request.POST)
        if form.is_valid():
            reajuste = form.save(commit=False)
            reajuste.contrato = contrato
            reajuste.save()
            messages.success(request, 'Reajuste cadastrado com sucesso!')
            return redirect('contratos:detalhar', pk=contrato.pk)
    else:
        form = ReajusteForm()

    return render(request, 'contratos/reajustes/cadastrar.html', {
        'form': form,
        'contrato': contrato
    })
