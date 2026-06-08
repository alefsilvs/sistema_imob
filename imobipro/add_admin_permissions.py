# Script para adicionar permissões ao perfil do usuário admin
from django.contrib.auth.models import User
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil

print("=== ADICIONANDO PERMISSÕES AO PERFIL DO ADMIN ===")

try:
    # Buscar usuário admin
    admin_user = User.objects.get(username='admin')
    print(f"✅ Usuário admin encontrado: {admin_user.username}")
    
    # Verificar perfil
    if hasattr(admin_user, 'perfil_usuario'):
        perfil_usuario = admin_user.perfil_usuario
        perfil = perfil_usuario.perfil
        print(f"✅ Perfil encontrado: {perfil.nome}")
        
        # Verificar permissões atuais
        print("\n🔍 Verificando permissões atuais...")
        
        # Módulos e ações importantes
        permissoes_necessarias = [
            ('relatorios', 'visualizar'),
            ('relatorios', 'editar'),
            ('imoveis', 'visualizar'),
            ('contratos', 'visualizar'),
            ('financeiro', 'visualizar'),
            ('configuracoes', 'visualizar'),
            ('configuracoes', 'editar'),
        ]
        
        permissoes_adicionadas = 0
        
        for modulo, acao in permissoes_necessarias:
            # Verificar se já tem a permissão
            tem_permissao = perfil_usuario.tem_permissao(modulo, acao)
            
            if not tem_permissao:
                # Criar a permissão
                abrangencia, created = AbrangenciaPerfil.objects.get_or_create(
                    perfil=perfil,
                    modulo=modulo,
                    acao=acao,
                    defaults={'permitido': True}
                )
                
                if created:
                    print(f"   ✅ Adicionada: {modulo}/{acao}")
                    permissoes_adicionadas += 1
                else:
                    # Se já existe mas não está permitida, ativar
                    if not abrangencia.permitido:
                        abrangencia.permitido = True
                        abrangencia.save()
                        print(f"   ✅ Ativada: {modulo}/{acao}")
                        permissoes_adicionadas += 1
                    else:
                        print(f"   ℹ️  Já existe: {modulo}/{acao}")
            else:
                print(f"   ✅ OK: {modulo}/{acao}")
        
        print(f"\n🎯 Total de permissões adicionadas/ativadas: {permissoes_adicionadas}")
        
        # Verificar resultado final
        print("\n🔍 Verificação final...")
        tem_relatorios = perfil_usuario.tem_permissao('relatorios', 'visualizar')
        print(f"   - Permissão 'relatorios/visualizar': {tem_relatorios}")
        
        if tem_relatorios:
            print("\n🎉 SUCESSO! Usuário admin agora pode acessar os indicadores!")
        else:
            print("\n❌ ERRO! Ainda não conseguiu adicionar a permissão.")
            
    else:
        print("❌ Usuário admin não tem perfil_usuario associado!")
        
except User.DoesNotExist:
    print("❌ Usuário admin não encontrado!")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()