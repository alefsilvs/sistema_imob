from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
import hashlib
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

class PlanoComercial(models.Model):
    TIPOS_PLANO = [
        ('trial', 'Trial Gratuito'),
        ('basico', 'Básico'),
        ('profissional', 'Profissional'),
        ('empresarial', 'Empresarial'),
        ('personalizado', 'Personalizado')
    ]
    
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_PLANO)
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_anual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_usuarios = models.IntegerField(default=1)
    max_imoveis = models.IntegerField(default=100)
    max_contratos = models.IntegerField(default=50)
    storage_gb = models.IntegerField(default=5)
    api_calls_mes = models.IntegerField(default=1000)
    suporte_prioritario = models.BooleanField(default=False)
    backup_automatico = models.BooleanField(default=False)
    subdominio_personalizado = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False, help_text='Plano de trial gratuito')
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}/mês"
    
    class Meta:
        verbose_name = "Plano Comercial"
        verbose_name_plural = "Planos Comerciais"

class Tenant(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('suspenso', 'Suspenso'),
        ('cancelado', 'Cancelado'),
        ('trial', 'Trial'),
        ('pendente_pagamento', 'Pendente Pagamento')
    ]
    
    nome_empresa = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    subdominio = models.CharField(max_length=100, unique=True)
    usuario_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_admin')
    plano = models.ForeignKey(PlanoComercial, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    trial_ate = models.DateTimeField(null=True, blank=True)
    configuracoes = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.trial_ate:
            is_trial_plan = False
            try:
                if self.plano:
                    is_trial_plan = bool(getattr(self.plano, "is_trial", False) or getattr(self.plano, "tipo", "") == "trial")
            except Exception:
                is_trial_plan = False
            if is_trial_plan:
                self.trial_ate = timezone.now() + timedelta(days=30)
                self.status = 'trial'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome_empresa} ({self.subdominio})"
    
    @property
    def is_trial_ativo(self):
        if self.trial_ate and timezone.now() < self.trial_ate:
            return True
        return False
    
    @property
    def dias_restantes_trial(self):
        if self.trial_ate:
            delta = self.trial_ate - timezone.now()
            return max(0, delta.days)
        return 0
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

class ConfiguracaoTenant(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='config')
    logo_url = models.URLField(blank=True, null=True)
    cor_primaria = models.CharField(max_length=7, default='#007bff')
    cor_secundaria = models.CharField(max_length=7, default='#6c757d')
    email_contato = models.EmailField()
    telefone_contato = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True)
    configuracoes_email = models.JSONField(default=dict, blank=True)
    configuracoes_api = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"Configurações - {self.tenant.nome_empresa}"
    
    class Meta:
        verbose_name = "Configuração do Tenant"
        verbose_name_plural = "Configurações dos Tenants"

class RegistroUso(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='registros_uso')
    data = models.DateField()
    usuarios_ativos = models.IntegerField(default=0)
    imoveis_cadastrados = models.IntegerField(default=0)
    contratos_ativos = models.IntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    storage_usado_mb = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.tenant.nome_empresa} - {self.data}"
    
    class Meta:
        verbose_name = "Registro de Uso"
        verbose_name_plural = "Registros de Uso"
        unique_together = ['tenant', 'data']

class Faturamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado')
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='faturas')
    numero_fatura = models.CharField(max_length=50, unique=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    detalhes = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Fatura {self.numero_fatura} - {self.tenant.nome_empresa}"
    
    @property
    def esta_vencida(self):
        return timezone.now().date() > self.data_vencimento and self.status == 'pendente'
    
    class Meta:
        verbose_name = "Faturamento"
        verbose_name_plural = "Faturamentos"
        ordering = ['-criado_em']

class PagamentoPlano(models.Model):
    """Modelo específico para pagamentos de assinatura de planos"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
        ('expirado', 'Expirado'),
    ]
    
    METODO_CHOICES = [
        ('pix', 'PIX'),
        ('cartao', 'Cartão de Crédito'),
        ('boleto', 'Boleto Bancário'),
    ]
    
    # Identificação única
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_pagamento = models.CharField(max_length=64, unique=True, editable=False)
    
    # Relacionamentos
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoComercial, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    
    # Dados do pagamento
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pagamento = models.CharField(max_length=20, choices=METODO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    # Dados da transação
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Controle de tempo
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField()
    data_pagamento = models.DateTimeField(null=True, blank=True)
    
    # Dados do pagador
    nome_pagador = models.CharField(max_length=200)
    email_pagador = models.EmailField()
    telefone_pagador = models.CharField(max_length=20, blank=True)
    documento_pagador = models.CharField(max_length=20, blank=True)
    
    # Metadados
    descricao = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.token_pagamento:
            self.token_pagamento = self.gerar_token_pagamento()
        
        if not self.data_expiracao:
            self.data_expiracao = timezone.now() + timezone.timedelta(hours=24)
        
        super().save(*args, **kwargs)
    
    def gerar_token_pagamento(self):
        """Gera um token único para o pagamento"""
        base_string = f"{self.usuario.id}-{self.plano.id}-{timezone.now().isoformat()}-{uuid.uuid4()}"
        return hashlib.sha256(base_string.encode()).hexdigest()
    
    @property
    def esta_expirado(self):
        return timezone.now() > self.data_expiracao
    
    @property
    def pode_processar(self):
        return self.status == 'pendente' and not self.esta_expirado
    
    def marcar_como_pago(self, transaction_id=None, gateway_response=None):
        """Marca o pagamento como aprovado e cria/ativa o tenant"""
        self.status = 'aprovado'
        self.data_pagamento = timezone.now()
        
        if transaction_id:
            self.transaction_id = transaction_id
        
        if gateway_response:
            self.gateway_response = gateway_response
        
        self.save()
        
        # Criar ou ativar tenant
        try:
            tenant = Tenant.objects.get(usuario_admin=self.usuario)
            # Atualizar plano e status
            tenant.plano = self.plano
            tenant.status = 'ativo'
            tenant.data_expiracao = timezone.now() + timezone.timedelta(days=30)
            tenant.save()
        except Tenant.DoesNotExist:
            # Criar novo tenant
            from django.utils.text import slugify
            import random
            import string
            
            # Gerar slug único
            base_slug = slugify(self.nome_pagador or self.usuario.username)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Gerar subdomínio único
            subdominio = slug
            while Tenant.objects.filter(subdominio=subdominio).exists():
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                subdominio = f"{base_slug}-{random_suffix}"
            
            tenant = Tenant.objects.create(
                nome_empresa=self.nome_pagador or f"Empresa {self.usuario.username}",
                slug=slug,
                subdominio=subdominio,
                usuario_admin=self.usuario,
                plano=self.plano,
                status='ativo',
                data_expiracao=timezone.now() + timezone.timedelta(days=30)
            )
        
        return tenant
    
    def __str__(self):
        return f"Pagamento {self.token_pagamento[:8]} - {self.plano.nome}"
    
    class Meta:
        verbose_name = "Pagamento de Plano"
        verbose_name_plural = "Pagamentos de Planos"
        ordering = ['-data_criacao']

class VerificacaoEmail(models.Model):
    """Modelo para gerenciar verificação de email dos usuários"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verificacao_email')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    email_verificado = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_verificacao = models.DateTimeField(null=True, blank=True)
    tentativas_envio = models.IntegerField(default=0)
    ultimo_envio = models.DateTimeField(null=True, blank=True)
    
    def gerar_novo_token(self):
        """Gera um novo token de verificação"""
        self.token = uuid.uuid4()
        self.save()
        return self.token
    
    def verificar_email(self):
        """Marca o email como verificado"""
        self.email_verificado = True
        self.data_verificacao = timezone.now()
        self.save()
    
    def enviar_email_verificacao(self, request=None):
        """Envia email de verificação"""
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        # Gerar URL de verificação
        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = settings.SITE_URL
        
        url_verificacao = f"{base_url}saas/verificar-email/{self.token}/"
        
        # Renderizar template do email
        contexto = {
            'usuario': self.usuario,
            'url_verificacao': url_verificacao,
            'site_name': 'ImobiPro'
        }
        
        html_message = render_to_string('saas/emails/verificacao_email.html', contexto)
        plain_message = strip_tags(html_message)
        
        # Enviar email
        try:
            send_mail(
                subject='Verificação de Email - ImobiPro',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.usuario.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Atualizar estatísticas
            self.tentativas_envio += 1
            self.ultimo_envio = timezone.now()
            self.save()
            
            return True
        except Exception as e:
            print(f"Erro ao enviar email de verificação: {e}")
            return False
    
    @property
    def pode_reenviar(self):
        """Verifica se pode reenviar email (limite de 1 por hora)"""
        if not self.ultimo_envio:
            return True
        
        tempo_limite = timezone.now() - timedelta(hours=1)
        return self.ultimo_envio < tempo_limite
    
    def __str__(self):
        status = "Verificado" if self.email_verificado else "Pendente"
        return f"{self.usuario.email} - {status}"
    
    class Meta:
        verbose_name = "Verificação de Email"
        verbose_name_plural = "Verificações de Email"
        ordering = ['-data_criacao']
