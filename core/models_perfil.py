# -*- coding: utf-8 -*-
"""
Sistema Imobiliário - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Sistema de Perfis de Usuário com Abrangências
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class PerfilUsuario(models.Model):
    """
    Modelo para definir perfis de usuário no sistema
    """
    TIPOS_PERFIL = [
        ('administrador', 'Administrador'),
        ('gerente', 'Gerente'),
        ('corretor', 'Corretor'),
        ('financeiro', 'Financeiro'),
        ('atendimento', 'Atendimento'),
        ('consulta', 'Consulta'),
    ]
    
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome do Perfil')
    tipo = models.CharField(max_length=20, choices=TIPOS_PERFIL, verbose_name='Tipo de Perfil')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuário'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class AbrangenciaPerfil(models.Model):
    """
    Modelo para definir as abrangências/permissões de cada perfil
    """
    MODULOS = [
        ('imoveis', 'Imóveis'),
        ('contratos', 'Contratos'),
        ('financeiro', 'Financeiro'),
        ('pessoas', 'Pessoas'),
        ('manutencao', 'Manutenção'),
        ('documentos', 'Documentos'),
        ('notificacoes', 'Notificações'),
        ('relatorios', 'Relatórios'),
        ('configuracoes', 'Configurações'),
        ('bancas', 'Bancas de Feira'),
    ]
    
    ACOES = [
        ('visualizar', 'Visualizar'),
        ('criar', 'Criar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
        ('aprovar', 'Aprovar'),
        ('exportar', 'Exportar'),
    ]
    
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='abrangencias')
    modulo = models.CharField(max_length=20, choices=MODULOS, verbose_name='Módulo')
    acao = models.CharField(max_length=20, choices=ACOES, verbose_name='Ação')
    permitido = models.BooleanField(default=True, verbose_name='Permitido')
    
    class Meta:
        verbose_name = 'Abrangência de Perfil'
        verbose_name_plural = 'Abrangências de Perfil'
        unique_together = ['perfil', 'modulo', 'acao']
    
    def __str__(self):
        status = "Permitido" if self.permitido else "Negado"
        return f"{self.perfil.nome} - {self.get_modulo_display()} - {self.get_acao_display()} ({status})"


class UsuarioPerfil(models.Model):
    """
    Modelo para associar usuários aos perfis
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_usuario')
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, verbose_name='Perfil')
    data_atribuicao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Atribuição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Usuário com Perfil'
        verbose_name_plural = 'Usuários com Perfil'
    
    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.perfil.nome}"
    
    def tem_permissao(self, modulo, acao):
        """
        Verifica se o usuário tem permissão para uma ação específica em um módulo
        """
        if not self.ativo or not self.perfil.ativo:
            return False
        
        try:
            abrangencia = AbrangenciaPerfil.objects.get(
                perfil=self.perfil,
                modulo=modulo,
                acao=acao
            )
            return abrangencia.permitido
        except AbrangenciaPerfil.DoesNotExist:
            return False
    
    def get_permissoes_modulo(self, modulo):
        """
        Retorna todas as permissões do usuário para um módulo específico
        """
        if not self.ativo or not self.perfil.ativo:
            return []
        
        abrangencias = AbrangenciaPerfil.objects.filter(
            perfil=self.perfil,
            modulo=modulo,
            permitido=True
        )
        return [abr.acao for abr in abrangencias]


class LogAlteracaoPerfil(models.Model):
    """
    Log de alterações nos perfis de usuário
    """
    TIPOS_ACAO = [
        ('criacao', 'Criação'),
        ('edicao', 'Edição'),
        ('exclusao', 'Exclusão'),
        ('ativacao', 'Ativação'),
        ('desativacao', 'Desativação'),
        ('atribuicao', 'Atribuição de Perfil'),
        ('remocao', 'Remoção de Perfil'),
    ]
    
    usuario_alterado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs_perfil_alterado')
    usuario_responsavel = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs_perfil_responsavel')
    acao = models.CharField(max_length=20, choices=TIPOS_ACAO, verbose_name='Ação')
    perfil_anterior = models.CharField(max_length=100, blank=True, verbose_name='Perfil Anterior')
    perfil_novo = models.CharField(max_length=100, blank=True, verbose_name='Perfil Novo')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes')
    data_alteracao = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(verbose_name='IP')
    
    class Meta:
        verbose_name = 'Log de Alteração de Perfil'
        verbose_name_plural = 'Logs de Alterações de Perfil'
        ordering = ['-data_alteracao']
    
    def __str__(self):
        return f"{self.usuario_alterado.username} - {self.get_acao_display()} - {self.data_alteracao.strftime('%d/%m/%Y %H:%M')}"


# Função utilitária para verificar permissões
def verificar_permissao(usuario, modulo, acao):
    """
    Verifica se um usuário tem permissão para executar uma ação em um módulo
    
    Args:
        usuario: Instância do User
        modulo: String do módulo (ex: 'imoveis', 'contratos')
        acao: String da ação (ex: 'visualizar', 'criar', 'editar')
    
    Returns:
        bool: True se tem permissão, False caso contrário
    """
    try:
        # Verificar se o usuário é superuser
        if usuario.is_superuser:
            return True
        
        # Verificar se o usuário tem perfil
        if not hasattr(usuario, 'perfil_usuario'):
            return False
        
        usuario_perfil = usuario.perfil_usuario
        
        # Verificar se o perfil está ativo
        if not usuario_perfil.ativo or not usuario_perfil.perfil.ativo:
            return False
        
        # Verificar permissão específica
        return usuario_perfil.tem_permissao(modulo, acao)
        
    except Exception:
        return False


def get_permissoes_usuario(usuario):
    """
    Retorna todas as permissões de um usuário
    
    Args:
        usuario: Instância do User
    
    Returns:
        dict: Dicionário com as permissões por módulo
    """
    try:
        if usuario.is_superuser:
            # Superuser tem todas as permissões
            modulos = dict(AbrangenciaPerfil.MODULOS)
            acoes = dict(AbrangenciaPerfil.ACOES)
            
            permissoes = {}
            for modulo_key in modulos.keys():
                permissoes[modulo_key] = list(acoes.keys())
            
            return permissoes
        
        if not hasattr(usuario, 'perfil_usuario'):
            return {}
        
        usuario_perfil = usuario.perfil_usuario
        
        if not usuario_perfil.ativo or not usuario_perfil.perfil.ativo:
            return {}
        
        # Buscar todas as abrangências do perfil
        abrangencias = AbrangenciaPerfil.objects.filter(
            perfil=usuario_perfil.perfil,
            permitido=True
        )
        
        permissoes = {}
        for abrangencia in abrangencias:
            if abrangencia.modulo not in permissoes:
                permissoes[abrangencia.modulo] = []
            permissoes[abrangencia.modulo].append(abrangencia.acao)
        
        return permissoes
        
    except Exception:
        return {}