"""
Modelos para gerenciar instâncias Evolution API por tenant
"""
from django.db import models
from django.utils import timezone
from .models import Tenant
import uuid
import secrets
import string

class EvolutionInstance(models.Model):
    """
    Modelo para gerenciar instâncias Evolution API por tenant
    """
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('conectado', 'Conectado'),
        ('desconectado', 'Desconectado'),
        ('erro', 'Erro'),
    ]
    
    tenant = models.OneToOneField(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='evolution_instance',
        verbose_name='Tenant'
    )
    
    # Configurações da instância
    instance_name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='Nome da Instância'
    )
    
    token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Token de Acesso'
    )
    
    api_key = models.CharField(
        max_length=255,
        verbose_name='API Key Global',
        help_text='Chave de API global para administração'
    )
    
    # Status e configurações
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inativo',
        verbose_name='Status'
    )
    
    qr_code = models.TextField(
        blank=True,
        null=True,
        verbose_name='QR Code'
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número do WhatsApp'
    )
    
    # Configurações do servidor
    server_url = models.URLField(
        default='http://localhost:8080',
        verbose_name='URL do Servidor'
    )
    
    webhook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL do Webhook'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_connection = models.DateTimeField(null=True, blank=True)
    
    # Configurações avançadas
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configurações Avançadas'
    )
    
    def save(self, *args, **kwargs):
        # Gerar nome da instância baseado no tenant
        if not self.instance_name:
            self.instance_name = f"{self.tenant.slug}_whatsapp"
        
        # Gerar token único se não existir
        if not self.token:
            self.token = self.generate_token()
            
        super().save(*args, **kwargs)
    
    def generate_token(self):
        """Gera um token único para a instância"""
        return f"{self.tenant.slug}_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))}"
    
    def get_manager_url(self):
        """Retorna a URL do gerenciador para esta instância"""
        return f"{self.server_url}/manager"
    
    def get_api_base_url(self):
        """Retorna a URL base da API para esta instância"""
        return f"{self.server_url}/instance/{self.instance_name}"
    
    def is_connected(self):
        """Verifica se a instância está conectada"""
        return self.status == 'conectado' and self.phone_number
    
    def __str__(self):
        return f"{self.tenant.nome_empresa} - {self.instance_name}"
    
    class Meta:
        verbose_name = 'Instância Evolution API'
        verbose_name_plural = 'Instâncias Evolution API'
        ordering = ['-created_at']


class EvolutionWebhook(models.Model):
    """
    Modelo para armazenar webhooks recebidos da Evolution API
    """
    EVENT_TYPES = [
        ('message', 'Mensagem'),
        ('status', 'Status'),
        ('connection', 'Conexão'),
        ('qrcode', 'QR Code'),
        ('other', 'Outro'),
    ]
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='evolution_webhooks',
        verbose_name='Tenant'
    )
    
    instance = models.ForeignKey(
        EvolutionInstance,
        on_delete=models.CASCADE,
        related_name='webhooks',
        verbose_name='Instância'
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        verbose_name='Tipo de Evento'
    )
    
    webhook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL do Webhook'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    data = models.JSONField(
        verbose_name='Dados do Webhook'
    )
    
    processed = models.BooleanField(
        default=False,
        verbose_name='Processado'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.tenant.nome_empresa} - {self.event_type}"
    
    class Meta:
        verbose_name = 'Webhook Evolution API'
        verbose_name_plural = 'Webhooks Evolution API'
        ordering = ['-created_at']


class EvolutionMessage(models.Model):
    """
    Modelo para armazenar mensagens da Evolution API
    """
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('document', 'Documento'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('location', 'Localização'),
        ('contact', 'Contato'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', 'Recebida'),
        ('outbound', 'Enviada'),
    ]
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='evolution_messages',
        verbose_name='Tenant'
    )
    
    instance = models.ForeignKey(
        EvolutionInstance,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Instância'
    )
    
    message_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='ID da Mensagem'
    )
    
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name='Direção'
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        verbose_name='Tipo de Mensagem'
    )
    
    from_number = models.CharField(
        max_length=20,
        verbose_name='Número Remetente'
    )
    
    to_number = models.CharField(
        max_length=20,
        verbose_name='Número Destinatário'
    )
    
    content = models.TextField(
        verbose_name='Conteúdo'
    )
    
    media_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL da Mídia'
    )
    
    timestamp = models.DateTimeField(
        verbose_name='Data/Hora'
    )
    
    raw_data = models.JSONField(
        verbose_name='Dados Brutos'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.tenant.nome_empresa} - {self.message_type} - {self.from_number}"
    
    class Meta:
        verbose_name = 'Mensagem Evolution API'
        verbose_name_plural = 'Mensagens Evolution API'
        ordering = ['-timestamp']