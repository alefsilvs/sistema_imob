from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import logging

logger = logging.getLogger(__name__)

@require_POST
@csrf_protect
@login_required
def custom_logout(request):
    """
    View customizada de logout com limpeza completa da sessão
    para evitar vazamento de dados entre usuários
    """
    user = request.user
    tenant_id = request.session.get('tenant_id')
    
    # Log do logout para auditoria
    logger.info(f"Logout do usuário: {user.username} (Tenant ID: {tenant_id})")
    
    # Fazer logout do usuário
    logout(request)
    
    # SEGURANÇA: Limpar completamente a sessão
    request.session.flush()
    
    # Regenerar a chave da sessão para evitar fixação de sessão
    request.session.cycle_key()
    
    messages.success(request, 'Logout realizado com sucesso!')
    
    # Redirecionar para a página de planos
    return redirect('saas:planos')