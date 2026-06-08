import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from core.models import PerfilUsuario

def test_indicadores():
    print("Iniciando teste de indicadores...")
    
    try:
        client = Client()
        
        # Criar usuário de teste
        username = 'test_indicadores_user'
        
        # Remover usuário se já existir
        User.objects.filter(username=username).delete()
        
        user = User.objects.create_user(
            username=username,
            email='test@example.com',
            password='testpass123'
        )
        print(f"Usuário criado: {user.username}")
        
        # Criar perfil de usuário
        perfil_usuario, created = PerfilUsuario.objects.get_or_create(
            nome='Admin Teste',
            defaults={
                'tipo': 'administrador',
                'descricao': 'Perfil de teste',
                'ativo': True
            }
        )
        print(f"Perfil criado/encontrado: {perfil_usuario.nome}")
        
        # Associar usuário ao perfil
        from core.models_perfil import UsuarioPerfil, AbrangenciaPerfil
        usuario_perfil, created = UsuarioPerfil.objects.get_or_create(
            usuario=user,
            defaults={
                'perfil': perfil_usuario,
                'ativo': True
            }
        )
        print(f"Usuário associado ao perfil: {usuario_perfil}")
        
        # Criar permissão
        AbrangenciaPerfil.objects.get_or_create(
            perfil=perfil_usuario,
            modulo='relatorios',
            acao='visualizar',
            defaults={'permitido': True}
        )
        print("Permissão criada")
        
        # Fazer login
        login_result = client.login(username=username, password='testpass123')
        print(f"Login realizado: {login_result}")
        
        # Testar acesso à página
        print("Acessando página de indicadores...")
        response = client.get('/indicadores/dashboard/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCESSO: Página de indicadores carregada!")
        elif response.status_code == 302:
            print(f"⚠️  REDIRECIONAMENTO: {response.get('Location', 'Local não especificado')}")
        else:
            print(f"❌ ERRO: Status {response.status_code}")
            
        # Limpar
        user.delete()
        print("Usuário de teste removido")
        
    except Exception as e:
        print(f"❌ ERRO DURANTE TESTE: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_indicadores()