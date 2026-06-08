#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from core.models_perfil import UsuarioPerfil, PerfilUsuario

def verificar_criar_perfil_usuario():
    try:
        # Buscar o usuário teste_header
        usuario = User.objects.get(username='teste_header')
        print(f"Usuário encontrado: {usuario.username} (ID: {usuario.id})")
        
        # Verificar se já existe um UsuarioPerfil
        try:
            usuario_perfil = UsuarioPerfil.objects.get(usuario=usuario, ativo=True)
            print(f"Perfil encontrado: {usuario_perfil.perfil.nome} (Ativo: {usuario_perfil.ativo})")
            return usuario_perfil
        except UsuarioPerfil.DoesNotExist:
            print("Usuário não possui perfil ativo. Criando perfil...")
            
            # Buscar ou criar um perfil padrão
            try:
                perfil_admin = PerfilUsuario.objects.filter(nome__icontains='admin').first()
                if not perfil_admin:
                    perfil_admin = PerfilUsuario.objects.filter(nome__icontains='gerente').first()
                if not perfil_admin:
                    perfil_admin = PerfilUsuario.objects.first()
                
                if not perfil_admin:
                    print("Nenhum perfil encontrado no sistema. Criando perfil básico...")
                    perfil_admin = PerfilUsuario.objects.create(
                        nome='Administrador Teste',
                        tipo='administrador',
                        descricao='Perfil de administrador para testes',
                        ativo=True
                    )
                
                print(f"Usando perfil: {perfil_admin.nome}")
                
                # Criar UsuarioPerfil
                usuario_perfil = UsuarioPerfil.objects.create(
                    usuario=usuario,
                    perfil=perfil_admin,
                    ativo=True
                )
                
                print(f"Perfil criado com sucesso: {usuario_perfil.perfil.nome}")
                return usuario_perfil
                
            except Exception as e:
                print(f"Erro ao criar perfil: {e}")
                return None
                
    except User.DoesNotExist:
        print("Usuário teste_header não encontrado!")
        return None
    except Exception as e:
        print(f"Erro geral: {e}")
        return None

if __name__ == '__main__':
    print("=== Verificando/Criando Perfil de Usuário ===")
    resultado = verificar_criar_perfil_usuario()
    
    if resultado:
        print(f"\n✓ Usuário {resultado.usuario.username} tem perfil: {resultado.perfil.nome}")
    else:
        print("\n✗ Falha ao configurar perfil do usuário")