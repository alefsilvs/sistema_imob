# Script para corrigir perfil do usuário admin
from django.contrib.auth.models import User
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil

print("=== VERIFICAÇÃO DO PERFIL DO USUÁRIO ADMIN ===")

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
            print("⚠️  Usuário não tem permissão para acessar relatórios!")
        else:
            print("✅ Usuário tem as permissões necessárias!")
            
    else:
        print("❌ Usuário admin NÃO tem perfil_usuario associado!")
        print("🔧 Criando perfil para o usuário admin...")
        
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
            print("✅ Perfil 'Administrador' criado!")
            
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
            print("✅ Perfil 'Administrador' já existe!")
        
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
            print("✅ Perfil associado ao usuário admin!")
        else:
            print("✅ Associação já existe!")
            # Garantir que está ativo
            if not usuario_perfil.ativo:
                usuario_perfil.ativo = True
                usuario_perfil.save()
                print("✅ Perfil reativado!")
        
        print("✅ Correção concluída! Usuário admin agora tem perfil completo.")
        
except User.DoesNotExist:
    print("❌ Usuário admin não encontrado!")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")

# Verificar resultado final
try:
    admin_user = User.objects.get(username='admin')
    if hasattr(admin_user, 'perfil_usuario'):
        tem_permissao = admin_user.perfil_usuario.tem_permissao('relatorios', 'visualizar')
        print(f"\n🎯 RESULTADO FINAL: Permissão 'relatorios/visualizar' = {tem_permissao}")
    else:
        print("\n❌ RESULTADO FINAL: Ainda sem perfil!")
except:
    print("\n❌ ERRO na verificação final!")