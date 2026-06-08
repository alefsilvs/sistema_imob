from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from .models import Imovel, FotoImovel
from .forms import ImovelForm, FotoImovelForm
from core.models import Proprietario
from saas.mixins import TenantViewMixin

@login_required
def listar_imoveis(request):
    # Filtrar por tenant se disponível
    if hasattr(request, 'tenant') and request.tenant:
        imoveis = Imovel.objects.filter(tenant=request.tenant).select_related('proprietario')
    elif request.user.is_superuser:
        # Superusuários veem todos os imóveis se não houver tenant selecionado
        imoveis = Imovel.objects.all().select_related('proprietario', 'tenant')
    else:
        imoveis = Imovel.objects.none()
    
    # Filtros
    search = request.GET.get('search')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    
    if search:
        imoveis = imoveis.filter(
            Q(codigo__icontains=search) |
            Q(endereco__icontains=search) |
            Q(bairro__icontains=search) |
            Q(proprietario__nome__icontains=search)
        )
    
    if tipo:
        imoveis = imoveis.filter(tipo=tipo)
    
    if status:
        imoveis = imoveis.filter(status=status)
    
    # Paginação
    paginator = Paginator(imoveis, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tipos': Imovel.TIPO_CHOICES,
        'status_choices': Imovel.STATUS_CHOICES,
        'search': search,
        'tipo_selected': tipo,
        'status_selected': status,
    }
    
    return render(request, 'imoveis/listar.html', context)

@login_required
def cadastrar_imovel(request):
    if request.method == 'POST':
        form = ImovelForm(request.POST)
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['proprietario'].queryset = Proprietario.objects.filter(tenant=request.tenant, ativo=True)
        if form.is_valid():
            imovel = form.save(commit=False)
            if hasattr(request, 'tenant') and request.tenant:
                imovel.tenant = request.tenant
            imovel.save()
            messages.success(request, f'Imóvel {imovel.codigo} cadastrado com sucesso!')
            return redirect('imoveis:listar')
        else:
            messages.error(request, 'Erro ao cadastrar imóvel. Verifique os dados informados.')
    else:
        form = ImovelForm()
        # Filtrar proprietários por tenant no formulário GET
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['proprietario'].queryset = Proprietario.objects.filter(tenant=request.tenant, ativo=True)
    
    context = {
        'form': form,
        'title': 'Cadastrar Imóvel',
    }
    
    return render(request, 'imoveis/form.html', context)

@login_required
def editar_imovel(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        imovel = get_object_or_404(Imovel, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('imoveis:listar')
    
    if request.method == 'POST':
        form = ImovelForm(request.POST, instance=imovel)
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['proprietario'].queryset = Proprietario.objects.filter(tenant=request.tenant, ativo=True)
        if form.is_valid():
            form.save()
            messages.success(request, f'Imóvel {imovel.codigo} atualizado com sucesso!')
            return redirect('imoveis:listar')
        else:
            messages.error(request, 'Erro ao atualizar imóvel. Verifique os dados informados.')
    else:
        form = ImovelForm(instance=imovel)
        # Filtrar proprietários por tenant no formulário GET
        if hasattr(request, 'tenant') and request.tenant:
            form.fields['proprietario'].queryset = Proprietario.objects.filter(tenant=request.tenant, ativo=True)
    
    context = {
        'form': form,
        'imovel': imovel,
        'title': f'Editar Imóvel - {imovel.codigo}',
    }
    
    return render(request, 'imoveis/form.html', context)

@login_required
def detalhes_imovel(request, pk):
    if hasattr(request, 'tenant') and request.tenant:
        imovel = get_object_or_404(Imovel, pk=pk, tenant=request.tenant)
    elif request.user.is_superuser:
        imovel = get_object_or_404(Imovel, pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('imoveis:listar')
    fotos = imovel.fotos.all()
    
    context = {
        'imovel': imovel,
        'fotos': fotos,
    }
    
    return render(request, 'imoveis/detalhar.html', context)

@login_required
def excluir_imovel(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        imovel = get_object_or_404(Imovel, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('imoveis:listar')
    
    if request.method == 'POST':
        codigo = imovel.codigo
        imovel.delete()
        messages.success(request, f'Imóvel {codigo} excluído com sucesso!')
        return redirect('imoveis:listar')
    
    context = {
        'imovel': imovel,
    }
    
    return render(request, 'imoveis/confirmar_exclusao.html', context)

@login_required
def gerenciar_fotos(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        imovel = get_object_or_404(Imovel, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('imoveis:listar_imoveis')
    
    if request.method == 'POST':
        form = FotoImovelForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.imovel = imovel
            foto.save()
            messages.success(request, 'Foto adicionada com sucesso!')
            return redirect('imoveis:gerenciar_fotos', pk=pk)
    else:
        form = FotoImovelForm()
    
    fotos = imovel.fotos.all()
    
    context = {
        'imovel': imovel,
        'fotos': fotos,
        'form': form,
    }
    
    return render(request, 'imoveis/gerenciar_fotos.html', context)
