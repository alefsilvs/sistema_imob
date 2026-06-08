from django.contrib import admin
from .models_perfil import PerfilUsuario, AbrangenciaPerfil, UsuarioPerfil, LogAlteracaoPerfil
from .admin_perfil import PerfilUsuarioAdmin, AbrangenciaPerfilAdmin, UsuarioPerfilAdmin, LogAlteracaoPerfilAdmin

# Register your models here.

# Registrar modelos de perfil
admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)
admin.site.register(AbrangenciaPerfil, AbrangenciaPerfilAdmin)
admin.site.register(UsuarioPerfil, UsuarioPerfilAdmin)
admin.site.register(LogAlteracaoPerfil, LogAlteracaoPerfilAdmin)
