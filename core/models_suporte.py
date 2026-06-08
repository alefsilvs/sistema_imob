from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid
import os


class CategoriaTicket(models.Model):
    """Categorias para organizar tickets de suporte"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#007bff')  # Cor em hexadecimal
    icone = models.CharField(max_length=50, default='fas fa-question-circle')
    tempo_resposta_sla = models.PositiveIntegerField(default=24, help_text='Tempo em horas para primeira resposta')
    tempo_resolucao_sla = models.PositiveIntegerField(default=72, help_text='Tempo em horas para resolução')
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Categoria de Ticket'
        verbose_name_plural = 'Categorias de Tickets'
        ordering = ['ordem', 'nome']
    
    def __str__(self):
        return self.nome


class Ticket(models.Model):
    """Modelo principal para tickets de suporte"""
    
    PRIORIDADES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando_cliente', 'Aguardando Cliente'),
        ('aguardando_terceiro', 'Aguardando Terceiro'),
        ('resolvido', 'Resolvido'),
        ('fechado', 'Fechado'),
        ('cancelado', 'Cancelado'),
    ]
    
    CANAIS = [
        ('web', 'Portal Web'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('telefone', 'Telefone'),
        ('chat', 'Chat Online'),
        ('presencial', 'Presencial'),
    ]
    
    # Identificação
    numero = models.CharField(max_length=20, unique=True, editable=False)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    
    # Classificação
    categoria = models.ForeignKey(CategoriaTicket, on_delete=models.CASCADE, related_name='tickets')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    canal = models.CharField(max_length=15, choices=CANAIS, default='web')
    
    # Pessoas envolvidas
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_solicitados')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_responsaveis')
    observadores = models.ManyToManyField(User, blank=True, related_name='tickets_observados')
    
    # Relacionamentos com entidades do sistema
    proprietario = models.ForeignKey('Proprietario', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    inquilino = models.ForeignKey('Inquilino', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    
    # Controle de tempo
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    primeira_resposta_em = models.DateTimeField(null=True, blank=True)
    resolvido_em = models.DateTimeField(null=True, blank=True)
    fechado_em = models.DateTimeField(null=True, blank=True)
    
    # SLA
    prazo_primeira_resposta = models.DateTimeField(null=True, blank=True)
    prazo_resolucao = models.DateTimeField(null=True, blank=True)
    sla_primeira_resposta_cumprido = models.BooleanField(null=True, blank=True)
    sla_resolucao_cumprido = models.BooleanField(null=True, blank=True)
    
    # Avaliação
    avaliacao_atendimento = models.PositiveIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    comentario_avaliacao = models.TextField(blank=True)
    avaliado_em = models.DateTimeField(null=True, blank=True)
    
    # Metadados
    tags = models.CharField(max_length=500, blank=True, help_text='Tags separadas por vírgula')
    tempo_estimado_resolucao = models.PositiveIntegerField(null=True, blank=True, help_text='Tempo em horas')
    
    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['status', 'prioridade']),
            models.Index(fields=['categoria', 'status']),
            models.Index(fields=['solicitante', 'status']),
            models.Index(fields=['responsavel', 'status']),
            models.Index(fields=['criado_em']),
        ]
    
    def __str__(self):
        return f"#{self.numero} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self.gerar_numero()
        
        # Calcular prazos SLA
        if not self.prazo_primeira_resposta and self.categoria:
            self.prazo_primeira_resposta = self.criado_em + timezone.timedelta(hours=self.categoria.tempo_resposta_sla)
        
        if not self.prazo_resolucao and self.categoria:
            self.prazo_resolucao = self.criado_em + timezone.timedelta(hours=self.categoria.tempo_resolucao_sla)
        
        super().save(*args, **kwargs)
    
    def gerar_numero(self):
        """Gera número único para o ticket"""
        ano = timezone.now().year
        ultimo_ticket = Ticket.objects.filter(
            numero__startswith=f"{ano}"
        ).order_by('-numero').first()
        
        if ultimo_ticket:
            ultimo_numero = int(ultimo_ticket.numero.split('-')[1])
            novo_numero = ultimo_numero + 1
        else:
            novo_numero = 1
        
        return f"{ano}-{novo_numero:06d}"
    
    @property
    def tempo_aberto(self):
        """Retorna o tempo que o ticket está aberto"""
        if self.fechado_em:
            return self.fechado_em - self.criado_em
        return timezone.now() - self.criado_em
    
    @property
    def tempo_primeira_resposta(self):
        """Retorna o tempo até a primeira resposta"""
        if self.primeira_resposta_em:
            return self.primeira_resposta_em - self.criado_em
        return None
    
    @property
    def tempo_resolucao(self):
        """Retorna o tempo até a resolução"""
        if self.resolvido_em:
            return self.resolvido_em - self.criado_em
        return None
    
    @property
    def sla_primeira_resposta_status(self):
        """Status do SLA de primeira resposta"""
        if self.primeira_resposta_em:
            return 'cumprido' if self.primeira_resposta_em <= self.prazo_primeira_resposta else 'violado'
        elif timezone.now() > self.prazo_primeira_resposta:
            return 'violado'
        return 'pendente'
    
    @property
    def sla_resolucao_status(self):
        """Status do SLA de resolução"""
        if self.resolvido_em:
            return 'cumprido' if self.resolvido_em <= self.prazo_resolucao else 'violado'
        elif timezone.now() > self.prazo_resolucao:
            return 'violado'
        return 'pendente'
    
    def pode_visualizar(self, usuario):
        """Verifica se o usuário pode visualizar o ticket"""
        return (
            usuario == self.solicitante or
            usuario == self.responsavel or
            usuario in self.observadores.all() or
            usuario.is_superuser or
            usuario.groups.filter(name='Suporte').exists()
        )
    
    def pode_editar(self, usuario):
        """Verifica se o usuário pode editar o ticket"""
        return (
            usuario == self.responsavel or
            usuario.is_superuser or
            usuario.groups.filter(name='Suporte').exists()
        )


def upload_anexo_path(instance, filename):
    """Gera caminho para upload de anexos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('tickets', str(instance.ticket.numero), filename)


class InteracaoTicket(models.Model):
    """Interações/respostas em tickets"""
    
    TIPOS = [
        ('resposta', 'Resposta'),
        ('nota_interna', 'Nota Interna'),
        ('mudanca_status', 'Mudança de Status'),
        ('atribuicao', 'Atribuição'),
        ('escalacao', 'Escalação'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='interacoes')
    tipo = models.CharField(max_length=15, choices=TIPOS, default='resposta')
    conteudo = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # Mudanças de estado
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20, blank=True)
    responsavel_anterior = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interacoes_resp_anterior')
    responsavel_novo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interacoes_resp_novo')
    
    # Controle de visibilidade
    visivel_cliente = models.BooleanField(default=True)
    
    # Tempo gasto
    tempo_gasto = models.PositiveIntegerField(null=True, blank=True, help_text='Tempo em minutos')
    
    class Meta:
        verbose_name = 'Interação'
        verbose_name_plural = 'Interações'
        ordering = ['criado_em']
    
    def __str__(self):
        return f"{self.ticket.numero} - {self.get_tipo_display()} - {self.usuario.username}"
    
    def save(self, *args, **kwargs):
        # Marcar primeira resposta no ticket
        if (self.tipo == 'resposta' and 
            not self.ticket.primeira_resposta_em and 
            self.usuario != self.ticket.solicitante):
            self.ticket.primeira_resposta_em = timezone.now()
            self.ticket.sla_primeira_resposta_cumprido = self.ticket.primeira_resposta_em <= self.ticket.prazo_primeira_resposta
            self.ticket.save()
        
        super().save(*args, **kwargs)


class AnexoTicket(models.Model):
    """Anexos de tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='anexos')
    interacao = models.ForeignKey(InteracaoTicket, on_delete=models.CASCADE, null=True, blank=True, related_name='anexos')
    arquivo = models.FileField(
        upload_to=upload_anexo_path,
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'zip'
        ])]
    )
    nome_original = models.CharField(max_length=255)
    tamanho = models.PositiveIntegerField(default=0)
    tipo_mime = models.CharField(max_length=100, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['criado_em']
    
    def __str__(self):
        return f"{self.ticket.numero} - {self.nome_original}"
    
    def save(self, *args, **kwargs):
        if self.arquivo:
            self.tamanho = self.arquivo.size
            self.nome_original = self.arquivo.name
        super().save(*args, **kwargs)
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho formatado"""
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"


class BaseConhecimento(models.Model):
    """Base de conhecimento para autoatendimento"""
    
    TIPOS = [
        ('artigo', 'Artigo'),
        ('faq', 'FAQ'),
        ('tutorial', 'Tutorial'),
        ('video', 'Vídeo'),
    ]
    
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    tipo = models.CharField(max_length=10, choices=TIPOS, default='artigo')
    categoria = models.ForeignKey(CategoriaTicket, on_delete=models.CASCADE, related_name='artigos_base')
    tags = models.CharField(max_length=500, blank=True)
    
    # Controle de acesso
    publico = models.BooleanField(default=True)
    usuarios_acesso = models.ManyToManyField(User, blank=True, related_name='artigos_acesso')
    
    # Metadados
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artigos_criados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    visualizacoes = models.PositiveIntegerField(default=0)
    util_sim = models.PositiveIntegerField(default=0)
    util_nao = models.PositiveIntegerField(default=0)
    
    # Status
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Artigo da Base de Conhecimento'
        verbose_name_plural = 'Base de Conhecimento'
        ordering = ['-destaque', '-criado_em']
    
    def __str__(self):
        return self.titulo
    
    @property
    def percentual_util(self):
        """Percentual de avaliações positivas"""
        total = self.util_sim + self.util_nao
        if total == 0:
            return 0
        return (self.util_sim / total) * 100


class ConfiguracaoSuporte(models.Model):
    """Configurações do sistema de suporte"""
    
    # Horário de funcionamento
    horario_inicio = models.TimeField(default='08:00')
    horario_fim = models.TimeField(default='18:00')
    dias_funcionamento = models.CharField(max_length=20, default='1,2,3,4,5')  # 1=segunda, 7=domingo
    
    # Notificações
    notificar_novo_ticket = models.BooleanField(default=True)
    notificar_resposta_cliente = models.BooleanField(default=True)
    notificar_sla_violado = models.BooleanField(default=True)
    
    # E-mail
    email_suporte = models.EmailField(default='suporte@empresa.com')
    template_email_novo_ticket = models.TextField(blank=True)
    template_email_resposta = models.TextField(blank=True)
    
    # WhatsApp
    whatsapp_ativo = models.BooleanField(default=False)
    whatsapp_numero = models.CharField(max_length=20, blank=True)
    whatsapp_mensagem_boas_vindas = models.TextField(blank=True)
    
    # Chat
    chat_ativo = models.BooleanField(default=False)
    chat_horario_funcionamento = models.BooleanField(default=True)
    
    # Autoatendimento
    base_conhecimento_ativa = models.BooleanField(default=True)
    sugerir_artigos = models.BooleanField(default=True)
    
    # SLA padrão
    sla_resposta_padrao = models.PositiveIntegerField(default=24)
    sla_resolucao_padrao = models.PositiveIntegerField(default=72)
    
    class Meta:
        verbose_name = 'Configuração do Suporte'
        verbose_name_plural = 'Configurações do Suporte'
    
    def __str__(self):
        return "Configurações do Suporte"
    
    @classmethod
    def get_configuracao(cls):
        """Retorna a configuração atual ou cria uma nova"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def esta_em_funcionamento(self):
        """Verifica se o suporte está em funcionamento"""
        agora = timezone.now()
        dia_semana = str(agora.weekday() + 1)  # 1=segunda, 7=domingo
        
        if dia_semana not in self.dias_funcionamento.split(','):
            return False
        
        hora_atual = agora.time()
        return self.horario_inicio <= hora_atual <= self.horario_fim


class EscalacaoTicket(models.Model):
    """Escalações de tickets"""
    
    MOTIVOS = [
        ('sla_violado', 'SLA Violado'),
        ('complexidade', 'Alta Complexidade'),
        ('cliente_vip', 'Cliente VIP'),
        ('manual', 'Escalação Manual'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='escalacoes')
    motivo = models.CharField(max_length=20, choices=MOTIVOS)
    responsavel_origem = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalacoes_origem')
    responsavel_destino = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalacoes_destino')
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Escalação'
        verbose_name_plural = 'Escalações'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Escalação {self.ticket.numero} - {self.get_motivo_display()}"