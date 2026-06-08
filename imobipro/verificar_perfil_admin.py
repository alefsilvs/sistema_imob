#!/usr/bin/env python
"""
Script para verificar e corrigir o perfil do usuário admin
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imo.settings')
django.setup()

from django.contrib.auth.models import User
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil

def verificar_e_corrigir_perfil_admin():
    """
    Verifica se o usuário admin tem perfil e cria um se necessário
    """
    print("=== VERIFICAÇÃO DO PERFIL DO USUÁRIO ADMIN ===\n")
    
    try:
        # Buscar usuário admin
        admin_user = User.objects.get(username='admin')
        print(f"✅ Usuário admin encontrado: {admin_user.username}")
        
        # Verificar se tem perfil_usuario
        if hasattr(admin_user, 'perfil_usuario'):
            perfil_usuario = admin_user.perfil_usuario
            print(f"✅ Perfil encontrado: {perfil_usuario.perfil.nome}")
            print(f"   - Ativo: {perfil_usuario.ativo}")
            print(f"   - Perfil ativo: {perfil_usuario.perfil.ativo}")
            
            # Testar permissão específica
            tem_permissao = perfil_usuario.tem_permissao('relatorios', 'visualizar')
            print(f"   - Tem permissão 'relatorios/visualizar': {tem_permissao}")
            
            if not tem_permissao:
                print("\n⚠️  Usuário não tem permissão para acessar relatórios!")
                return False
            else:
                print("\n✅ Usuário tem as permissões necessárias!")
                return True
                
        else:
            print("❌ Usuário admin NÃO tem perfil_usuario associado!")
            print("\n🔧 Criando perfil para o usuário admin...")
            
            # Buscar ou criar perfil de administrador
            perfil_admin, created = PerfilUsuario.objects.get_or_create(
                nome='Administrador',
                defaults={
                    'tipo': 'administrador',
                    'descricao': 'Perfil com acesso total ao sistema',
                    'ativo': True
                }
            )
            
            if created:
                print(f"✅ Perfil 'Administrador' criado!")
                
                # Criar todas as permissões para o perfil de administrador
                modulos = dict(AbrangenciaPerfil.MODULOS)
                acoes = dict(AbrangenciaPerfil.ACOES)
                
                print("🔧 Criando permissões completas...")
                for modulo_key in modulos.keys():
                    for acao_key in acoes.keys():
                        AbrangenciaPerfil.objects.get_or_create(
                            perfil=perfil_admin,
                            modulo=modulo_key,
                            acao=acao_key,
                            defaults={'permitido': True}
                        )
                
                print(f"✅ Permissões criadas para {len(modulos)} módulos e {len(acoes)} ações!")
            else:
                print(f"✅ Perfil 'Administrador' já existe!")
            
            # Associar perfil ao usuário admin
            usuario_perfil, created = UsuarioPerfil.objects.get_or_create(
                usuario=admin_user,
                defaults={
                    'perfil': perfil_admin,
                    'ativo': True,
                    'observacoes': 'Perfil criado automaticamente para usuário admin'
                }
            )
            
            if created:
                print(f"✅ Perfil associado ao usuário admin!")
            else:
                print(f"✅ Associação já existe!")
                # Garantir que está ativo
                if not usuario_perfil.ativo:
                    usuario_perfil.ativo = True
                    usuario_perfil.save()
                    print("✅ Perfil reativado!")
            
            print("\n✅ Correção concluída! Usuário admin agora tem perfil completo.")
            return True
            
    except User.DoesNotExist:
        print("❌ Usuário admin não encontrado!")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def listar_usuarios_sem_perfil():
    """
    Lista todos os usuários que não têm perfil
    """
    print("\n=== USUÁRIOS SEM PERFIL ===")
    
    usuarios_sem_perfil = User.objects.filter(perfil_usuario__isnull=True)
    
    if usuarios_sem_perfil.exists():
        print(f"⚠️  Encontrados {usuarios_sem_perfil.count()} usuários sem perfil:")
        for user in usuarios_sem_perfil:
            print(f"   - {user.username} ({user.get_full_name() or 'Sem nome'})")
    else:
        print("✅ Todos os usuários têm perfil associado!")

if __name__ == "__main__":
    sucesso = verificar_e_corrigir_perfil_admin()
    listar_usuarios_sem_perfil()
    
    if sucesso:
        print("\n🎉 Correção realizada com sucesso!")
        print("   Agora você pode acessar a página de indicadores sem erro.")
    else:
        print("\n❌ Houve problemas na correção.")