from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from core.models import Inquilino
from contratos.models import Contrato
import json

class CategoriaTemplate(models.Model):
    """Categorias para organizar templates de notificação"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#007bff', help_text='Cor em hexadecimal')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoria de Template'
        verbose_name_plural = 'Categorias de Templates'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class TemplateNotificacao(models.Model):
    """Templates personalizáveis para notificações"""
    TIPO_CHOICES = [
        ('COBRANCA', 'Cobrança'),
        ('VENCIMENTO', 'Vencimento'),
        ('BOAS_VINDAS', 'Boas-vindas'),
        ('RENOVACAO', 'Renovação'),
        ('MANUTENCAO', 'Manutenção'),
        ('COMUNICADO', 'Comunicado'),
        ('LEMBRETE', 'Lembrete'),
        ('PERSONALIZADO', 'Personalizado'),
    ]
    
    FORMATO_CHOICES = [
        ('HTML', 'HTML'),
        ('TEXTO', 'Texto Simples'),
    ]
    
    nome = models.CharField(max_length=200)
    categoria = models.ForeignKey(CategoriaTemplate, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    assunto_template = models.CharField(max_length=300, help_text='Use {{variavel}} para campos dinâmicos')
    corpo_template = models.TextField(help_text='Use {{variavel}} para campos dinâmicos')
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='HTML')
    variaveis_disponiveis = models.JSONField(default=dict, help_text='Variáveis disponíveis para este template')
    preview_dados = models.JSONField(default=dict, help_text='Dados de exemplo para preview')
    ativo = models.BooleanField(default=True)
    padrao = models.BooleanField(default=False, help_text='Template padrão para este tipo')
    usuario_criador = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Template de Notificação'
        verbose_name_plural = 'Templates de Notificação'
        ordering = ['categoria__nome', 'nome']
        unique_together = ['tipo', 'padrao']
    
    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"
    
    def renderizar(self, contexto):
        """Renderiza o template com os dados fornecidos"""
        assunto = self.assunto_template
        corpo = self.corpo_template
        
        for chave, valor in contexto.items():
            placeholder = f"{{{{{chave}}}}}"
            assunto = assunto.replace(placeholder, str(valor))
            corpo = corpo.replace(placeholder, str(valor))
        
        return assunto, corpo
    
    def renderizar_assunto(self, contexto):
        """Renderiza o assunto do template com o contexto fornecido"""
        try:
            from django.template import Template, Context
            template = Template(self.assunto_template)
            return template.render(Context(contexto))
        except Exception as e:
            return f"Erro na renderização: {str(e)}"
    
    def renderizar_corpo(self, contexto):
        """Renderiza o corpo do template com o contexto fornecido"""
        try:
            from django.template import Template, Context
            template = Template(self.corpo_template)
            return template.render(Context(contexto))
        except Exception as e:
            return f"Erro na renderização: {str(e)}"
    
    def preview_renderizado(self, contexto=None):
        """Gera preview do template renderizado"""
        if not contexto:
            contexto = self.preview_dados or {}
        
        return {
            'assunto': self.renderizar_assunto(contexto),
            'corpo': self.renderizar_corpo(contexto)
        }

class NotificacaoAgendada(models.Model):
    """Sistema de agendamento de notificações"""
    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('PROCESSANDO', 'Processando'),
        ('ENVIADA', 'Enviada'),
        ('ERRO', 'Erro'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    RECORRENCIA_CHOICES = [
        ('UNICA', 'Única'),
        ('DIARIA', 'Diária'),
        ('SEMANAL', 'Semanal'),
        ('MENSAL', 'Mensal'),
        ('ANUAL', 'Anual'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    
    template = models.ForeignKey(TemplateNotificacao, on_delete=models.CASCADE)
    nome_campanha = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    # Destinatários
    inquilinos = models.ManyToManyField(Inquilino, blank=True)
    filtro_personalizado = models.JSONField(default=dict, help_text='Filtros para seleção automática')
    
    # Agendamento
    data_envio = models.DateTimeField()
    recorrencia = models.CharField(max_length=20, choices=RECORRENCIA_CHOICES, default='UNICA')
    intervalo_recorrencia = models.PositiveIntegerField(default=1, help_text='Intervalo para recorrência')
    data_fim_recorrencia = models.DateTimeField(null=True, blank=True)
    
    # Configurações
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='NORMAL')
    max_tentativas = models.PositiveIntegerField(default=3)
    intervalo_tentativas = models.PositiveIntegerField(default=60, help_text='Minutos entre tentativas')
    
    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGENDADA')
    tentativas_realizadas = models.PositiveIntegerField(default=0)
    ultima_tentativa = models.DateTimeField(null=True, blank=True)
    proximo_envio = models.DateTimeField(null=True, blank=True)
    
    # Auditoria
    usuario_criador = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notificação Agendada'
        verbose_name_plural = 'Notificações Agendadas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nome_campanha} - {self.get_status_display()}"

class Notificacao(models.Model):
    """Registro individual de cada notificação enviada"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ENVIANDO', 'Enviando'),
        ('ENVIADA', 'Enviada'),
        ('ENTREGUE', 'Entregue'),
        ('ABERTA', 'Aberta'),
        ('CLICADA', 'Clicada'),
        ('ERRO', 'Erro'),
        ('REJEITADA', 'Rejeitada'),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', 'E-mail'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('PUSH', 'Push Notification'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    
    # Relacionamentos
    template = models.ForeignKey(TemplateNotificacao, on_delete=models.CASCADE, null=True, blank=True)
    agendamento = models.ForeignKey(NotificacaoAgendada, on_delete=models.CASCADE, null=True, blank=True)
    inquilino = models.ForeignKey(Inquilino, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True)
    
    # Conteúdo
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, default='EMAIL')
    destinatario = models.CharField(max_length=200)
    assunto = models.CharField(max_length=300)
    corpo = models.TextField()
    corpo_html = models.TextField(blank=True)
    anexos = models.JSONField(default=list, help_text='Lista de anexos')
    
    # Configurações
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='NORMAL')
    tentativas_maximas = models.PositiveIntegerField(default=3)
    tentativas_realizadas = models.PositiveIntegerField(default=0)
    
    # Status e tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_envio = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    data_abertura = models.DateTimeField(null=True, blank=True)
    data_clique = models.DateTimeField(null=True, blank=True)
    
    # Metadados
    ip_abertura = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    tracking_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Erros e logs
    erro_envio = models.TextField(blank=True)
    log_tentativas = models.JSONField(default=list)
    
    # Auditoria
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'canal']),
            models.Index(fields=['inquilino', 'created_at']),
            models.Index(fields=['tracking_id']),
        ]
    
    def __str__(self):
        return f"{self.assunto} - {self.inquilino.nome}"
    
    def marcar_como_aberta(self, ip=None, user_agent=None):
        """Marca a notificação como aberta"""
        if self.status in ['ENVIADA', 'ENTREGUE']:
            self.status = 'ABERTA'
            self.data_abertura = timezone.now()
            self.ip_abertura = ip
            self.user_agent = user_agent
            self.save()
    
    def marcar_como_clicada(self):
        """Marca a notificação como clicada"""
        if self.status in ['ENVIADA', 'ENTREGUE', 'ABERTA']:
            self.status = 'CLICADA'
            self.data_clique = timezone.now()
            self.save()

class EstatisticaNotificacao(models.Model):
    """Estatísticas agregadas de notificações"""
    PERIODO_CHOICES = [
        ('DIARIO', 'Diário'),
        ('SEMANAL', 'Semanal'),
        ('MENSAL', 'Mensal'),
        ('ANUAL', 'Anual'),
    ]
    
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    data_referencia = models.DateField()
    canal = models.CharField(max_length=20, choices=Notificacao.CANAL_CHOICES)
    template = models.ForeignKey(TemplateNotificacao, on_delete=models.CASCADE, null=True, blank=True)
    
    # Métricas de envio
    total_enviadas = models.PositiveIntegerField(default=0)
    total_entregues = models.PositiveIntegerField(default=0)
    total_abertas = models.PositiveIntegerField(default=0)
    total_clicadas = models.PositiveIntegerField(default=0)
    total_erros = models.PositiveIntegerField(default=0)
    total_rejeitadas = models.PositiveIntegerField(default=0)
    
    # Taxas calculadas
    taxa_entrega = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_abertura = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_clique = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    taxa_erro = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Tempo médio
    tempo_medio_abertura = models.DurationField(null=True, blank=True)
    tempo_medio_clique = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Estatística de Notificação'
        verbose_name_plural = 'Estatísticas de Notificações'
        unique_together = ['periodo', 'data_referencia', 'canal', 'template']
        ordering = ['-data_referencia']
    
    def __str__(self):
        return f"{self.get_periodo_display()} - {self.data_referencia} - {self.get_canal_display()}"
    
    def calcular_taxas(self):
        """Calcula as taxas baseadas nos totais"""
        if self.total_enviadas > 0:
            self.taxa_entrega = (self.total_entregues / self.total_enviadas) * 100
            self.taxa_erro = (self.total_erros / self.total_enviadas) * 100
            
            if self.total_entregues > 0:
                self.taxa_abertura = (self.total_abertas / self.total_entregues) * 100
                
            if self.total_abertas > 0:
                self.taxa_clique = (self.total_clicadas / self.total_abertas) * 100
        
        self.save()

# Modelo legado mantido para compatibilidade
class TipoNotificacao(models.Model):
    """Modelo legado - mantido para compatibilidade"""
    nome = models.CharField(max_length=100)
    template_assunto = models.CharField(max_length=200)
    template_corpo = models.TextField()
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tipo de Notificação (Legado)'
        verbose_name_plural = 'Tipos de Notificação (Legado)'
    
    def __str__(self):
        return self.nome


class CobrancaAutomaticaLog(models.Model):
    STATUS_CHOICES = [
        ('ENVIADA', 'Enviada'),
        ('ERRO', 'Erro'),
        ('SIMULADA', 'Simulada'),
    ]
    
    TIPO_CHOICES = [
        ('ALUGUEL', 'Aluguel'),
        ('IPTU_CONTRATO', 'IPTU (Contrato)'),
        ('IPTU_PARCELA', 'IPTU (Parcela)'),
    ]
    
    tenant = models.ForeignKey('saas.Tenant', on_delete=models.CASCADE)
    inquilino = models.ForeignKey(Inquilino, on_delete=models.CASCADE)
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, null=True, blank=True)
    
    parcela = models.ForeignKey('financeiro.Parcela', on_delete=models.SET_NULL, null=True, blank=True)
    parcela_iptu = models.ForeignKey('financeiro.ParcelaIPTU', on_delete=models.SET_NULL, null=True, blank=True)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nivel = models.PositiveSmallIntegerField()
    
    canal = models.CharField(max_length=20, default='WHATSAPP')
    destinatario = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    provider = models.CharField(max_length=50, blank=True)
    provider_message_id = models.CharField(max_length=255, blank=True)
    erro = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cobrança Automática (Log)'
        verbose_name_plural = 'Cobranças Automáticas (Logs)'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'tipo', 'nivel', 'parcela'],
                condition=Q(parcela__isnull=False),
                name='uniq_cobranca_auto_parcela_nivel'
            ),
            models.UniqueConstraint(
                fields=['tenant', 'tipo', 'nivel', 'parcela_iptu'],
                condition=Q(parcela_iptu__isnull=False),
                name='uniq_cobranca_auto_parcela_iptu_nivel'
            ),
        ]


class WhatsAppMensagemConfig(models.Model):
    TIPO_CHOICES = [
        ('GERAL', 'Mensagem Geral'),
        ('BOAS_VINDAS', 'Boas-vindas'),
        ('COBRANCA_ALUGUEL', 'Cobrança Aluguel'),
        ('COBRANCA_IPTU', 'Cobrança IPTU'),
        ('CONTRATO_VENCENDO', 'Contrato Vencendo'),
    ]

    tenant = models.ForeignKey('saas.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensagem = models.TextField(blank=True)
    anexo = models.FileField(upload_to='notificacoes/whatsapp/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração WhatsApp'
        verbose_name_plural = 'Configurações WhatsApp'
        ordering = ['tipo']
        unique_together = ['tenant', 'tipo']

    def __str__(self):
        tenant_nome = self.tenant.nome_empresa if self.tenant else 'Global'
        return f'{tenant_nome} - {self.get_tipo_display()}'
