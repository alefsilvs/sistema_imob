from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Parcela, IPTU, ParcelaIPTU, Seguro, ParcelaSeguro, Repasse, NotaFiscal, Sangria
from .forms import IPTUForm, SeguroForm, ParcelaForm, SangriaForm, SangriaFiltroForm
from imoveis.models import Imovel
from .services import NFEService, NFEServiceException
from .utils import requer_confirmacao_senha

# Views para Parcelas
@login_required
def listar_parcelas(request):
    parcelas = Parcela.objects.select_related('contrato', 'contrato__imovel', 'contrato__inquilino').all()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        parcelas = parcelas.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        parcelas = parcelas.filter(
            Q(contrato__numero__icontains=search) |
            Q(contrato__inquilino__nome__icontains=search)
        )
    
    paginator = Paginator(parcelas, 20)
    page = request.GET.get('page')
    parcelas = paginator.get_page(page)
    
    context = {
        'parcelas': parcelas,
        'status_choices': Parcela.STATUS_CHOICES,
    }
    return render(request, 'financeiro/parcelas/listar.html', context)

@login_required
def detalhes_parcela(request, pk):
    parcela = get_object_or_404(Parcela, pk=pk)
    
    # Buscar notas fiscais relacionadas à parcela
    notas_fiscais = parcela.notafiscal_set.all()
    
    context = {
        'parcela': parcela,
        'notas_fiscais': notas_fiscais,
    }
    return render(request, 'financeiro/parcelas/detalhar.html', context)

@login_required
def editar_parcela(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        parcela = get_object_or_404(Parcela, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_parcelas')
    
    if request.method == 'POST':
        form = ParcelaForm(request.POST, instance=parcela)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parcela editada com sucesso!')
            return redirect('financeiro:detalhes_parcela', pk=pk)
    else:
        form = ParcelaForm(instance=parcela)
    
    return render(request, 'financeiro/parcelas/editar.html', {'form': form, 'parcela': parcela})

@login_required
def marcar_pago(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        parcela = get_object_or_404(Parcela, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_parcelas')
    
    if request.method == 'POST':
        parcela.status = 'PAGO'
        parcela.data_pagamento = timezone.now().date()
        parcela.valor_pago = parcela.valor_total
        parcela.save()
        messages.success(request, 'Parcela marcada como paga com sucesso!')
    
    return redirect('financeiro:listar_parcelas')

# Views para IPTU
@login_required
def listar_iptus(request):
    iptus = IPTU.objects.select_related('imovel').all()
    
    # Filtros
    ano = request.GET.get('ano')
    if ano:
        iptus = iptus.filter(ano_exercicio=ano)
    
    status = request.GET.get('status')
    if status:
        iptus = iptus.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        iptus = iptus.filter(
            Q(imovel__endereco__icontains=search) |
            Q(imovel__codigo__icontains=search)
        )
    
    paginator = Paginator(iptus, 20)
    page = request.GET.get('page')
    iptus = paginator.get_page(page)
    
    # Anos disponíveis para filtro
    anos = IPTU.objects.values_list('ano_exercicio', flat=True).distinct().order_by('-ano_exercicio')
    
    context = {
        'iptus': iptus,
        'anos': anos,
        'status_choices': IPTU.STATUS_CHOICES,
    }
    return render(request, 'financeiro/iptu/listar.html', context)

@login_required
def cadastrar_iptu(request):
    if request.method == 'POST':
        form = IPTUForm(request.POST)
        if form.is_valid():
            iptu = form.save()
            messages.success(request, 'IPTU cadastrado com sucesso!')
            return redirect('financeiro:detalhes_iptu', pk=iptu.pk)
    else:
        form = IPTUForm()
    
    return render(request, 'financeiro/iptu/cadastrar.html', {'form': form})

@login_required
def detalhes_iptu(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        iptu = get_object_or_404(IPTU, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_iptu')
    parcelas = iptu.parcelas_iptu.all()
    return render(request, 'financeiro/iptu/detalhar.html', {
        'iptu': iptu,
        'parcelas': parcelas
    })

@login_required
def editar_iptu(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        iptu = get_object_or_404(IPTU, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_iptu')
    if request.method == 'POST':
        form = IPTUForm(request.POST, instance=iptu)
        if form.is_valid():
            form.save()
            messages.success(request, 'IPTU atualizado com sucesso!')
            return redirect('financeiro:detalhes_iptu', pk=pk)
    else:
        form = IPTUForm(instance=iptu)
    
    return render(request, 'financeiro/iptu/editar.html', {'form': form, 'iptu': iptu})

@login_required
def excluir_iptu(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        iptu = get_object_or_404(IPTU, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_iptu')
    
    if request.method == 'POST':
        # Excluir todas as parcelas relacionadas primeiro
        iptu.parcelas_iptu.all().delete()
        # Excluir o IPTU
        iptu.delete()
        messages.success(request, 'IPTU excluído com sucesso!')
        return redirect('financeiro:listar_iptus')
    
    return render(request, 'financeiro/iptu/excluir.html', {'iptu': iptu})

# Views para Seguros
@login_required
def listar_seguros(request):
    seguros = Seguro.objects.select_related('imovel', 'contrato').all()
    
    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        seguros = seguros.filter(tipo_seguro=tipo)
    
    status = request.GET.get('status')
    if status:
        seguros = seguros.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        seguros = seguros.filter(
            Q(numero_apolice__icontains=search) |
            Q(seguradora__icontains=search) |
            Q(imovel__endereco__icontains=search)
        )
    
    paginator = Paginator(seguros, 20)
    page = request.GET.get('page')
    seguros = paginator.get_page(page)
    
    context = {
        'seguros': seguros,
        'tipo_choices': Seguro.TIPO_CHOICES,
        'status_choices': Seguro.STATUS_CHOICES,
    }
    return render(request, 'financeiro/seguro/listar.html', context)

@login_required
def cadastrar_seguro(request):
    if request.method == 'POST':
        form = SeguroForm(request.POST)
        if form.is_valid():
            seguro = form.save()
            messages.success(request, 'Seguro cadastrado com sucesso!')
            return redirect('financeiro:detalhes_seguro', pk=seguro.pk)
    else:
        form = SeguroForm()
    
    return render(request, 'financeiro/seguro/cadastrar.html', {'form': form})

@login_required
def detalhes_seguro(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        seguro = get_object_or_404(Seguro, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_seguros')
    parcelas = seguro.parcelas_seguro.all()
    return render(request, 'financeiro/seguro/detalhar.html', {
        'seguro': seguro,
        'parcelas': parcelas
    })

@login_required
def editar_seguro(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        seguro = get_object_or_404(Seguro, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_seguros')
    if request.method == 'POST':
        form = SeguroForm(request.POST, instance=seguro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seguro atualizado com sucesso!')
            return redirect('financeiro:detalhes_seguro', pk=pk)
    else:
        form = SeguroForm(instance=seguro)
    
    return render(request, 'financeiro/seguro/editar.html', {'form': form, 'seguro': seguro})

# Views para Repasses
@login_required
def listar_repasses(request):
    repasses = Repasse.objects.select_related('proprietario', 'parcela').all()
    
    paginator = Paginator(repasses, 20)
    page = request.GET.get('page')
    repasses = paginator.get_page(page)
    
    return render(request, 'financeiro/repasses/listar.html', {'repasses': repasses})

# Views para Boletos
@login_required
def gerar_boletos(request):
    # Implementar lógica de geração de boletos
    return render(request, 'financeiro/boletos/gerar.html')

# Views para Relatórios
@login_required
def relatorios_iptu(request):
    ano_atual = timezone.now().year
    
    # Estatísticas gerais
    total_iptus = IPTU.objects.filter(ano_exercicio=ano_atual).count()
    valor_total = IPTU.objects.filter(ano_exercicio=ano_atual).aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    pagos = IPTU.objects.filter(ano_exercicio=ano_atual, status='PAGO').count()
    pendentes = IPTU.objects.filter(ano_exercicio=ano_atual, status='PENDENTE').count()
    
    context = {
        'ano_atual': ano_atual,
        'total_iptus': total_iptus,
        'valor_total': valor_total,
        'pagos': pagos,
        'pendentes': pendentes,
    }
    return render(request, 'financeiro/relatorios/iptu.html', context)

# Views para NFe
@login_required
def listar_nfe(request):
    notas = NotaFiscal.objects.select_related('parcela', 'parcela__contrato', 'parcela__contrato__inquilino').all()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        notas = notas.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        notas = notas.filter(
            Q(numero__icontains=search) |
            Q(parcela__contrato__numero__icontains=search) |
            Q(parcela__contrato__inquilino__nome__icontains=search)
        )
    
    paginator = Paginator(notas, 20)
    page = request.GET.get('page')
    notas = paginator.get_page(page)
    
    context = {
        'notas': notas,
        'status_choices': NotaFiscal.STATUS_CHOICES,
    }
    return render(request, 'financeiro/nfe/listar.html', context)

@login_required
def emitir_nfe(request):
    if request.method == 'POST':
        parcela_ids = request.POST.getlist('parcelas')
        
        if not parcela_ids:
            messages.error(request, 'Selecione pelo menos uma parcela para emitir NFe.')
            return redirect('financeiro:emitir_nfe')
        
        try:
            nfe_service = NFEService()
            nfes_emitidas = []
            
            for parcela_id in parcela_ids:
                parcela = get_object_or_404(Parcela, id=parcela_id, status='PAGO')
                
                # Verifica se já existe NFe para esta parcela
                if NotaFiscal.objects.filter(parcelas=parcela).exists():
                    messages.warning(request, f'Parcela {parcela.numero_parcela} do contrato {parcela.contrato.numero} já possui NFe emitida.')
                    continue
                
                # Cria nova NFe
                nota_fiscal = NotaFiscal.objects.create(
                    numero=NotaFiscal.gerar_proximo_numero(),
                    serie=settings.NFE_SERIE_PADRAO,
                    data_emissao=timezone.now(),
                    cliente_nome=parcela.contrato.inquilino.nome,
                    cliente_cpf=parcela.contrato.inquilino.cpf,
                    cliente_cnpj=parcela.contrato.inquilino.cnpj if hasattr(parcela.contrato.inquilino, 'cnpj') else None,
                    cliente_endereco=parcela.contrato.imovel.endereco,
                    cliente_numero=parcela.contrato.imovel.numero,
                    cliente_bairro=parcela.contrato.imovel.bairro,
                    cliente_cidade=parcela.contrato.imovel.cidade,
                    cliente_uf=parcela.contrato.imovel.estado,
                    cliente_cep=parcela.contrato.imovel.cep,
                    discriminacao_servicos=f"Serviços de administração predial - Contrato {parcela.contrato.numero} - Parcela {parcela.numero_parcela}",
                    valor_servicos=parcela.valor_total,
                    status='PENDENTE'
                )
                
                # Associa parcela à NFe
                nota_fiscal.parcelas.add(parcela)
                
                # Emite via API
                try:
                    nfe_service.emitir_nfe(nota_fiscal)
                    nfes_emitidas.append(nota_fiscal)
                    messages.success(request, f'NFe {nota_fiscal.numero} emitida com sucesso!')
                    
                except NFEServiceException as e:
                    messages.error(request, f'Erro ao emitir NFe para parcela {parcela.numero_parcela}: {e}')
                    nota_fiscal.delete()  # Remove NFe com erro
            
            if nfes_emitidas:
                return redirect('financeiro:listar_nfe')
            
        except Exception as e:
            messages.error(request, f'Erro inesperado: {e}')
    
    # Lista parcelas elegíveis para NFe
    parcelas_elegiveis = Parcela.objects.filter(
        status='PAGO',
        data_pagamento__isnull=False
    ).exclude(
        id__in=NotaFiscal.objects.values_list('parcelas__id', flat=True)
    ).select_related('contrato', 'contrato__inquilino', 'contrato__imovel')
    
    return render(request, 'financeiro/nfe/emitir.html', {
        'parcelas_elegiveis': parcelas_elegiveis
    })

@login_required
def listar_nfe(request):
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status = request.GET.get('status')
    cliente = request.GET.get('cliente')
    
    nfes = NotaFiscal.objects.all().order_by('-data_emissao')
    
    if data_inicio:
        nfes = nfes.filter(data_emissao__gte=data_inicio)
    if data_fim:
        nfes = nfes.filter(data_emissao__lte=data_fim)
    if status:
        nfes = nfes.filter(status=status)
    if cliente:
        nfes = nfes.filter(cliente_nome__icontains=cliente)
    
    # Paginação
    paginator = Paginator(nfes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'financeiro/nfe/listar.html', {
        'page_obj': page_obj,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'status': status,
            'cliente': cliente
        }
    })

@login_required
def detalhes_nfe(request, pk):
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_nfe')
    
    # Ações via POST
    if request.method == 'POST':
        acao = request.POST.get('acao')
        nfe_service = NFEService()
        
        try:
            if acao == 'consultar_status':
                nfe_service.consultar_status(nota_fiscal)
                messages.success(request, 'Status da NFe atualizado com sucesso!')
                
            elif acao == 'cancelar':
                motivo = request.POST.get('motivo_cancelamento')
                if not motivo:
                    messages.error(request, 'Motivo do cancelamento é obrigatório.')
                else:
                    nfe_service.cancelar_nfe(nota_fiscal, motivo)
                    messages.success(request, 'NFe cancelada com sucesso!')
                    
            elif acao == 'reenviar_email':
                email = request.POST.get('email_destino')
                if not email:
                    messages.error(request, 'Email de destino é obrigatório.')
                else:
                    nfe_service.reenviar_email(nota_fiscal, email)
                    messages.success(request, f'NFe enviada para {email} com sucesso!')
                    
        except NFEServiceException as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Erro inesperado: {e}')
        
        return redirect('financeiro:detalhes_nfe', pk=pk)
    
    return render(request, 'financeiro/nfe/detalhar.html', {
        'nota_fiscal': nota_fiscal
    })

@login_required
def download_nfe_pdf(request, pk):
    """Download do PDF da NFe"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_nfe')
    
    if not nota_fiscal.arquivo_pdf:
        messages.error(request, 'PDF não disponível para esta NFe.')
        return redirect('financeiro:detalhes_nfe', pk=pk)
    
    response = HttpResponse(nota_fiscal.arquivo_pdf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="NFe_{nota_fiscal.numero}.pdf"'
    return response

@login_required
def download_nfe_xml(request, pk):
    """Download do XML da NFe"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('financeiro:listar_nfe')
    
    if not nota_fiscal.arquivo_xml:
        messages.error(request, 'XML não disponível para esta NFe.')
        return redirect('financeiro:detalhes_nfe', pk=pk)
    
    response = HttpResponse(nota_fiscal.arquivo_xml.read(), content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="NFe_{nota_fiscal.numero}.xml"'
    return response

# Views para Sangrias
@login_required
def listar_sangrias(request):
    """Lista todas as sangrias/despesas"""
    sangrias = Sangria.objects.select_related('imovel', 'contrato').all()
    
    # Filtrar por tenant - incluir sangrias sem tenant se usuário não tem tenant
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangrias = sangrias.filter(tenant=tenant)
    else:
        # Se usuário não tem tenant, mostrar sangrias sem tenant ou criadas por ele
        sangrias = sangrias.filter(
            models.Q(tenant__isnull=True) | models.Q(usuario_criacao=request.user)
        )
    
    # Aplicar filtros
    form = SangriaFiltroForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('data_inicio'):
            sangrias = sangrias.filter(data_vencimento__gte=form.cleaned_data['data_inicio'])
        if form.cleaned_data.get('data_fim'):
            sangrias = sangrias.filter(data_vencimento__lte=form.cleaned_data['data_fim'])
        if form.cleaned_data.get('categoria'):
            sangrias = sangrias.filter(categoria=form.cleaned_data['categoria'])
        if form.cleaned_data.get('status'):
            sangrias = sangrias.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('forma_pagamento'):
            sangrias = sangrias.filter(forma_pagamento=form.cleaned_data['forma_pagamento'])
        if form.cleaned_data.get('descricao'):
            sangrias = sangrias.filter(descricao__icontains=form.cleaned_data['descricao'])
    
    # Ordenar por data de vencimento (mais recentes primeiro)
    sangrias = sangrias.order_by('-data_vencimento')
    
    # Paginação
    paginator = Paginator(sangrias, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular totais
    total_pendente = sangrias.filter(status='pendente').aggregate(
        total=models.Sum('valor')
    )['total'] or 0
    
    total_pago = sangrias.filter(status='pago').aggregate(
        total=models.Sum('valor')
    )['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'total_geral': total_pendente + total_pago,
        'total_sangrias': sangrias.count(),
        'valor_total': total_pendente + total_pago,
        'categoria_choices': Sangria.CATEGORIA_CHOICES
    }
    
    return render(request, 'financeiro/sangria/listar.html', context)

@login_required
def cadastrar_sangria(request):
    """Cadastra nova sangria/despesa"""
    if request.method == 'POST':
        form = SangriaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                sangria = form.save(commit=False)
                # Definir usuário que criou (campo obrigatório)
                sangria.usuario_criacao = request.user
                # Definir tenant
                tenant = getattr(request.user, 'tenant', None)
                if tenant:
                    sangria.tenant = tenant
                sangria.save()
                messages.success(request, 'Sangria cadastrada com sucesso!')
                return redirect('financeiro:listar_sangrias')
            except Exception as e:
                messages.error(request, f'Erro ao salvar sangria: {str(e)}')
        else:
            # Adicionar mensagens de erro específicas
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erro no campo {field}: {error}')
    else:
        form = SangriaForm(user=request.user)
    
    return render(request, 'financeiro/sangria/cadastrar.html', {'form': form})

@login_required
def detalhes_sangria(request, pk):
    """Exibe detalhes de uma sangria"""
    # Filtrar por tenant para evitar vazamento de dados
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangria = get_object_or_404(Sangria, pk=pk, tenant=tenant)
    else:
        # Se usuário não tem tenant, verificar se é criador da sangria
        sangria = get_object_or_404(
            Sangria, 
            pk=pk, 
            usuario_criacao=request.user,
            tenant__isnull=True
        )
    
    return render(request, 'financeiro/sangria/detalhar.html', {'sangria': sangria})

@login_required
@requer_confirmacao_senha()
def editar_sangria(request, pk):
    """Edita uma sangria existente"""
    # Filtrar por tenant para evitar vazamento de dados
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangria = get_object_or_404(Sangria, pk=pk, tenant=tenant)
    else:
        # Se usuário não tem tenant, verificar se é criador da sangria
        sangria = get_object_or_404(
            Sangria, 
            pk=pk, 
            usuario_criacao=request.user,
            tenant__isnull=True
        )
    
    if request.method == 'POST':
        form = SangriaForm(request.POST, instance=sangria, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sangria atualizada com sucesso!')
            return redirect('financeiro:detalhes_sangria', pk=pk)
    else:
        form = SangriaForm(instance=sangria, user=request.user)
    
    return render(request, 'financeiro/sangria/editar.html', {'form': form, 'sangria': sangria})

@login_required
@requer_confirmacao_senha()
def excluir_sangria(request, pk):
    """Exclui uma sangria"""
    # Filtrar por tenant para evitar vazamento de dados
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangria = get_object_or_404(Sangria, pk=pk, tenant=tenant)
    else:
        # Se usuário não tem tenant, verificar se é criador da sangria
        sangria = get_object_or_404(
            Sangria, 
            pk=pk, 
            usuario_criacao=request.user,
            tenant__isnull=True
        )
    
    if request.method == 'POST':
        sangria.delete()
        messages.success(request, 'Sangria excluída com sucesso!')
        return redirect('financeiro:listar_sangrias')
    
    return render(request, 'financeiro/sangria/excluir.html', {'sangria': sangria})

@login_required
def marcar_sangria_paga(request, pk):
    """Marca uma sangria como paga"""
    # Filtrar por tenant para evitar vazamento de dados
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangria = get_object_or_404(Sangria, pk=pk, tenant=tenant)
    else:
        # Se usuário não tem tenant, verificar se é criador da sangria
        sangria = get_object_or_404(
            Sangria, 
            pk=pk, 
            usuario_criacao=request.user,
            tenant__isnull=True
        )
    
    if request.method == 'POST':
        try:
            sangria.marcar_como_pago()
            messages.success(request, 'Sangria marcada como paga!')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('financeiro:detalhes_sangria', pk=pk)
    
    return render(request, 'financeiro/sangria/marcar_paga.html', {'sangria': sangria})

@login_required
def cancelar_sangria(request, pk):
    """Cancela uma sangria"""
    # Filtrar por tenant para evitar vazamento de dados
    tenant = getattr(request.user, 'tenant', None)
    if tenant:
        sangria = get_object_or_404(Sangria, pk=pk, tenant=tenant)
    else:
        # Se usuário não tem tenant, verificar se é criador da sangria
        sangria = get_object_or_404(
            Sangria, 
            pk=pk, 
            usuario_criacao=request.user,
            tenant__isnull=True
        )
    
    if request.method == 'POST':
        try:
            sangria.cancelar()
            messages.success(request, 'Sangria cancelada!')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('financeiro:detalhes_sangria', pk=pk)
    
    return render(request, 'financeiro/sangria/cancelar.html', {'sangria': sangria})
