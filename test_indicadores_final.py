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
        
        # Usar usuário existente ou criar um novo
        username = 'test_indicadores_user'
        
        # Tentar encontrar usuário existente
        try:
            user = User.objects.get(username=username)
            print(f"Usuario existente encontrado: {user.username}")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='test@example.com',
                password='testpass123'
            )
            print(f"Usuario criado: {user.username}")
        
        # Criar perfil de usuário
        perfil_usuario, created = PerfilUsuario.objects.get_or_create(
            nome='Admin Teste',
            defaults={
                'tipo': 'administrador',
                'descricao': 'Perfil de teste',
                'ativo': True
            }
        )
        print(f"Perfil: {perfil_usuario.nome}")
        
        # Associar usuário ao perfil
        from core.models_perfil import UsuarioPerfil, AbrangenciaPerfil
        usuario_perfil, created = UsuarioPerfil.objects.get_or_create(
            usuario=user,
            defaults={
                'perfil': perfil_usuario,
                'ativo': True
            }
        )
        print(f"Usuario associado ao perfil")
        
        # Criar permissão
        AbrangenciaPerfil.objects.get_or_create(
            perfil=perfil_usuario,
            modulo='relatorios',
            acao='visualizar',
            defaults={'permitido': True}
        )
        print("Permissao criada")
        
        # Fazer login
        login_result = client.login(username=username, password='testpass123')
        print(f"Login realizado: {login_result}")
        
        # Testar acesso à página
        print("Acessando pagina de indicadores...")
        response = client.get('/indicadores/dashboard/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCESSO: Pagina de indicadores carregada!")
            return True
        elif response.status_code == 302:
            location = response.get('Location', 'Local nao especificado')
            print(f"REDIRECIONAMENTO: {location}")
            return False
        else:
            print(f"ERRO: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO DURANTE TESTE: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_indicadores()
    if success:
        print("TESTE CONCLUIDO COM SUCESSO!")
    else:
        print("TESTE FALHOU!")