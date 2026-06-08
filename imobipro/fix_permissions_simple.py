# Corrigir permissões do admin
from django.contrib.auth.models import User
from core.models_perfil import PerfilUsuario, UsuarioPerfil, AbrangenciaPerfil

admin = User.objects.get(username='admin')
perfil = admin.perfil_usuario.perfil

# Adicionar permissão de relatórios
perm, created = AbrangenciaPerfil.objects.get_or_create(
    perfil=perfil,
    modulo='relatorios',
    acao='visualizar',
    defaults={'permitido': True}
)

if not perm.permitido:
    perm.permitido = True
    perm.save()

print("Permissão adicionada!")
print(f"Teste: {admin.perfil_usuario.tem_permissao('relatorios', 'visualizar')}")