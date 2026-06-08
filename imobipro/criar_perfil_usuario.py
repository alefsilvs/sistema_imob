#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar PerfilUsuario para todos os usuários que não possuem
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil


def criar_perfil_padrao():
    """
    Cria um perfil padrão se não existir
    """
    perfil_padrao, created = PerfilUsuario.objects.get_or_create(
        nome='Usuário Padrão',
        defaults={
            'tipo': 'consulta',
            'descricao': 'Perfil padrão para usuários sem perfil específico',
            'ativo': True
        }
    )
    
    if created:
        print(f"✅ Perfil padrão criado: {perfil_padrao.nome}")
        
        # Criar permissões básicas para o perfil padrão
        permissoes_basicas = [
            ('imoveis', 'visualizar'),
            ('contratos', 'visualizar'),
            ('pessoas', 'visualizar'),
            ('bancas', 'visualizar'),
            ('relatorios', 'visualizar'),
        ]
        
        for modulo, acao in permissoes_basicas:
            AbrangenciaPerfil.objects.get_or_create(
                perfil=perfil_padrao,
                modulo=modulo,
                acao=acao,
                defaults={'permitido': True}
            )
        
        print(f"✅ Permissões básicas criadas para o perfil padrão")
    else:
        print(f"ℹ️  Perfil padrão já existe: {perfil_padrao.nome}")
    
    return perfil_padrao


def criar_perfil_administrador():
    """
    Cria um perfil de administrador se não existir
    """
    perfil_admin, created = PerfilUsuario.objects.get_or_create(
        nome='Administrador',
        defaults={
            'tipo': 'administrador',
            'descricao': 'Perfil com acesso total ao sistema',
            'ativo': True
        }
    )
    
    if created:
        print(f"✅ Perfil administrador criado: {perfil_admin.nome}")
        
        # Criar todas as permissões para o administrador
        modulos = [choice[0] for choice in AbrangenciaPerfil.MODULOS]
        acoes = [choice[0] for choice in AbrangenciaPerfil.ACOES]
        
        for modulo in modulos:
            for acao in acoes:
                AbrangenciaPerfil.objects.get_or_create(
                    perfil=perfil_admin,
                    modulo=modulo,
                    acao=acao,
                    defaults={'permitido': True}
                )
        
        print(f"✅ Todas as permissões criadas para o perfil administrador")
    else:
        print(f"ℹ️  Perfil administrador já existe: {perfil_admin.nome}")
    
    return perfil_admin


def associar_usuarios_perfis():
    """
    Associa todos os usuários sem perfil ao perfil padrão
    """
    perfil_padrao = criar_perfil_padrao()
    perfil_admin = criar_perfil_administrador()
    
    usuarios_sem_perfil = User.objects.filter(perfil_usuario__isnull=True)
    
    print(f"\n📊 Encontrados {usuarios_sem_perfil.count()} usuários sem perfil")
    
    for usuario in usuarios_sem_perfil:
        # Se for superuser, associar ao perfil administrador
        if usuario.is_superuser:
            perfil_escolhido = perfil_admin
            tipo_perfil = "administrador"
        else:
            perfil_escolhido = perfil_padrao
            tipo_perfil = "padrão"
        
        usuario_perfil = UsuarioPerfil.objects.create(
            usuario=usuario,
            perfil=perfil_escolhido,
            ativo=True,
            observacoes=f"Perfil criado automaticamente pelo script de correção"
        )
        
        print(f"✅ Usuário '{usuario.username}' associado ao perfil {tipo_perfil}")
    
    print(f"\n✅ Processo concluído! Todos os usuários agora possuem perfil.")


def verificar_perfis_existentes():
    """
    Verifica e exibe informações sobre os perfis existentes
    """
    print("\n📋 RELATÓRIO DE PERFIS:")
    print("=" * 50)
    
    total_usuarios = User.objects.count()
    usuarios_com_perfil = User.objects.filter(perfil_usuario__isnull=False).count()
    usuarios_sem_perfil = total_usuarios - usuarios_com_perfil
    
    print(f"👥 Total de usuários: {total_usuarios}")
    print(f"✅ Usuários com perfil: {usuarios_com_perfil}")
    print(f"❌ Usuários sem perfil: {usuarios_sem_perfil}")
    
    if usuarios_sem_perfil > 0:
        print(f"\n⚠️  Usuários sem perfil:")
        for usuario in User.objects.filter(perfil_usuario__isnull=True):
            tipo = "Superuser" if usuario.is_superuser else "Usuário comum"
            print(f"   - {usuario.username} ({tipo})")
    
    print(f"\n📊 Perfis disponíveis:")
    for perfil in PerfilUsuario.objects.all():
        usuarios_count = UsuarioPerfil.objects.filter(perfil=perfil, ativo=True).count()
        status = "Ativo" if perfil.ativo else "Inativo"
        print(f"   - {perfil.nome} ({perfil.get_tipo_display()}) - {usuarios_count} usuários - {status}")


if __name__ == '__main__':
    print("🔧 SCRIPT DE CORREÇÃO DE PERFIS DE USUÁRIO")
    print("=" * 50)
    
    try:
        # Verificar situação atual
        verificar_perfis_existentes()
        
        # Perguntar se deve prosseguir
        if len(sys.argv) > 1 and sys.argv[1] == '--auto':
            resposta = 'y'
        else:
            resposta = input("\n❓ Deseja criar perfis para os usuários sem perfil? (y/n): ").lower()
        
        if resposta in ['y', 'yes', 's', 'sim']:
            print("\n🚀 Iniciando processo de correção...")
            associar_usuarios_perfis()
            
            # Verificar novamente após as correções
            print("\n" + "=" * 50)
            verificar_perfis_existentes()
        else:
            print("\n❌ Operação cancelada pelo usuário.")
    
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {str(e)}")
        import traceback
        traceback.print_exc()