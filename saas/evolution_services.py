"""
Serviços para gerenciar Evolution API automaticamente por tenant
"""
import requests
import json
import logging
from django.conf import settings
from django.utils import timezone
from .evolution_models import EvolutionInstance
from .models import Tenant

logger = logging.getLogger(__name__)

class EvolutionAPIService:
    """
    Serviço para interagir com a Evolution API
    """
    
    def __init__(self, base_url='http://localhost:8080', global_api_key=None):
        self.base_url = base_url.rstrip('/')
        self.global_api_key = global_api_key or getattr(settings, 'EVOLUTION_GLOBAL_API_KEY', 'sistema_imo_2024_secure_key_789')
        self.timeout_seconds = int(getattr(settings, 'EVOLUTION_HTTP_TIMEOUT', 5) or 5)
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'apikey': self.global_api_key
        })
    
    def create_instance(self, instance_name, token=None):
        """
        Cria uma nova instância na Evolution API
        """
        try:
            data = {
                'instanceName': instance_name,
                'token': token or f"{instance_name}_token_{timezone.now().strftime('%Y%m%d%H%M%S')}",
                'qrcode': True,
                'integration': 'WHATSAPP-BAILEYS'
            }
            
            response = self.session.post(
                f"{self.base_url}/instance/create",
                json=data,
                timeout=self.timeout_seconds,
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Erro ao criar instância {instance_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar instância {instance_name}: {str(e)}")
            return None
    
    def get_instance_info(self, instance_name):
        """
        Obtém informações de uma instância
        """
        try:
            response = self.session.get(
                f"{self.base_url}/instance/fetchInstances",
                timeout=self.timeout_seconds,
            )
            
            if response.status_code == 200:
                instances = response.json()
                for instance in instances:
                    if instance.get('instance', {}).get('instanceName') == instance_name:
                        return instance
                return None
            else:
                logger.error(f"Erro ao buscar instância {instance_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar instância {instance_name}: {str(e)}")
            return None
    
    def get_qr_code(self, instance_name):
        """
        Obtém o QR Code de uma instância
        """
        try:
            response = self.session.get(
                f"{self.base_url}/instance/connect/{instance_name}",
                timeout=self.timeout_seconds,
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('base64')
            else:
                logger.error(f"Erro ao obter QR Code {instance_name}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter QR Code {instance_name}: {str(e)}")
            return None
    
    def delete_instance(self, instance_name):
        """
        Deleta uma instância
        """
        try:
            response = self.session.delete(f"{self.base_url}/instance/delete/{instance_name}", timeout=self.timeout_seconds)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Erro ao deletar instância {instance_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao deletar instância {instance_name}: {str(e)}")
            return False
    
    def send_message(self, instance_name, number, message, message_type='text'):
        """
        Envia uma mensagem via instância
        """
        try:
            data = {
                'number': number,
                'textMessage': {
                    'text': message
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.global_api_key
            }
            
            response = requests.post(
                f"{self.base_url}/message/sendText/{instance_name}",
                json=data,
                headers=headers,
                timeout=self.timeout_seconds
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return None


class TenantEvolutionService:
    """
    Serviço para gerenciar Evolution API por tenant
    """
    
    def __init__(self):
        self.api_service = EvolutionAPIService()
    
    def provision_tenant_instance(self, tenant):
        """
        Provisiona uma instância Evolution API para um tenant
        """
        try:
            # Verificar se já existe uma instância para este tenant
            existing_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
            if existing_instance:
                logger.info(f"Instância já existe para tenant {tenant.nome_empresa}")
                return existing_instance
            
            # Gerar nome único para a instância
            instance_name = f"{tenant.slug}_whatsapp"
            token = f"{tenant.slug}_token_{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Criar instância na Evolution API
            api_response = self.api_service.create_instance(instance_name, token)
            
            if api_response:
                # Criar registro no banco de dados
                evolution_instance = EvolutionInstance.objects.create(
                    tenant=tenant,
                    instance_name=instance_name,
                    token=token,
                    api_key=self.api_service.global_api_key,
                    status='ativo',
                    server_url=self.api_service.base_url,
                    settings={
                        'auto_created': True,
                        'creation_response': api_response
                    }
                )
                
                logger.info(f"Instância criada com sucesso para tenant {tenant.nome_empresa}")
                return evolution_instance
            else:
                logger.error(f"Falha ao criar instância na API para tenant {tenant.nome_empresa}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao provisionar instância para tenant {tenant.nome_empresa}: {str(e)}")
            return None
    
    def update_instance_status(self, evolution_instance):
        """
        Atualiza o status de uma instância
        """
        try:
            instance_info = self.api_service.get_instance_info(evolution_instance.instance_name)
            
            if instance_info:
                # Atualizar status baseado na resposta da API
                connection_status = instance_info.get('instance', {}).get('state')
                
                if connection_status == 'open':
                    evolution_instance.status = 'conectado'
                    evolution_instance.last_connection = timezone.now()
                elif connection_status == 'close':
                    evolution_instance.status = 'desconectado'
                else:
                    evolution_instance.status = 'inativo'
                
                # Atualizar número do telefone se disponível
                phone_number = instance_info.get('instance', {}).get('owner')
                if phone_number:
                    evolution_instance.phone_number = phone_number
                
                evolution_instance.save()
                return True
            else:
                evolution_instance.status = 'erro'
                evolution_instance.save()
                return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status da instância {evolution_instance.instance_name}: {str(e)}")
            evolution_instance.status = 'erro'
            evolution_instance.save()
            return False
    
    def get_qr_code_for_tenant(self, tenant):
        """
        Obtém o QR Code para um tenant
        """
        try:
            evolution_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
            
            if not evolution_instance:
                # Provisionar instância se não existir
                evolution_instance = self.provision_tenant_instance(tenant)
            
            if evolution_instance:
                qr_code = self.api_service.get_qr_code(evolution_instance.instance_name)
                
                if qr_code:
                    evolution_instance.qr_code = qr_code
                    evolution_instance.save()
                    return qr_code
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter QR Code para tenant {tenant.nome_empresa}: {str(e)}")
            return None
    
    def send_message_for_tenant(self, tenant, number, message):
        """
        Envia mensagem via instância do tenant
        """
        try:
            evolution_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
            
            if not evolution_instance:
                logger.error(f"Nenhuma instância encontrada para tenant {tenant.nome_empresa}")
                return None
            
            if evolution_instance.status != 'conectado':
                logger.error(f"Instância não está conectada para tenant {tenant.nome_empresa}")
                return None
            
            return self.api_service.send_message(
                evolution_instance.instance_name,
                number,
                message
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para tenant {tenant.nome_empresa}: {str(e)}")
            return None
    
    def cleanup_tenant_instance(self, tenant):
        """
        Remove instância de um tenant
        """
        try:
            evolution_instance = EvolutionInstance.objects.filter(tenant=tenant).first()
            
            if evolution_instance:
                # Deletar da Evolution API
                self.api_service.delete_instance(evolution_instance.instance_name)
                
                # Deletar do banco de dados
                evolution_instance.delete()
                
                logger.info(f"Instância removida para tenant {tenant.nome_empresa}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover instância para tenant {tenant.nome_empresa}: {str(e)}")
            return False


# Instância global do serviço
tenant_evolution_service = TenantEvolutionService()
