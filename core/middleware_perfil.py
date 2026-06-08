# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Middleware para Controle de Permissões por Perfil
"""

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from .models_perfil import UsuarioPerfil
import re


class ControlePermissaoPerfilMiddleware(MiddlewareMixin):
    """
    Middleware para controlar acesso baseado nos perfis de usuário
    """
    
    # URLs que não precisam de verificação de perfil
    URLS_EXCLUIDAS = [
        r'^/admin/',
        r'^/accounts/',
        r'^/static/',
        r'^/media/',
        r'^/api/',
        r'^/core/api/',  # APIs do módulo core (incluindo elementos editáveis)
        r'^/security/',
        r'^/$',  # Home
        r'^/core/perfil/',  # Página de perfil do usuário
        r'^/core/sobre/',  # Página sobre o sistema
    ]
    
    # Mapeamento de URLs para módulos e ações
    MAPEAMENTO_URLS = {
        # Imóveis
        r'^/imoveis/': {'modulo': 'imoveis', 'acao_padrao': 'visualizar'},
        r'^/imoveis/cadastrar/': {'modulo': 'imoveis', 'acao': 'criar'},
        r'^/imoveis/editar/': {'modulo': 'imoveis', 'acao': 'editar'},
        r'^/imoveis/excluir/': {'modulo': 'imoveis', 'acao': 'excluir'},
        r'^/imoveis/exportar/': {'modulo': 'imoveis', 'acao': 'exportar'},
        
        # Contratos
        r'^/contratos/': {'modulo': 'contratos', 'acao_padrao': 'visualizar'},
        r'^/contratos/cadastrar/': {'modulo': 'contratos', 'acao': 'criar'},
        r'^/contratos/editar/': {'modulo': 'contratos', 'acao': 'editar'},
        r'^/contratos/excluir/': {'modulo': 'contratos', 'acao': 'excluir'},
        r'^/contratos/aprovar/': {'modulo': 'contratos', 'acao': 'aprovar'},
        r'^/contratos/exportar/': {'modulo': 'contratos', 'acao': 'exportar'},
        
        # Financeiro
        r'^/financeiro/': {'modulo': 'financeiro', 'acao_padrao': 'visualizar'},
        r'^/financeiro/cadastrar/': {'modulo': 'financeiro', 'acao': 'criar'},
        r'^/financeiro/editar/': {'modulo': 'financeiro', 'acao': 'editar'},
        r'^/financeiro/excluir/': {'modulo': 'financeiro', 'acao': 'excluir'},
        r'^/financeiro/aprovar/': {'modulo': 'financeiro', 'acao': 'aprovar'},
        r'^/financeiro/exportar/': {'modulo': 'financeiro', 'acao': 'exportar'},
        
        # Pessoas (Proprietários e Inquilinos)
        r'^/core/proprietarios/': {'modulo': 'pessoas', 'acao_padrao': 'visualizar'},
        r'^/core/inquilinos/': {'modulo': 'pessoas', 'acao_padrao': 'visualizar'},
        r'^/core/proprietarios/cadastrar/': {'modulo': 'pessoas', 'acao': 'criar'},
        r'^/core/inquilinos/cadastrar/': {'modulo': 'pessoas', 'acao': 'criar'},
        r'^/core/proprietarios/editar/': {'modulo': 'pessoas', 'acao': 'editar'},
        r'^/core/inquilinos/editar/': {'modulo': 'pessoas', 'acao': 'editar'},
        r'^/core/proprietarios/excluir/': {'modulo': 'pessoas', 'acao': 'excluir'},
        r'^/core/inquilinos/excluir/': {'modulo': 'pessoas', 'acao': 'excluir'},
        
        # Manutenção
        r'^/manutencao/': {'modulo': 'manutencao', 'acao_padrao': 'visualizar'},
        r'^/manutencao/cadastrar/': {'modulo': 'manutencao', 'acao': 'criar'},
        r'^/manutencao/editar/': {'modulo': 'manutencao', 'acao': 'editar'},
        r'^/manutencao/excluir/': {'modulo': 'manutencao', 'acao': 'excluir'},
        
        # Documentos
        r'^/documentos/': {'modulo': 'documentos', 'acao_padrao': 'visualizar'},
        r'^/documentos/upload/': {'modulo': 'documentos', 'acao': 'criar'},
        r'^/documentos/editar/': {'modulo': 'documentos', 'acao': 'editar'},
        r'^/documentos/excluir/': {'modulo': 'documentos', 'acao': 'excluir'},
        
        # Notificações
        r'^/notificacoes/': {'modulo': 'notificacoes', 'acao_padrao': 'visualizar'},
        r'^/notificacoes/enviar/': {'modulo': 'notificacoes', 'acao': 'criar'},
        r'^/notificacoes/editar/': {'modulo': 'notificacoes', 'acao': 'editar'},
        r'^/notificacoes/excluir/': {'modulo': 'notificacoes', 'acao': 'excluir'},
        
        # Relatórios
        r'^/relatorios/': {'modulo': 'relatorios', 'acao_padrao': 'visualizar'},
        r'^/relatorios/exportar/': {'modulo': 'relatorios', 'acao': 'exportar'},
        
        # Configurações
        r'^/configuracoes/': {'modulo': 'configuracoes', 'acao_padrao': 'visualizar'},
        r'^/configuracoes/editar/': {'modulo': 'configuracoes', 'acao': 'editar'},
        
        # Bancas de Feira
        r'^/core/bancas/': {'modulo': 'bancas', 'acao_padrao': 'visualizar'},
        r'^/core/bancas/cadastrar/': {'modulo': 'bancas', 'acao': 'criar'},
        r'^/core/bancas/editar/': {'modulo': 'bancas', 'acao': 'editar'},
        r'^/core/bancas/excluir/': {'modulo': 'bancas', 'acao': 'excluir'},
    }
    
    def process_request(self, request):
        # Pular verificação para usuários não autenticados
        if not request.user.is_authenticated:
            return None
        
        # Pular verificação para superusuários
        if request.user.is_superuser:
            return None
        
        # Pular verificação para usuários master
        if hasattr(request.user, 'master_profile'):
            return None
        
        # Verificar se a URL está nas excluídas
        path = request.path
        for url_pattern in self.URLS_EXCLUIDAS:
            if re.match(url_pattern, path):
                return None
        
        # Verificar se o usuário tem perfil
        try:
            usuario_perfil = UsuarioPerfil.objects.get(usuario=request.user, ativo=True)
        except UsuarioPerfil.DoesNotExist:
            # Verificar se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'no_profile',
                    'message': 'Seu usuário não possui um perfil definido. Entre em contato com o administrador.',
                    'redirect_url': reverse('core:perfil')
                }, status=403)
            
            # Usuário sem perfil - redirecionar para página de erro
            messages.error(request, 'Seu usuário não possui um perfil definido. Entre em contato com o administrador.')
            return redirect('core:perfil')
        
        # Verificar permissões para a URL atual
        permissao_necessaria = self.obter_permissao_necessaria(path, request.method)
        
        if permissao_necessaria:
            modulo = permissao_necessaria['modulo']
            acao = permissao_necessaria['acao']
            
            if not usuario_perfil.tem_permissao(modulo, acao):
                # Verificar se é uma requisição AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': False,
                        'error': 'no_permission',
                        'message': f'Você não tem permissão para {acao} em {modulo}.',
                        'profile': usuario_perfil.perfil.nome
                    }, status=403)
                
                # Usuário sem permissão
                messages.error(request, f'Você não tem permissão para {acao} em {modulo}.')
                return HttpResponseForbidden(
                    f'<h1>Acesso Negado</h1>'
                    f'<p>Você não tem permissão para {acao} em {modulo}.</p>'
                    f'<p>Seu perfil: {usuario_perfil.perfil.nome}</p>'
                    f'<a href="/">Voltar ao início</a>'
                )
        
        return None
    
    def obter_permissao_necessaria(self, path, method):
        """
        Determina qual permissão é necessária para a URL e método HTTP
        """
        for url_pattern, config in self.MAPEAMENTO_URLS.items():
            if re.match(url_pattern, path):
                modulo = config['modulo']
                
                # Determinar ação baseada na URL específica ou método HTTP
                if 'acao' in config:
                    acao = config['acao']
                elif method == 'POST':
                    if 'cadastrar' in path or 'criar' in path:
                        acao = 'criar'
                    elif 'editar' in path:
                        acao = 'editar'
                    elif 'excluir' in path:
                        acao = 'excluir'
                    else:
                        acao = config.get('acao_padrao', 'visualizar')
                elif method == 'DELETE':
                    acao = 'excluir'
                elif method == 'PUT' or method == 'PATCH':
                    acao = 'editar'
                else:
                    acao = config.get('acao_padrao', 'visualizar')
                
                return {'modulo': modulo, 'acao': acao}
        
        return None


def verificar_permissao_usuario(user, modulo, acao):
    """
    Função utilitária para verificar permissões em views
    """
    if user.is_superuser:
        return True
    
    if hasattr(user, 'master_profile'):
        return True
    
    try:
        usuario_perfil = UsuarioPerfil.objects.get(usuario=user, ativo=True)
        return usuario_perfil.tem_permissao(modulo, acao)
    except UsuarioPerfil.DoesNotExist:
        return False


def require_permission(modulo, acao):
    """
    Decorator para views que requer permissão específica
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not verificar_permissao_usuario(request.user, modulo, acao):
                messages.error(request, f'Você não tem permissão para {acao} em {modulo}.')
                return HttpResponseForbidden(
                    f'<h1>Acesso Negado</h1>'
                    f'<p>Você não tem permissão para {acao} em {modulo}.</p>'
                    f'<a href="/">Voltar ao início</a>'
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator