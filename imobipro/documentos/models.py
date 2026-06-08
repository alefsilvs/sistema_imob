from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Pessoa
from imoveis.models import Imovel
from contratos.models import Contrato
from saas.models import Tenant
import hashlib
import os

class TipoDocumento(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    obrigatorio = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    categoria = models.CharField(max_length=50, choices=[
        ('CONTRATO', 'Contrato'),
        ('PESSOA', 'Pessoa'),
        ('IMOVEL', 'Imóvel'),
        ('FINANCEIRO', 'Financeiro'),
        ('JURIDICO', 'Jurídico'),
        ('OUTROS', 'Outros'),
    ], default='OUTROS')
    
    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documentos'
    
    def __str__(self):
        return self.nome

def upload_documento_path(instance, filename):
    """Função para definir o caminho de upload dos documentos"""
    tenant_id = instance.tenant.id if instance.tenant else 'default'
    return f'documentos/{tenant_id}/{instance.tipo.categoria.lower()}/{filename}'

class Documento(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('ARQUIVADO', 'Arquivado'),
        ('VENCIDO', 'Vencido'),
        ('PENDENTE', 'Pendente Aprovação'),
    ]
    
    CONFIDENCIALIDADE_CHOICES = [
        ('PUBLICO', 'Público'),
        ('INTERNO', 'Interno'),
        ('CONFIDENCIAL', 'Confidencial'),
        ('RESTRITO', 'Restrito'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, null=True, blank=True)
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, null=True, blank=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True)
    
    # Informações do arquivo
    arquivo = models.FileField(upload_to=upload_documento_path)
    nome_arquivo = models.CharField(max_length=200)
    nome_original = models.CharField(max_length=200, null=True, blank=True)
    tamanho_arquivo = models.BigIntegerField(default=0)
    tipo_mime = models.CharField(max_length=100, blank=True)
    hash_arquivo = models.CharField(max_length=64, blank=True)  # SHA-256
    
    # Metadados
    descricao = models.TextField(blank=True)
    palavras_chave = models.CharField(max_length=500, blank=True, help_text="Palavras-chave separadas por vírgula")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    confidencialidade = models.CharField(max_length=20, choices=CONFIDENCIALIDADE_CHOICES, default='INTERNO')
    
    # Datas
    data_upload = models.DateTimeField(auto_now_add=True)
    data_documento = models.DateField(null=True, blank=True, help_text="Data do documento original")
    data_validade = models.DateField(null=True, blank=True)
    data_arquivamento = models.DateTimeField(null=True, blank=True)
    
    # Controle de acesso
    usuario_upload = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos_enviados')
    usuario_aprovacao = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos_aprovados')
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    
    # Versionamento
    versao = models.PositiveIntegerField(default=1)
    documento_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versoes')
    
    # Controle
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-data_upload']
        indexes = [
            models.Index(fields=['tenant', 'tipo']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['hash_arquivo']),
        ]
    
    def __str__(self):
        return f"{self.tipo.nome} - {self.nome_arquivo}"
    
    def save(self, *args, **kwargs):
        if self.arquivo:
            # Calcular hash do arquivo
            if not self.hash_arquivo:
                self.hash_arquivo = self.calcular_hash()
            
            # Definir tamanho do arquivo
            if not self.tamanho_arquivo:
                self.tamanho_arquivo = self.arquivo.size
            
            # Definir nome original se não definido
            if not self.nome_original:
                self.nome_original = self.arquivo.name
        
        super().save(*args, **kwargs)
    
    def calcular_hash(self):
        """Calcula o hash SHA-256 do arquivo"""
        if self.arquivo:
            hash_sha256 = hashlib.sha256()
            for chunk in self.arquivo.chunks():
                hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        return ''
    
    def is_vencido(self):
        """Verifica se o documento está vencido"""
        if self.data_validade:
            return self.data_validade < timezone.now().date()
        return False
    
    def get_extensao(self):
        """Retorna a extensão do arquivo"""
        if self.nome_arquivo:
            return os.path.splitext(self.nome_arquivo)[1].lower()
        return ''
    
    def get_tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if self.tamanho_arquivo:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if self.tamanho_arquivo < 1024.0:
                    return f"{self.tamanho_arquivo:.1f} {unit}"
                self.tamanho_arquivo /= 1024.0
        return "0 B"

class CategoriaDocumento(models.Model):
    """Categorias para organização hierárquica de documentos"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    categoria_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategorias')
    cor = models.CharField(max_length=7, default='#007bff', help_text="Cor em hexadecimal")
    icone = models.CharField(max_length=50, default='bi-folder', help_text="Classe do ícone Bootstrap")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        ordering = ['nome']
    
    def __str__(self):
        if self.categoria_pai:
            return f"{self.categoria_pai.nome} > {self.nome}"
        return self.nome

class LogAcessoDocumento(models.Model):
    """Log de acessos aos documentos para auditoria"""
    ACAO_CHOICES = [
        ('VISUALIZAR', 'Visualizar'),
        ('DOWNLOAD', 'Download'),
        ('EDITAR', 'Editar'),
        ('EXCLUIR', 'Excluir'),
        ('COMPARTILHAR', 'Compartilhar'),
    ]
    
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='logs_acesso')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    data_acesso = models.DateTimeField(auto_now_add=True)
    detalhes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Log de Acesso'
        verbose_name_plural = 'Logs de Acesso'
        ordering = ['-data_acesso']
    
    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.documento.nome_arquivo}"

class CompartilhamentoDocumento(models.Model):
    """Compartilhamento de documentos com controle de acesso"""
    TIPO_ACESSO_CHOICES = [
        ('LEITURA', 'Somente Leitura'),
        ('DOWNLOAD', 'Leitura e Download'),
        ('EDICAO', 'Edição'),
    ]
    
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='compartilhamentos')
    usuario_origem = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compartilhamentos_enviados')
    usuario_destino = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compartilhamentos_recebidos', null=True, blank=True)
    email_externo = models.EmailField(blank=True, help_text="Para compartilhamento com usuários externos")
    tipo_acesso = models.CharField(max_length=20, choices=TIPO_ACESSO_CHOICES, default='LEITURA')
    token_acesso = models.CharField(max_length=64, unique=True, blank=True)
    data_compartilhamento = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    acessos = models.PositiveIntegerField(default=0)
    limite_acessos = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Compartilhamento'
        verbose_name_plural = 'Compartilhamentos'
        ordering = ['-data_compartilhamento']
    
    def __str__(self):
        destino = self.usuario_destino.username if self.usuario_destino else self.email_externo
        return f"{self.documento.nome_arquivo} -> {destino}"
    
    def save(self, *args, **kwargs):
        if not self.token_acesso:
            self.token_acesso = hashlib.sha256(
                f"{self.documento.id}{self.usuario_origem.id}{timezone.now()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)
    
    def is_expirado(self):
        if self.data_expiracao:
            return timezone.now() > self.data_expiracao
        return False
    
    def pode_acessar(self):
        if not self.ativo or self.is_expirado():
            return False
        if self.limite_acessos and self.acessos >= self.limite_acessos:
            return False
        return True

class Vistoria(models.Model):
    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('PERIODICA', 'Periódica'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data_agendamento = models.DateTimeField()
    data_realizacao = models.DateTimeField(null=True, blank=True)
    responsavel = models.CharField(max_length=200)
    observacoes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGENDADA')
    assinatura_digital = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Vistoria'
        verbose_name_plural = 'Vistorias'
        ordering = ['-data_agendamento']
    
    def __str__(self):
        return f"Vistoria {self.tipo} - {self.imovel.codigo}"

class ItemVistoria(models.Model):
    ESTADO_CHOICES = [
        ('OTIMO', 'Ótimo'),
        ('BOM', 'Bom'),
        ('REGULAR', 'Regular'),
        ('RUIM', 'Ruim'),
        ('PESSIMO', 'Péssimo'),
    ]
    
    vistoria = models.ForeignKey(Vistoria, on_delete=models.CASCADE, related_name='itens')
    item = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    observacoes = models.TextField(blank=True)
    foto = models.ImageField(upload_to='vistorias/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Item de Vistoria'
        verbose_name_plural = 'Itens de Vistoria'
    
    def __str__(self):
        return f"{self.item} - {self.estado}"
