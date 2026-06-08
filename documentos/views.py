from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
import json
import os
import mimetypes
from .models import (
    Vistoria, ItemVistoria, Documento, TipoDocumento, 
    CategoriaDocumento, LogAcessoDocumento, CompartilhamentoDocumento
)
from .forms import VistoriaForm, ItemVistoriaFormSet
from imoveis.models import Imovel
from contratos.models import Contrato

@login_required
def agendar_vistoria(request):
    """View para agendar uma nova vistoria"""
    if request.method == 'POST':
        form = VistoriaForm(request.POST)
        if form.is_valid():
            vistoria = form.save()
            messages.success(
                request, 
                f'Vistoria agendada com sucesso para {vistoria.data_agendamento.strftime("%d/%m/%Y às %H:%M")}!'
            )
            return redirect('documentos:listar_vistorias')
    else:
        form = VistoriaForm()
    
    context = {
        'form': form,
        'title': 'Agendar Vistoria'
    }
    return render(request, 'documentos/agendar_vistoria.html', context)

@login_required
def listar_vistorias(request):
    """View para listar vistorias agendadas"""
    vistorias = Vistoria.objects.select_related('imovel', 'contrato').all()
    
    # Filtros
    status = request.GET.get('status')
    if status:
        vistorias = vistorias.filter(status=status)
    
    tipo = request.GET.get('tipo')
    if tipo:
        vistorias = vistorias.filter(tipo=tipo)
    
    search = request.GET.get('search')
    if search:
        vistorias = vistorias.filter(
            Q(imovel__codigo__icontains=search) |
            Q(imovel__endereco__icontains=search) |
            Q(responsavel__icontains=search) |
            Q(observacoes__icontains=search)
        )
    
    # Ordenação
    vistorias = vistorias.order_by('-data_agendamento')
    
    # Paginação
    paginator = Paginator(vistorias, 20)
    page = request.GET.get('page')
    vistorias_page = paginator.get_page(page)
    
    context = {
        'vistorias': vistorias_page,
        'status_choices': Vistoria.STATUS_CHOICES,
        'tipo_choices': Vistoria.TIPO_CHOICES,
        'title': 'Vistorias Agendadas'
    }
    return render(request, 'documentos/listar_vistorias.html', context)

@login_required
def detalhes_vistoria(request, pk):
    """View para detalhar uma vistoria específica"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        vistoria = get_object_or_404(Vistoria, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('documentos:listar_vistorias')
    
    context = {
        'vistoria': vistoria,
        'title': f'Vistoria {vistoria.tipo} - {vistoria.imovel.codigo}'
    }
    return render(request, 'documentos/detalhar_vistoria.html', context)

@login_required
def editar_vistoria(request, pk):
    """View para editar uma vistoria"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        vistoria = get_object_or_404(Vistoria, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('documentos:listar_vistorias')
    
    if request.method == 'POST':
        form = VistoriaForm(request.POST, instance=vistoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vistoria atualizada com sucesso!')
            return redirect('documentos:detalhes_vistoria', pk=pk)
    else:
        form = VistoriaForm(instance=vistoria)
    
    context = {
        'form': form,
        'vistoria': vistoria,
        'title': f'Editar Vistoria - {vistoria.imovel.codigo}'
    }
    return render(request, 'documentos/editar_vistoria.html', context)

@login_required
def cancelar_vistoria(request, pk):
    """View para cancelar uma vistoria"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        vistoria = get_object_or_404(Vistoria, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('documentos:listar_vistorias')
    
    if vistoria.status == 'AGENDADA':
        vistoria.status = 'CANCELADA'
        vistoria.save()
        messages.success(request, 'Vistoria cancelada com sucesso!')
    else:
        messages.error(request, 'Apenas vistorias agendadas podem ser canceladas.')
    
    return redirect('documentos:listar_vistorias')

@login_required
def realizar_vistoria(request, pk):
    """View para marcar uma vistoria como realizada"""
    # Filtrar por tenant para evitar vazamento de dados
    if hasattr(request, 'tenant') and request.tenant:
        vistoria = get_object_or_404(Vistoria, pk=pk, tenant=request.tenant)
    else:
        messages.error(request, 'Acesso negado.')
        return redirect('documentos:listar_vistorias')
    
    if vistoria.status == 'AGENDADA':
        vistoria.status = 'REALIZADA'
        vistoria.data_realizacao = timezone.now()
        vistoria.save()
        messages.success(request, 'Vistoria marcada como realizada!')
    else:
        messages.error(request, 'Apenas vistorias agendadas podem ser marcadas como realizadas.')
    
    return redirect('documentos:detalhes_vistoria', pk=pk)

# ==================== REPOSITÓRIO DIGITAL ====================

@login_required
def repositorio_dashboard(request):
    """Dashboard principal do repositório digital"""
    tenant = getattr(request.user, 'tenant', None)
    
    # Estatísticas gerais
    total_documentos = Documento.objects.filter(tenant=tenant).count()
    documentos_recentes = Documento.objects.filter(
        tenant=tenant,
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Documentos por tipo
    tipos_stats = TipoDocumento.objects.filter(
        tenant=tenant
    ).annotate(
        total_docs=Count('documento')
    ).order_by('-total_docs')[:5]
    
    # Documentos vencendo
    documentos_vencendo = Documento.objects.filter(
        tenant=tenant,
        data_validade__lte=timezone.now() + timezone.timedelta(days=30),
        data_validade__gte=timezone.now()
    ).order_by('data_validade')[:10]
    
    # Atividade recente
    atividades_recentes = LogAcessoDocumento.objects.filter(
        documento__tenant=tenant
    ).select_related('documento', 'usuario').order_by('-data_acesso')[:10]
    
    context = {
        'total_documentos': total_documentos,
        'documentos_recentes': documentos_recentes,
        'tipos_stats': tipos_stats,
        'documentos_vencendo': documentos_vencendo,
        'atividades_recentes': atividades_recentes,
    }
    
    return render(request, 'documentos/repositorio_dashboard.html', context)

@login_required
def listar_documentos(request):
    """Lista todos os documentos com filtros e busca"""
    tenant = getattr(request.user, 'tenant', None)
    
    documentos = Documento.objects.filter(tenant=tenant).select_related(
        'tipo', 'usuario_upload'
    ).order_by('-created_at')
    
    # Filtros
    categoria = request.GET.get('categoria')
    tipo_id = request.GET.get('tipo')
    status = request.GET.get('status')
    busca = request.GET.get('busca')
    
    if categoria:
        documentos = documentos.filter(tipo__categoria=categoria)
    
    if tipo_id:
        documentos = documentos.filter(tipo_id=tipo_id)
    
    if status:
        documentos = documentos.filter(status=status)
    
    if busca:
        documentos = documentos.filter(
            Q(nome_arquivo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(palavras_chave__icontains=busca)
        )
    
    # Paginação
    paginator = Paginator(documentos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    tipos = TipoDocumento.objects.filter(tenant=tenant, ativo=True)
    categorias = TipoDocumento.objects.filter(tenant=tenant, ativo=True).values_list('categoria', flat=True).distinct()
    
    # Choices para status
    status_choices = [
        ('ATIVO', 'Ativo'),
        ('ARQUIVADO', 'Arquivado'),
        ('VENCIDO', 'Vencido'),
    ]
    
    context = {
        'page_obj': page_obj,
        'tipos': tipos,
        'categorias': categorias,
        'status_choices': status_choices,
        'filtros': {
            'categoria': categoria,
            'tipo': tipo_id,
            'status': status,
            'busca': busca,
        }
    }
    
    return render(request, 'documentos/listar_documentos.html', context)

@login_required
def upload_documento(request):
    """Upload de novos documentos"""
    # Obter tenant do usuário ou do request
    tenant = getattr(request.user, 'tenant', None)
    if not tenant:
        tenant = getattr(request, 'tenant', None)
    
    # Se ainda não tem tenant e é superuser, permitir acesso a todos os dados
    if not tenant and request.user.is_superuser:
        # Para superusers sem tenant, usar o primeiro tenant disponível ou None
        from saas.models import Tenant
        tenant = Tenant.objects.filter(status__in=['ativo', 'trial']).first()
    
    if request.method == 'POST':
        from .forms import DocumentoForm
        from core.models import Pessoa, Proprietario, Inquilino
        from imoveis.models import Imovel
        from contratos.models import Contrato
        from django.db.models import Q
        
        form = DocumentoForm(request.POST, request.FILES)
        
        # Configurar querysets baseado no tenant
        if tenant:
            form.fields['tipo'].queryset = TipoDocumento.objects.filter(tenant=tenant, ativo=True)
            # Para pessoas, combinar proprietários e inquilinos do tenant
            proprietarios = Proprietario.objects.filter(tenant=tenant).values_list('id', flat=True)
            inquilinos = Inquilino.objects.filter(tenant=tenant).values_list('id', flat=True)
            pessoas_ids = list(proprietarios) + list(inquilinos)
            form.fields['pessoa'].queryset = Pessoa.objects.filter(id__in=pessoas_ids)
            form.fields['imovel'].queryset = Imovel.objects.filter(tenant=tenant)
            form.fields['contrato'].queryset = Contrato.objects.filter(tenant=tenant)
        else:
            # Se não há tenant, usar querysets vazios ou todos os dados para superuser
            if request.user.is_superuser:
                form.fields['tipo'].queryset = TipoDocumento.objects.filter(ativo=True)
                form.fields['pessoa'].queryset = Pessoa.objects.all()
                form.fields['imovel'].queryset = Imovel.objects.all()
                form.fields['contrato'].queryset = Contrato.objects.all()
            else:
                form.fields['tipo'].queryset = TipoDocumento.objects.none()
                form.fields['pessoa'].queryset = Pessoa.objects.none()
                form.fields['imovel'].queryset = Imovel.objects.none()
                form.fields['contrato'].queryset = Contrato.objects.none()
        
        if form.is_valid():
            try:
                documento = form.save(commit=False)
                documento.tenant = tenant
                documento.usuario_upload = request.user
                
                # Processar tags
                tags = form.cleaned_data.get('tags', '')
                if tags:
                    documento.palavras_chave = tags
                
                documento.save()
                
                # Log de atividade
                LogAcessoDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    acao='UPLOAD',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    detalhes=f'Upload do arquivo {documento.nome_arquivo}'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Documento enviado com sucesso!',
                    'documento_id': documento.id
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f'{form.fields[field].label}: {error}')
            return JsonResponse({'success': False, 'error': '; '.join(errors)})
    
    # GET - Formulário de upload
    from .forms import DocumentoForm
    from core.models import Pessoa, Proprietario, Inquilino
    from imoveis.models import Imovel
    from contratos.models import Contrato
    
    # Configurar querysets baseado no tenant
    if tenant:
        tipos = TipoDocumento.objects.filter(tenant=tenant, ativo=True)
        form = DocumentoForm()
        form.fields['tipo'].queryset = tipos
        # Para pessoas, combinar proprietários e inquilinos do tenant
        proprietarios = Proprietario.objects.filter(tenant=tenant).values_list('id', flat=True)
        inquilinos = Inquilino.objects.filter(tenant=tenant).values_list('id', flat=True)
        pessoas_ids = list(proprietarios) + list(inquilinos)
        form.fields['pessoa'].queryset = Pessoa.objects.filter(id__in=pessoas_ids)
        form.fields['imovel'].queryset = Imovel.objects.filter(tenant=tenant)
        form.fields['contrato'].queryset = Contrato.objects.filter(tenant=tenant)
    else:
        # Se não há tenant, usar querysets vazios ou todos os dados para superuser
        if request.user.is_superuser:
            tipos = TipoDocumento.objects.filter(ativo=True)
            form = DocumentoForm()
            form.fields['tipo'].queryset = tipos
            form.fields['pessoa'].queryset = Pessoa.objects.all()
            form.fields['imovel'].queryset = Imovel.objects.all()
            form.fields['contrato'].queryset = Contrato.objects.all()
        else:
            tipos = TipoDocumento.objects.none()
            form = DocumentoForm()
            form.fields['tipo'].queryset = tipos
            form.fields['pessoa'].queryset = Pessoa.objects.none()
            form.fields['imovel'].queryset = Imovel.objects.none()
            form.fields['contrato'].queryset = Contrato.objects.none()
    
    context = {
        'form': form,
        'tipos': tipos,
    }
    
    return render(request, 'documentos/upload_documento.html', context)

@login_required
def visualizar_documento(request, documento_id):
    """Visualizar detalhes de um documento"""
    tenant = getattr(request.user, 'tenant', None)
    documento = get_object_or_404(Documento, id=documento_id, tenant=tenant)
    
    # Log de acesso
    LogAcessoDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='VISUALIZAR',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Histórico de versões
    versoes = Documento.objects.filter(
        tenant=tenant,
        nome_arquivo=documento.nome_arquivo
    ).exclude(id=documento.id).order_by('-versao')
    
    # Compartilhamentos ativos
    compartilhamentos = CompartilhamentoDocumento.objects.filter(
        documento=documento,
        ativo=True
    ).select_related('usuario_destino')
    
    context = {
        'documento': documento,
        'versoes': versoes,
        'compartilhamentos': compartilhamentos,
    }
    
    return render(request, 'documentos/visualizar_documento.html', context)

@login_required
def download_documento(request, documento_id):
    """Download de documento com controle de acesso"""
    tenant = getattr(request.user, 'tenant', None)
    documento = get_object_or_404(Documento, id=documento_id, tenant=tenant)
    
    # Verificar permissões
    if documento.confidencialidade == 'CONFIDENCIAL' and documento.usuario_upload != request.user:
        if not request.user.is_superuser:
            raise Http404("Documento não encontrado")
    
    # Log de download
    LogAcessoDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='DOWNLOAD',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Servir arquivo
    if documento.arquivo:
        response = HttpResponse(
            documento.arquivo.read(),
            content_type=mimetypes.guess_type(documento.arquivo.name)[0] or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{documento.nome_arquivo}"'
        return response
    
    raise Http404("Arquivo não encontrado")

@login_required
def compartilhar_documento(request, documento_id):
    """Compartilhar documento com outros usuários"""
    tenant = getattr(request.user, 'tenant', None)
    documento = get_object_or_404(Documento, id=documento_id, tenant=tenant)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            compartilhamento = CompartilhamentoDocumento(
                documento=documento,
                usuario_origem=request.user,
                tipo_acesso=data.get('tipo_acesso', 'LEITURA'),
                email_externo=data.get('email_externo', ''),
            )
            
            # Usuário interno
            if data.get('usuario_id'):
                compartilhamento.usuario_destino_id = data['usuario_id']
            
            # Data de expiração
            if data.get('data_expiracao'):
                compartilhamento.data_expiracao = data['data_expiracao']
            
            # Limite de acessos
            if data.get('limite_acessos'):
                compartilhamento.limite_acessos = data['limite_acessos']
            
            compartilhamento.save()
            
            # Log de atividade
            LogAcessoDocumento.objects.create(
                documento=documento,
                usuario=request.user,
                acao='COMPARTILHAR',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                detalhes=f'Compartilhado com {compartilhamento.usuario_destino or compartilhamento.email_externo}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Documento compartilhado com sucesso!',
                'token': compartilhamento.token_acesso
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})

@login_required
def gerenciar_categorias(request):
    """Gerenciar tipos de documentos"""
    tenant = getattr(request.user, 'tenant', None)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create':
                tipo = TipoDocumento.objects.create(
                    tenant=tenant,
                    nome=data['nome'],
                    descricao=data.get('descricao', ''),
                    categoria=data.get('categoria', 'OUTROS'),
                    obrigatorio=data.get('obrigatorio', False)
                )
                return JsonResponse({
                    'success': True,
                    'tipo': {
                        'id': tipo.id,
                        'nome': tipo.nome,
                        'descricao': tipo.descricao,
                        'categoria': tipo.categoria
                    }
                })
            
            elif action == 'update':
                tipo = get_object_or_404(TipoDocumento, id=data['id'], tenant=tenant)
                tipo.nome = data['nome']
                tipo.descricao = data.get('descricao', '')
                tipo.categoria = data.get('categoria', tipo.categoria)
                tipo.obrigatorio = data.get('obrigatorio', tipo.obrigatorio)
                tipo.save()
                
                return JsonResponse({'success': True, 'message': 'Tipo atualizado!'})
            
            elif action == 'delete':
                tipo = get_object_or_404(TipoDocumento, id=data['id'], tenant=tenant)
                tipo.ativo = False
                tipo.save()
                
                return JsonResponse({'success': True, 'message': 'Tipo removido!'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET - Listar tipos
    tipos = TipoDocumento.objects.filter(
        tenant=tenant,
        ativo=True
    ).annotate(
        total_documentos=Count('documento')
    ).order_by('nome')
    
    context = {
        'tipos': tipos,
        'categorias_choices': TipoDocumento._meta.get_field('categoria').choices,
    }
    
    return render(request, 'documentos/gerenciar_categorias.html', context)


@login_required
def obter_tipo_documento(request, tipo_id):
    """Obter dados de um tipo de documento específico"""
    tenant = getattr(request.user, 'tenant', None)
    
    try:
        tipo = get_object_or_404(TipoDocumento, id=tipo_id, tenant=tenant)
        return JsonResponse({
            'id': tipo.id,
            'nome': tipo.nome,
            'descricao': tipo.descricao,
            'categoria': tipo.categoria,
            'obrigatorio': tipo.obrigatorio,
            'ativo': tipo.ativo
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def editar_tipo_documento(request, tipo_id):
    """Editar um tipo de documento específico"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    tenant = getattr(request.user, 'tenant', None)
    
    try:
        data = json.loads(request.body)
        tipo = get_object_or_404(TipoDocumento, id=tipo_id, tenant=tenant)
        
        tipo.nome = data.get('nome', tipo.nome)
        tipo.descricao = data.get('descricao', tipo.descricao)
        tipo.categoria = data.get('categoria', tipo.categoria)
        tipo.obrigatorio = data.get('obrigatorio', tipo.obrigatorio)
        tipo.save()
        
        return JsonResponse({'success': True, 'message': 'Tipo atualizado com sucesso!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def excluir_tipo_documento(request, tipo_id):
    """Excluir (desativar) um tipo de documento específico"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    tenant = getattr(request.user, 'tenant', None)
    
    try:
        tipo = get_object_or_404(TipoDocumento, id=tipo_id, tenant=tenant)
        tipo.ativo = False
        tipo.save()
        
        return JsonResponse({'success': True, 'message': 'Tipo removido com sucesso!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
