import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from core.views import dashboard

def test_dashboard_directly():
    """Testa a view dashboard diretamente para capturar o erro"""
    
    try:
        # Criar um request factory
        factory = RequestFactory()
        
        # Obter o usuário admin
        user = User.objects.get(username='admin')
        
        # Criar request
        request = factory.get('/dashboard/')
        request.user = user
        
        # Adicionar session
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Adicionar messages
        messages_middleware = MessageMiddleware(lambda x: None)
        messages_middleware.process_request(request)
        
        # Tentar executar a view
        print("Executando view dashboard...")
        response = dashboard(request)
        print(f"Sucesso! Status: {response.status_code}")
        
        # Salvar HTML se sucesso
        if hasattr(response, 'content'):
            with open('temp_dashboard_success.html', 'w', encoding='utf-8') as f:
                f.write(response.content.decode('utf-8'))
            print("HTML salvo em: temp_dashboard_success.html")
        
    except Exception as e:
        print(f"ERRO CAPTURADO: {type(e).__name__}: {e}")
        
        # Imprimir traceback completo
        import traceback
        print("\nTRACEBACK COMPLETO:")
        traceback.print_exc()
        
        # Tentar identificar o problema específico
        if 'FieldError' in str(e):
            print(f"\nERRO DE CAMPO DETECTADO: {e}")
            
            # Verificar se é problema com tenant
            if 'tenant' in str(e).lower():
                print("Problema relacionado ao campo 'tenant'")
            
            # Verificar se é problema com relacionamentos
            if 'join' in str(e).lower() or 'related' in str(e).lower():
                print("Problema relacionado a joins/relacionamentos")

if __name__ == "__main__":
    test_dashboard_directly()