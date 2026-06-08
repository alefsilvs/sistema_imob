from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import os
import uuid


class CategoriaDocumento(models.Model):
    """Categorias para organizar documentos no repositório"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, default='fas fa-file')
    cor = models.CharField(max_length=7, default='#007bff')  # Cor em hexadecimal
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoria de Documento'
        verbose_name_plural = 'Categorias de Documentos'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


def upload_documento_path(instance, filename):
    """Gera caminho único para upload de documentos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('repositorio', str(instance.categoria.id), filename)


class Documento(models.Model):
    """Modelo principal para documentos do repositório"""
    
    TIPOS_ACESSO = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('restrito', 'Restrito'),
    ]
    
    TIPOS_DOCUMENTO = [
        ('contrato', 'Contrato'),
        ('comprovante', 'Comprovante'),
        ('certidao', 'Certidão'),
        ('rg', 'RG'),
        ('cpf', 'CPF'),
        ('comprovante_renda', 'Comprovante de Renda'),
        ('comprovante_residencia', 'Comprovante de Residência'),
        ('foto', 'Foto'),
        ('planta', 'Planta do Imóvel'),
        ('escritura', 'Escritura'),
        ('iptu', 'IPTU'),
        ('outros', 'Outros'),
    ]
    
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(CategoriaDocumento, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=25, choices=TIPOS_DOCUMENTO, default='outros')
    arquivo = models.FileField(
        upload_to=upload_documento_path,
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt'
        ])]
    )
    tamanho_arquivo = models.PositiveIntegerField(default=0)  # Em bytes
    tipo_acesso = models.CharField(max_length=10, choices=TIPOS_ACESSO, default='privado')
    
    # Relacionamentos
    proprietario = models.ForeignKey('Proprietario', on_delete=models.CASCADE, null=True, blank=True, related_name='repositorio_documentos')
    inquilino = models.ForeignKey('Inquilino', on_delete=models.CASCADE, null=True, blank=True, related_name='repositorio_documentos')
    
    # Metadados
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositorio_documentos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    # Controle de versão
    versao = models.PositiveIntegerField(default=1)
    documento_pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='versoes')
    
    # Controle de acesso
    usuarios_acesso = models.ManyToManyField(User, blank=True, related_name='repositorio_documentos_acesso')
    
    # Tags para busca
    tags = models.CharField(max_length=500, blank=True, help_text='Tags separadas por vírgula')
    
    # Status
    ativo = models.BooleanField(default=True)
    aprovado = models.BooleanField(default=False)
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='repositorio_documentos_aprovados')
    aprovado_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['categoria', 'tipo_documento']),
            models.Index(fields=['criado_em']),
            models.Index(fields=['tipo_acesso']),
        ]
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        if self.arquivo:
            self.tamanho_arquivo = self.arquivo.size
        super().save(*args, **kwargs)
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho do arquivo formatado"""
        if self.tamanho_arquivo < 1024:
            return f"{self.tamanho_arquivo} B"
        elif self.tamanho_arquivo < 1024 * 1024:
            return f"{self.tamanho_arquivo / 1024:.1f} KB"
        else:
            return f"{self.tamanho_arquivo / (1024 * 1024):.1f} MB"
    
    @property
    def extensao(self):
        """Retorna a extensão do arquivo"""
        if self.arquivo:
            return os.path.splitext(self.arquivo.name)[1].lower()
        return ''
    
    def pode_visualizar(self, usuario):
        """Verifica se o usuário pode visualizar o documento"""
        if self.tipo_acesso == 'publico':
            return True
        elif self.tipo_acesso == 'privado':
            return usuario == self.criado_por or usuario.is_superuser
        elif self.tipo_acesso == 'restrito':
            return (usuario == self.criado_por or 
                   usuario.is_superuser or 
                   usuario in self.usuarios_acesso.all())
        return False
    
    def criar_nova_versao(self, arquivo, usuario):
        """Cria uma nova versão do documento"""
        nova_versao = Documento.objects.create(
            titulo=self.titulo,
            descricao=self.descricao,
            categoria=self.categoria,
            tipo_documento=self.tipo_documento,
            arquivo=arquivo,
            tipo_acesso=self.tipo_acesso,
            proprietario=self.proprietario,
            inquilino=self.inquilino,
            criado_por=usuario,
            versao=self.versao + 1,
            documento_pai=self.documento_pai or self,
            tags=self.tags
        )
        return nova_versao


class LogAcessoDocumento(models.Model):
    """Log de acessos aos documentos"""
    
    TIPOS_ACAO = [
        ('visualizar', 'Visualizar'),
        ('download', 'Download'),
        ('compartilhar', 'Compartilhar'),
        ('editar', 'Editar'),
        ('excluir', 'Excluir'),
    ]
    
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='logs_acesso')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositorio_logs_acesso')
    acao = models.CharField(max_length=20, choices=TIPOS_ACAO)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    data_acesso = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log de Acesso'
        verbose_name_plural = 'Logs de Acesso'
        ordering = ['-data_acesso']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.acao} - {self.documento.titulo}"


class CompartilhamentoDocumento(models.Model):
    """Compartilhamento de documentos via link"""
    
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='compartilhamentos')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    ativo = models.BooleanField(default=True)
    senha = models.CharField(max_length=50, blank=True)
    limite_acessos = models.PositiveIntegerField(null=True, blank=True)
    acessos_realizados = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Compartilhamento'
        verbose_name_plural = 'Compartilhamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Compartilhamento: {self.documento.titulo}"
    
    @property
    def expirado(self):
        """Verifica se o compartilhamento expirou"""
        return timezone.now() > self.expira_em
    
    @property
    def limite_atingido(self):
        """Verifica se o limite de acessos foi atingido"""
        if self.limite_acessos:
            return self.acessos_realizados >= self.limite_acessos
        return False
    
    def pode_acessar(self, senha=None):
        """Verifica se o compartilhamento pode ser acessado"""
        if not self.ativo or self.expirado or self.limite_atingido:
            return False
        
        if self.senha and senha != self.senha:
            return False
        
        return True


class FavoritoDocumento(models.Model):
    """Documentos favoritos dos usuários"""
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = ['usuario', 'documento']
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.documento.titulo}"


class ConfiguracaoRepositorio(models.Model):
    """Configurações do repositório de documentos"""
    
    tamanho_maximo_arquivo = models.PositiveIntegerField(default=10485760)  # 10MB em bytes
    tipos_arquivo_permitidos = models.TextField(
        default='pdf,doc,docx,xls,xlsx,jpg,jpeg,png,gif,txt',
        help_text='Extensões permitidas separadas por vírgula'
    )
    backup_automatico = models.BooleanField(default=True)
    dias_retencao_logs = models.PositiveIntegerField(default=90)
    aprovacao_obrigatoria = models.BooleanField(default=False)
    notificar_novos_documentos = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Configuração do Repositório'
        verbose_name_plural = 'Configurações do Repositório'
    
    def __str__(self):
        return "Configurações do Repositório"
    
    @classmethod
    def get_configuracao(cls):
        """Retorna a configuração atual ou cria uma nova"""
        config, created = cls.objects.get_or_create(pk=1)
        return config