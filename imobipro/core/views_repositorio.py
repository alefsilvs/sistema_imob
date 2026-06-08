from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import mimetypes
from datetime import datetime, timedelta

from .models_repositorio import (
    Documento, CategoriaDocumento, LogAcessoDocumento, 
    CompartilhamentoDocumento, FavoritoDocumento, ConfiguracaoRepositorio
)
from .models_perfil import verificar_permissao


@login_required
def repositorio_dashboard(request):
    """Dashboard principal do repositório"""
    if not verificar_permissao(request.user, 'repositorio', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar o repositório.')
        return redirect('core:dashboard')
    
    # Estatísticas
    total_documentos = Documento.objects.filter(ativo=True).count()
    documentos_pendentes = Documento.objects.filter(ativo=True, aprovado=False).count()
    categorias_ativas = CategoriaDocumento.objects.filter(ativo=True).count()
    
    # Documentos recentes
    documentos_recentes = Documento.objects.filter(
        ativo=True
    ).select_related('categoria', 'criado_por')[:10]
    
    # Documentos por categoria
    documentos_por_categoria = CategoriaDocumento.objects.filter(
        ativo=True
    ).annotate(
        total_documentos=Count('documentos', filter=Q(documentos__ativo=True))
    ).order_by('-total_documentos')
    
    # Meus documentos favoritos
    favoritos = FavoritoDocumento.objects.filter(
        usuario=request.user
    ).select_related('documento', 'documento__categoria')[:5]
    
    context = {
        'total_documentos': total_documentos,
        'documentos_pendentes': documentos_pendentes,
        'categorias_ativas': categorias_ativas,
        'documentos_recentes': documentos_recentes,
        'documentos_por_categoria': documentos_por_categoria,
        'favoritos': favoritos,
    }
    
    return render(request, 'core/repositorio/dashboard.html', context)


@login_required
def listar_documentos(request):
    """Lista todos os documentos com filtros"""
    if not verificar_permissao(request.user, 'repositorio', 'visualizar'):
        messages.error(request, 'Você não tem permissão para acessar o repositório.')
        return redirect('core:dashboard')
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    tipo_documento = request.GET.get('tipo')
    busca = request.GET.get('busca')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Query base
    documentos = Documento.objects.filter(ativo=True).select_related(
        'categoria', 'criado_por', 'proprietario', 'inquilino'
    )
    
    # Aplicar filtros
    if categoria_id:
        documentos = documentos.filter(categoria_id=categoria_id)
    
    if tipo_documento:
        documentos = documentos.filter(tipo_documento=tipo_documento)
    
    if busca:
        documentos = documentos.filter(
            Q(titulo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(tags__icontains=busca)
        )
    
    if data_inicio:
        documentos = documentos.filter(criado_em__gte=data_inicio)
    
    if data_fim:
        documentos = documentos.filter(criado_em__lte=data_fim)
    
    # Filtrar por permissão de acesso
    documentos_permitidos = []
    for doc in documentos:
        if doc.pode_visualizar(request.user):
            documentos_permitidos.append(doc.id)
    
    documentos = documentos.filter(id__in=documentos_permitidos)
    
    # Paginação
    paginator = Paginator(documentos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para filtros
    categorias = CategoriaDocumento.objects.filter(ativo=True)
    tipos_documento = Documento.TIPOS_DOCUMENTO
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'tipos_documento': tipos_documento,
        'filtros': {
            'categoria': categoria_id,
            'tipo': tipo_documento,
            'busca': busca,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    
    return render(request, 'core/repositorio/listar_documentos.html', context)


@login_required
def upload_documento(request):
    """Upload de novo documento"""
    if not verificar_permissao(request.user, 'repositorio', 'criar'):
        messages.error(request, 'Você não tem permissão para fazer upload de documentos.')
        return redirect('core:repositorio_dashboard')
    
    if request.method == 'POST':
        try:
            # Validar dados
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao', '')
            categoria_id = request.POST.get('categoria')
            tipo_documento = request.POST.get('tipo_documento')
            tipo_acesso = request.POST.get('tipo_acesso', 'privado')
            tags = request.POST.get('tags', '')
            arquivo = request.FILES.get('arquivo')
            
            if not all([titulo, categoria_id, tipo_documento, arquivo]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                return redirect('core:upload_documento')
            
            # Validar configurações
            config = ConfiguracaoRepositorio.get_configuracao()
            
            # Validar tamanho do arquivo
            if arquivo.size > config.tamanho_maximo_arquivo:
                tamanho_max_mb = config.tamanho_maximo_arquivo / (1024 * 1024)
                messages.error(request, f'Arquivo muito grande. Tamanho máximo: {tamanho_max_mb:.1f}MB')
                return redirect('core:upload_documento')
            
            # Validar extensão
            extensao = os.path.splitext(arquivo.name)[1].lower().replace('.', '')
            tipos_permitidos = config.tipos_arquivo_permitidos.split(',')
            if extensao not in tipos_permitidos:
                messages.error(request, f'Tipo de arquivo não permitido. Tipos aceitos: {", ".join(tipos_permitidos)}')
                return redirect('core:upload_documento')
            
            # Criar documento
            documento = Documento.objects.create(
                titulo=titulo,
                descricao=descricao,
                categoria_id=categoria_id,
                tipo_documento=tipo_documento,
                arquivo=arquivo,
                tipo_acesso=tipo_acesso,
                criado_por=request.user,
                tags=tags,
                aprovado=not config.aprovacao_obrigatoria
            )
            
            # Relacionamentos opcionais
            proprietario_id = request.POST.get('proprietario')
            inquilino_id = request.POST.get('inquilino')
            
            if proprietario_id:
                documento.proprietario_id = proprietario_id
            if inquilino_id:
                documento.inquilino_id = inquilino_id
            
            documento.save()
            
            # Log de ação
            LogAcessoDocumento.objects.create(
                documento=documento,
                usuario=request.user,
                acao='editar',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Documento enviado com sucesso!')
            return redirect('core:detalhes_documento', documento_id=documento.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao enviar documento: {str(e)}')
    
    # Dados para o formulário
    categorias = CategoriaDocumento.objects.filter(ativo=True)
    tipos_documento = Documento.TIPOS_DOCUMENTO
    tipos_acesso = Documento.TIPOS_ACESSO
    
    # Buscar relacionamentos para seleção
    from .models import Proprietario, Inquilino
    proprietarios = Proprietario.objects.all()
    inquilinos = Inquilino.objects.all()
    
    context = {
        'categorias': categorias,
        'tipos_documento': tipos_documento,
        'tipos_acesso': tipos_acesso,
        'proprietarios': proprietarios,
        'inquilinos': inquilinos,
    }
    
    return render(request, 'core/repositorio/upload_documento.html', context)


@login_required
def detalhes_documento(request, documento_id):
    """Detalhes de um documento"""
    documento = get_object_or_404(Documento, id=documento_id, ativo=True)
    
    if not documento.pode_visualizar(request.user):
        messages.error(request, 'Você não tem permissão para visualizar este documento.')
        return redirect('core:listar_documentos')
    
    # Log de acesso
    LogAcessoDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='visualizar',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Verificar se é favorito
    is_favorito = FavoritoDocumento.objects.filter(
        usuario=request.user, documento=documento
    ).exists()
    
    # Versões do documento
    versoes = Documento.objects.filter(
        Q(documento_pai=documento) | Q(documento_pai=documento.documento_pai, documento_pai__isnull=False),
        ativo=True
    ).order_by('-versao')
    
    # Logs de acesso recentes
    logs_recentes = LogAcessoDocumento.objects.filter(
        documento=documento
    ).select_related('usuario').order_by('-data_acesso')[:10]
    
    context = {
        'documento': documento,
        'is_favorito': is_favorito,
        'versoes': versoes,
        'logs_recentes': logs_recentes,
        'pode_editar': verificar_permissao(request.user, 'repositorio', 'editar'),
        'pode_excluir': verificar_permissao(request.user, 'repositorio', 'excluir'),
    }
    
    return render(request, 'core/repositorio/detalhes_documento.html', context)


@login_required
def download_documento(request, documento_id):
    """Download de um documento"""
    documento = get_object_or_404(Documento, id=documento_id, ativo=True)
    
    if not documento.pode_visualizar(request.user):
        raise Http404("Documento não encontrado")
    
    # Log de download
    LogAcessoDocumento.objects.create(
        documento=documento,
        usuario=request.user,
        acao='download',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Preparar resposta
    file_path = documento.arquivo.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_path)[0])
            response['Content-Disposition'] = f'attachment; filename="{documento.titulo}{documento.extensao}"'
            return response
    
    raise Http404("Arquivo não encontrado")


@login_required
@require_http_methods(["POST"])
def toggle_favorito(request, documento_id):
    """Adiciona/remove documento dos favoritos"""
    documento = get_object_or_404(Documento, id=documento_id, ativo=True)
    
    if not documento.pode_visualizar(request.user):
        return JsonResponse({'error': 'Sem permissão'}, status=403)
    
    favorito, created = FavoritoDocumento.objects.get_or_create(
        usuario=request.user,
        documento=documento
    )
    
    if not created:
        favorito.delete()
        is_favorito = False
    else:
        is_favorito = True
    
    return JsonResponse({'is_favorito': is_favorito})


@login_required
def compartilhar_documento(request, documento_id):
    """Criar link de compartilhamento para documento"""
    documento = get_object_or_404(Documento, id=documento_id, ativo=True)
    
    if not documento.pode_visualizar(request.user):
        messages.error(request, 'Você não tem permissão para compartilhar este documento.')
        return redirect('core:detalhes_documento', documento_id=documento_id)
    
    if request.method == 'POST':
        dias_expiracao = int(request.POST.get('dias_expiracao', 7))
        senha = request.POST.get('senha', '')
        limite_acessos = request.POST.get('limite_acessos')
        
        expira_em = timezone.now() + timedelta(days=dias_expiracao)
        
        compartilhamento = CompartilhamentoDocumento.objects.create(
            documento=documento,
            criado_por=request.user,
            expira_em=expira_em,
            senha=senha,
            limite_acessos=int(limite_acessos) if limite_acessos else None
        )
        
        # Log de compartilhamento
        LogAcessoDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            acao='compartilhar',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        link_compartilhamento = request.build_absolute_uri(
            f'/repositorio/compartilhado/{compartilhamento.token}/'
        )
        
        messages.success(request, 'Link de compartilhamento criado com sucesso!')
        return JsonResponse({
            'success': True,
            'link': link_compartilhamento,
            'expira_em': expira_em.strftime('%d/%m/%Y %H:%M')
        })
    
    return render(request, 'core/repositorio/compartilhar_documento.html', {
        'documento': documento
    })


def documento_compartilhado(request, token):
    """Acesso a documento via link de compartilhamento"""
    compartilhamento = get_object_or_404(CompartilhamentoDocumento, token=token)
    
    if request.method == 'POST':
        senha = request.POST.get('senha', '')
        
        if not compartilhamento.pode_acessar(senha):
            messages.error(request, 'Link expirado, inativo ou senha incorreta.')
            return render(request, 'core/repositorio/documento_compartilhado.html', {
                'compartilhamento': compartilhamento,
                'erro': True
            })
        
        # Incrementar contador de acessos
        compartilhamento.acessos_realizados += 1
        compartilhamento.save()
        
        # Retornar arquivo
        documento = compartilhamento.documento
        file_path = documento.arquivo.path
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_path)[0])
                response['Content-Disposition'] = f'attachment; filename="{documento.titulo}{documento.extensao}"'
                return response
        
        raise Http404("Arquivo não encontrado")
    
    # Verificar se precisa de senha
    precisa_senha = bool(compartilhamento.senha)
    
    context = {
        'compartilhamento': compartilhamento,
        'precisa_senha': precisa_senha,
        'pode_acessar': compartilhamento.pode_acessar() if not precisa_senha else None
    }
    
    return render(request, 'core/repositorio/documento_compartilhado.html', context)


@login_required
def gerenciar_categorias(request):
    """Gerenciar categorias de documentos"""
    if not verificar_permissao(request.user, 'repositorio', 'editar'):
        messages.error(request, 'Você não tem permissão para gerenciar categorias.')
        return redirect('core:repositorio_dashboard')
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'criar':
            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao', '')
            icone = request.POST.get('icone', 'fas fa-file')
            cor = request.POST.get('cor', '#007bff')
            
            if nome:
                CategoriaDocumento.objects.create(
                    nome=nome,
                    descricao=descricao,
                    icone=icone,
                    cor=cor
                )
                messages.success(request, 'Categoria criada com sucesso!')
            else:
                messages.error(request, 'Nome da categoria é obrigatório.')
        
        elif acao == 'editar':
            categoria_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(CategoriaDocumento, id=categoria_id)
            
            categoria.nome = request.POST.get('nome', categoria.nome)
            categoria.descricao = request.POST.get('descricao', categoria.descricao)
            categoria.icone = request.POST.get('icone', categoria.icone)
            categoria.cor = request.POST.get('cor', categoria.cor)
            categoria.save()
            
            messages.success(request, 'Categoria atualizada com sucesso!')
        
        elif acao == 'excluir':
            categoria_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(CategoriaDocumento, id=categoria_id)
            
            if categoria.documentos.filter(ativo=True).exists():
                messages.error(request, 'Não é possível excluir categoria com documentos.')
            else:
                categoria.ativo = False
                categoria.save()
                messages.success(request, 'Categoria removida com sucesso!')
    
    categorias = CategoriaDocumento.objects.annotate(
        total_documentos=Count('documentos', filter=Q(documentos__ativo=True))
    ).order_by('nome')
    
    return render(request, 'core/repositorio/gerenciar_categorias.html', {
        'categorias': categorias
    })


@login_required
def configuracoes_repositorio(request):
    """Configurações do repositório"""
    if not request.user.is_superuser:
        messages.error(request, 'Apenas administradores podem acessar as configurações.')
        return redirect('core:repositorio_dashboard')
    
    config = ConfiguracaoRepositorio.get_configuracao()
    
    if request.method == 'POST':
        config.tamanho_maximo_arquivo = int(request.POST.get('tamanho_maximo_arquivo', config.tamanho_maximo_arquivo))
        config.tipos_arquivo_permitidos = request.POST.get('tipos_arquivo_permitidos', config.tipos_arquivo_permitidos)
        config.backup_automatico = request.POST.get('backup_automatico') == 'on'
        config.dias_retencao_logs = int(request.POST.get('dias_retencao_logs', config.dias_retencao_logs))
        config.aprovacao_obrigatoria = request.POST.get('aprovacao_obrigatoria') == 'on'
        config.notificar_novos_documentos = request.POST.get('notificar_novos_documentos') == 'on'
        
        config.save()
        messages.success(request, 'Configurações salvas com sucesso!')
    
    return render(request, 'core/repositorio/configuracoes.html', {
        'config': config
    })