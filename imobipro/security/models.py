import hashlib
import platform
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import json
from .fields import EncryptedCharField, EncryptedJSONField

class MasterUser(models.Model):
    """
    Modelo para o usuário master único do sistema.
    Apenas um usuário master pode existir por vez.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='master_profile')
    hardware_fingerprint = models.CharField(max_length=255, unique=True)
    authorized_ips = models.JSONField(default=list, help_text="Lista de IPs autorizados")
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = EncryptedCharField(max_length=32, blank=True)
    backup_codes = EncryptedJSONField(default=list, blank=True, help_text="Códigos de backup para 2FA")
    last_security_check = models.DateTimeField(auto_now=True)
    security_level = models.CharField(
        max_length=20,
        choices=[
            ('BASIC', 'Básico'),
            ('ENHANCED', 'Aprimorado'),
            ('MAXIMUM', 'Máximo')
        ],
        default='ENHANCED'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuário Master'
        verbose_name_plural = 'Usuários Master'
    
    def save(self, *args, **kwargs):
        # Garantir que apenas um usuário master existe
        if not self.pk and MasterUser.objects.exists():
            raise ValidationError("Apenas um usuário master pode existir no sistema.")
        
        # Gerar fingerprint do hardware se não existir
        if not self.hardware_fingerprint:
            self.hardware_fingerprint = self.generate_hardware_fingerprint()
        
        super().save(*args, **kwargs)
    
    def generate_hardware_fingerprint(self):
        """
        Gera uma impressão digital única do hardware
        """
        machine_info = {
            'machine': platform.machine(),
            'processor': platform.processor(),
            'system': platform.system(),
            'node': platform.node(),
            'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                   for elements in range(0,2*6,2)][::-1])
        }
        
        fingerprint_string = json.dumps(machine_info, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def is_ip_authorized(self, ip_address):
        """
        Verifica se o IP está autorizado
        """
        if not self.authorized_ips:
            return False
        return ip_address in self.authorized_ips
    
    def add_authorized_ip(self, ip_address):
        """
        Adiciona um IP à lista de autorizados
        """
        if ip_address not in self.authorized_ips:
            self.authorized_ips.append(ip_address)
            self.save()
    
    def remove_authorized_ip(self, ip_address):
        """
        Remove um IP da lista de autorizados
        """
        if ip_address in self.authorized_ips:
            self.authorized_ips.remove(ip_address)
            self.save()
    
    def __str__(self):
        return f"Master User: {self.user.username}"

class SecurityLog(models.Model):
    """
    Log de eventos de segurança
    """
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Login Bem-sucedido'),
        ('LOGIN_FAILED', 'Tentativa de Login Falhada'),
        ('UNAUTHORIZED_ACCESS', 'Acesso Não Autorizado'),
        ('IP_BLOCKED', 'IP Bloqueado'),
        ('HARDWARE_MISMATCH', 'Hardware Não Reconhecido'),
        ('ADMIN_ACTION', 'Ação Administrativa'),
        ('DATA_EXPORT', 'Exportação de Dados'),
        ('SYSTEM_CHANGE', 'Alteração no Sistema'),
        ('SECURITY_BREACH', 'Violação de Segurança'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField()
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    severity = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Baixa'),
            ('MEDIUM', 'Média'),
            ('HIGH', 'Alta'),
            ('CRITICAL', 'Crítica')
        ],
        default='MEDIUM'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Segurança'
        verbose_name_plural = 'Logs de Segurança'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.ip_address} - {self.timestamp}"

class LoginAttempt(models.Model):
    """
    Rastreamento de tentativas de login
    """
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=150)
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField()
    
    class Meta:
        verbose_name = 'Tentativa de Login'
        verbose_name_plural = 'Tentativas de Login'
        ordering = ['-timestamp']
    
    @classmethod
    def get_failed_attempts(cls, ip_address, minutes=15):
        """
        Retorna o número de tentativas falhadas nos últimos X minutos
        """
        since = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            ip_address=ip_address,
            success=False,
            timestamp__gte=since
        ).count()
    
    def __str__(self):
        status = "Sucesso" if self.success else "Falha"
        return f"{self.username} - {self.ip_address} - {status}"

class BlockedIP(models.Model):
    """
    IPs bloqueados por tentativas suspeitas
    """
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    permanent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'IP Bloqueado'
        verbose_name_plural = 'IPs Bloqueados'
        ordering = ['-blocked_at']
    
    def is_blocked(self):
        """
        Verifica se o IP ainda está bloqueado
        """
        if self.permanent:
            return True
        if self.blocked_until and timezone.now() > self.blocked_until:
            return False
        return True
    
    def __str__(self):
        return f"IP Bloqueado: {self.ip_address}"

class SystemSetting(models.Model):
    """
    Configurações de segurança do sistema
    """
    key = models.CharField(max_length=100, unique=True)
    value = EncryptedCharField(max_length=1000)
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=True)  # Sempre criptografado agora
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."