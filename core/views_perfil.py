# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Views para Sistema de Perfis de Usuário
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
from .models_perfil import PerfilUsuario, AbrangenciaPerfil, UsuarioPerfil, LogAlteracaoPerfil
from .middleware_perfil import require_permission, verificar_permissao_usuario


@login_required
@require_permission('configuracoes', 'visualizar')
def listar_perfis(request):
    """Lista todos os perfis de usuário"""
    perfis = PerfilUsuario.objects.annotate(
        total_usuarios=Count('usuarioperfil', filter=Q(usuarioperfil__ativo=True))
    ).order_by('nome')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo')
    ativo_filtro = request.GET.get('ativo')
    
    if tipo_filtro:
        perfis = perfis.filter(tipo=tipo_filtro)
    
    if ativo_filtro:
        perfis = perfis.filter(ativo=ativo_filtro == 'true')
    
    # Paginação
    paginator = Paginator(perfis, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tipos_perfil': PerfilUsuario.TIPOS_PERFIL,
        'tipo_filtro': tipo_filtro,
        'ativo_filtro': ativo_filtro,
    }
    
    return render(request, 'core/perfis/listar.html', context)


@login_required
@require_permission('configuracoes', 'visualizar')
def detalhar_perfil(request, perfil_id):
    """Mostra detalhes de um perfil específico"""
    perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
    
    # Abrangências do perfil
    abrangencias = AbrangenciaPerfil.objects.filter(perfil=perfil).order_by('modulo', 'acao')
    
    # Usuários com este perfil
    usuarios = UsuarioPerfil.objects.filter(perfil=perfil, ativo=True).select_related('usuario')
    
    # Agrupar abrangências por módulo
    abrangencias_por_modulo = {}
    for abrangencia in abrangencias:
        modulo = abrangencia.get_modulo_display()
        if modulo not in abrangencias_por_modulo:
            abrangencias_por_modulo[modulo] = []
        abrangencias_por_modulo[modulo].append(abrangencia)
    
    context = {
        'perfil': perfil,
        'abrangencias_por_modulo': abrangencias_por_modulo,
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
    }
    
    return render(request, 'core/perfis/detalhar.html', context)


@login_required
@require_permission('configuracoes', 'visualizar')
def listar_usuarios_perfil(request):
    """Lista usuários e seus perfis"""
    usuarios = UsuarioPerfil.objects.select_related('usuario', 'perfil').order_by('usuario__username')
    
    # Filtros
    perfil_filtro = request.GET.get('perfil')
    ativo_filtro = request.GET.get('ativo')
    busca = request.GET.get('busca')
    
    if perfil_filtro:
        usuarios = usuarios.filter(perfil_id=perfil_filtro)
    
    if ativo_filtro:
        usuarios = usuarios.filter(ativo=ativo_filtro == 'true')
    
    if busca:
        usuarios = usuarios.filter(
            Q(usuario__username__icontains=busca) |
            Q(usuario__first_name__icontains=busca) |
            Q(usuario__last_name__icontains=busca) |
            Q(usuario__email__icontains=busca)
        )
    
    # Paginação
    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Perfis para filtro
    perfis = PerfilUsuario.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'page_obj': page_obj,
        'perfis': perfis,
        'perfil_filtro': perfil_filtro,
        'ativo_filtro': ativo_filtro,
        'busca': busca,
    }
    
    return render(request, 'core/perfis/usuarios.html', context)


@login_required
@require_permission('configuracoes', 'editar')
def atribuir_perfil(request, user_id):
    """Atribui ou altera perfil de um usuário"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        perfil_id = request.POST.get('perfil_id')
        ativo = request.POST.get('ativo') == 'on'
        observacoes = request.POST.get('observacoes', '')
        
        if perfil_id:
            perfil = get_object_or_404(PerfilUsuario, id=perfil_id)
            
            # Verificar se já existe perfil para o usuário
            usuario_perfil, created = UsuarioPerfil.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'perfil': perfil,
                    'ativo': ativo,
                    'observacoes': observacoes
                }
            )
            
            if not created:
                # Atualizar perfil existente
                perfil_anterior = usuario_perfil.perfil.nome
                usuario_perfil.perfil = perfil
                usuario_perfil.ativo = ativo
                usuario_perfil.observacoes = observacoes
                usuario_perfil.save()
                
                # Log da alteração
                LogAlteracaoPerfil.objects.create(
                    usuario_alterado=usuario,
                    usuario_responsavel=request.user,
                    acao='edicao',
                    perfil_anterior=perfil_anterior,
                    perfil_novo=perfil.nome,
                    detalhes=f'Perfil alterado de {perfil_anterior} para {perfil.nome}',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Perfil do usuário {usuario.username} atualizado com sucesso!')
            else:
                # Log da criação
                LogAlteracaoPerfil.objects.create(
                    usuario_alterado=usuario,
                    usuario_responsavel=request.user,
                    acao='atribuicao',
                    perfil_novo=perfil.nome,
                    detalhes=f'Perfil {perfil.nome} atribuído ao usuário',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Perfil {perfil.nome} atribuído ao usuário {usuario.username} com sucesso!')
            
            return redirect('core:usuarios_perfil')
    
    # GET - mostrar formulário
    perfis = PerfilUsuario.objects.filter(ativo=True).order_by('nome')
    
    try:
        usuario_perfil = UsuarioPerfil.objects.get(usuario=usuario)
    except UsuarioPerfil.DoesNotExist:
        usuario_perfil = None
    
    context = {
        'usuario': usuario,
        'perfis': perfis,
        'usuario_perfil': usuario_perfil,
    }
    
    return render(request, 'core/perfis/atribuir.html', context)


@login_required
def meu_perfil_permissoes(request):
    """Mostra as permissões do usuário logado"""
    try:
        usuario_perfil = UsuarioPerfil.objects.get(usuario=request.user, ativo=True)
        abrangencias = AbrangenciaPerfil.objects.filter(
            perfil=usuario_perfil.perfil, 
            permitido=True
        ).order_by('modulo', 'acao')
        
        # Agrupar por módulo
        permissoes_por_modulo = {}
        for abrangencia in abrangencias:
            modulo = abrangencia.get_modulo_display()
            if modulo not in permissoes_por_modulo:
                permissoes_por_modulo[modulo] = []
            permissoes_por_modulo[modulo].append(abrangencia.get_acao_display())
        
    except UsuarioPerfil.DoesNotExist:
        usuario_perfil = None
        permissoes_por_modulo = {}
    
    context = {
        'usuario_perfil': usuario_perfil,
        'permissoes_por_modulo': permissoes_por_modulo,
    }
    
    return render(request, 'core/perfis/meu_perfil.html', context)


@login_required
@require_permission('configuracoes', 'visualizar')
def logs_alteracao_perfil(request):
    """Lista logs de alterações de perfil"""
    logs = LogAlteracaoPerfil.objects.select_related(
        'usuario_alterado', 'usuario_responsavel'
    ).order_by('-data_alteracao')
    
    # Filtros
    acao_filtro = request.GET.get('acao')
    usuario_filtro = request.GET.get('usuario')
    
    if acao_filtro:
        logs = logs.filter(acao=acao_filtro)
    
    if usuario_filtro:
        logs = logs.filter(usuario_alterado_id=usuario_filtro)
    
    # Paginação
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Usuários para filtro
    usuarios_com_logs = User.objects.filter(
        logs_perfil_alterado__isnull=False
    ).distinct().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'acoes': LogAlteracaoPerfil.TIPOS_ACAO,
        'usuarios_com_logs': usuarios_com_logs,
        'acao_filtro': acao_filtro,
        'usuario_filtro': usuario_filtro,
    }
    
    return render(request, 'core/perfis/logs.html', context)


@login_required
def verificar_permissao_ajax(request):
    """Endpoint AJAX para verificar permissões"""
    if request.method == 'POST':
        modulo = request.POST.get('modulo')
        acao = request.POST.get('acao')
        
        if modulo and acao:
            tem_permissao = verificar_permissao_usuario(request.user, modulo, acao)
            return JsonResponse({'tem_permissao': tem_permissao})
    
    return JsonResponse({'erro': 'Parâmetros inválidos'}, status=400)


def get_client_ip(request):
    """Obtém o IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip