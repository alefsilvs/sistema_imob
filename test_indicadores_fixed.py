import os
import django
from django.conf import settings
import random
import string

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from core.models import PerfilUsuario

def test_indicadores_page():
    """Testa o acesso à página de indicadores"""
    client = Client()
    
    # Gerar nome de usuário único
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    username = f'test_user_{random_suffix}'
    
    # Criar usuário de teste
    user = User.objects.create_user(
        username=username,
        email=f'test_{random_suffix}@example.com',
        password='testpass123'
    )
    
    # Criar perfil de usuário (ou usar existente)
    perfil_usuario, created = PerfilUsuario.objects.get_or_create(
        nome='Administrador Teste',
        defaults={
            'tipo': 'administrador',
            'descricao': 'Perfil de teste para administrador',
            'ativo': True
        }
    )
    
    # Associar usuário ao perfil
    from core.models_perfil import UsuarioPerfil, AbrangenciaPerfil
    usuario_perfil, created = UsuarioPerfil.objects.get_or_create(
        usuario=user,
        defaults={
            'perfil': perfil_usuario,
            'ativo': True
        }
    )
    
    # Criar permissão para acessar relatórios
    AbrangenciaPerfil.objects.get_or_create(
        perfil=perfil_usuario,
        modulo='relatorios',
        acao='visualizar',
        defaults={'permitido': True}
    )
    
    # Fazer login
    client.login(username=username, password='testpass123')
    
    # Testar acesso à página de indicadores
    response = client.get('/indicadores/dashboard/')
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Página de indicadores carregada com sucesso!")
    else:
        print(f"❌ Erro ao carregar página: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Conteúdo do erro: {response.content.decode()[:500]}")
    
    # Limpar dados de teste
    user.delete()

if __name__ == "__main__":
    test_indicadores_page()