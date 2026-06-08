from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import OrdemServico, Fornecedor
from .forms import OrdemServicoForm, FornecedorForm

@login_required
def listar_ordens(request):
    if hasattr(request, 'tenant') and request.tenant:
        ordens = OrdemServico.objects.select_related('imovel', 'fornecedor').filter(imovel__tenant=request.tenant)
    elif request.user.is_superuser:
        ordens = OrdemServico.objects.select_related('imovel', 'fornecedor').all()
    else:
        ordens = OrdemServico.objects.none()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        ordens = ordens.filter(status=status)
    
    responsavel = request.GET.get('responsavel')
    if responsavel:
        ordens = ordens.filter(responsavel_pagamento=responsavel)
    
    search = request.GET.get('search')
    if search:
        ordens = ordens.filter(
            Q(numero__icontains=search) |
            Q(descricao__icontains=search) |
            Q(imovel__endereco__icontains=search)
        )
    
    paginator = Paginator(ordens, 20)
    page = request.GET.get('page')
    ordens = paginator.get_page(page)
    
    context = {
        'ordens': ordens,
        'status_choices': OrdemServico.STATUS_CHOICES,
        'responsavel_choices': OrdemServico.RESPONSAVEL_CHOICES,
    }
    return render(request, 'manutencao/ordens/listar.html', context)

@login_required
def cadastrar_ordem(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST)
        if form.is_valid():
            ordem = form.save()
            messages.success(request, 'Ordem de serviço cadastrada com sucesso!')
            return redirect('manutencao:detalhes_ordem', pk=ordem.pk)
    else:
        form = OrdemServicoForm()
    
    if hasattr(request, 'tenant') and request.tenant:
        form.fields['imovel'].queryset = form.fields['imovel'].queryset.filter(tenant=request.tenant)
        form.fields['contrato'].queryset = form.fields['contrato'].queryset.filter(tenant=request.tenant)
    return render(request, 'manutencao/ordens/form.html', {'form': form})

@login_required
def detalhes_ordem(request, pk):
    if hasattr(request, 'tenant') and request.tenant:
        ordem = get_object_or_404(OrdemServico, pk=pk, imovel__tenant=request.tenant)
    elif request.user.is_superuser:
        ordem = get_object_or_404(OrdemServico, pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('manutencao:listar_ordens')
    return render(request, 'manutencao/ordens/detalhar.html', {'ordem': ordem})

@login_required
def editar_ordem(request, pk):
    if hasattr(request, 'tenant') and request.tenant:
        ordem = get_object_or_404(OrdemServico, pk=pk, imovel__tenant=request.tenant)
    elif request.user.is_superuser:
        ordem = get_object_or_404(OrdemServico, pk=pk)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('manutencao:listar_ordens')
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=ordem)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ordem de serviço atualizada com sucesso!')
            return redirect('manutencao:detalhes_ordem', pk=pk)
    else:
        form = OrdemServicoForm(instance=ordem)
    if hasattr(request, 'tenant') and request.tenant:
        form.fields['imovel'].queryset = form.fields['imovel'].queryset.filter(tenant=request.tenant)
        form.fields['contrato'].queryset = form.fields['contrato'].queryset.filter(tenant=request.tenant)
    return render(request, 'manutencao/ordens/form.html', {'form': form, 'ordem': ordem})

@login_required
def listar_fornecedores(request):
    fornecedores = Fornecedor.objects.filter(ativo=True)
    
    search = request.GET.get('search')
    if search:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search) |
            Q(cnpj__icontains=search) |
            Q(especialidade__icontains=search)
        )
    
    paginator = Paginator(fornecedores, 20)
    page = request.GET.get('page')
    fornecedores = paginator.get_page(page)
    
    return render(request, 'manutencao/fornecedores/listar.html', {'fornecedores': fornecedores})

@login_required
def cadastrar_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, 'Fornecedor cadastrado com sucesso!')
            return redirect('manutencao:listar_fornecedores')
    else:
        form = FornecedorForm()
    
    return render(request, 'manutencao/fornecedores/form.html', {'form': form})
