from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import logging

from .models import Tenant

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def configurar_tenant_na_sessao(sender, request, user, **kwargs):
    """
    Signal executado após login bem-sucedido para configurar o tenant_id na sessão
    """
    try:
        # Verificar se o usuário tem um tenant
        tenant = Tenant.objects.filter(usuario_admin=user).first()
        
        if tenant:
            # Configurar tenant_id na sessão
            request.session['tenant_id'] = tenant.id
            logger.info(f"Tenant ID {tenant.id} configurado na sessão para usuário {user.username}")
            
            # Verificar status do tenant
            if tenant.status == 'pendente_pagamento':
                messages.warning(
                    request, 
                    'Seu pagamento está pendente. Complete o pagamento para acessar todas as funcionalidades.'
                )
            elif tenant.status == 'trial':
                if not tenant.is_trial_ativo:
                    messages.warning(
                        request,
                        'Seu período de trial expirou. Escolha um plano para continuar usando o sistema.'
                    )
                else:
                    # Calcular dias restantes do trial
                    dias_restantes = (tenant.trial_ate - timezone.now()).days if tenant.trial_ate else 0
                    if dias_restantes <= 7:
                        messages.info(
                            request,
                            f'Seu trial expira em {dias_restantes} dias. Considere escolher um plano.'
                        )
        else:
            logger.info(f"Usuário {user.username} não possui tenant associado")
            
    except Exception as e:
        logger.error(f"Erro ao configurar tenant na sessão para usuário {user.username}: {str(e)}")


@receiver(post_save, sender=Tenant)
def create_database_schema_for_tenant(sender, instance, created, **kwargs):
    if created:
        try:
            from .database_isolation import TenantDatabaseManager
            TenantDatabaseManager().create_tenant_schema(instance)
        except Exception:
            return

@receiver(post_save, sender=Tenant)
def create_evolution_instance_for_tenant(sender, instance, created, **kwargs):
    """
    Cria automaticamente uma instância Evolution API quando um tenant é criado
    """
    if created:
        try:
            if not bool(getattr(settings, 'EVOLUTION_AUTO_PROVISION', False)):
                return
            from .evolution_services import tenant_evolution_service
            
            logger.info(f"Criando instância Evolution API para novo tenant: {instance.nome_empresa}")
            
            # Provisionar instância Evolution API
            evolution_instance = tenant_evolution_service.provision_tenant_instance(instance)
            
            if evolution_instance:
                logger.info(f"Instância Evolution API criada com sucesso para {instance.nome_empresa}")
                
                # Atualizar configurações do tenant
                if not instance.configuracoes:
                    instance.configuracoes = {}
                
                instance.configuracoes.update({
                    'evolution_api': {
                        'instance_name': evolution_instance.instance_name,
                        'token': evolution_instance.token,
                        'provisioned_at': timezone.now().isoformat(),
                        'auto_provisioned': True
                    }
                })
                
                # Salvar sem triggerar o signal novamente
                Tenant.objects.filter(id=instance.id).update(configuracoes=instance.configuracoes)
                
            else:
                logger.error(f"Falha ao criar instância Evolution API para {instance.nome_empresa}")
                
        except Exception as e:
            logger.error(f"Erro ao criar instância Evolution API para {instance.nome_empresa}: {str(e)}")


@receiver(post_delete, sender=Tenant)
def cleanup_evolution_instance_for_tenant(sender, instance, **kwargs):
    """
    Remove a instância Evolution API quando um tenant é deletado
    """
    try:
        from .evolution_services import tenant_evolution_service
        
        logger.info(f"Removendo instância Evolution API para tenant deletado: {instance.nome_empresa}")
        
        # Remover instância Evolution API
        success = tenant_evolution_service.cleanup_tenant_instance(instance)
        
        if success:
            logger.info(f"Instância Evolution API removida com sucesso para {instance.nome_empresa}")
        else:
            logger.warning(f"Nenhuma instância Evolution API encontrada para {instance.nome_empresa}")
            
    except Exception as e:
        logger.error(f"Erro ao remover instância Evolution API para {instance.nome_empresa}: {str(e)}")
