from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from notificacoes.models import NotificacaoAgendada, TemplateNotificacao
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Agenda verificações automáticas de vencimentos de contratos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--periodo',
            type=str,
            choices=['diario', 'semanal'],
            default='semanal',
            help='Período de verificação (diario ou semanal)',
        )
        parser.add_argument(
            '--dias-antecedencia',
            type=str,
            default='30,15,7',
            help='Dias de antecedência separados por vírgula (ex: 30,15,7)',
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Nome do template a usar',
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista agendamentos existentes',
        )
        parser.add_argument(
            '--cancelar',
            action='store_true',
            help='Cancela agendamentos existentes',
        )
    
    def handle(self, *args, **options):
        if options['listar']:
            self.listar_agendamentos()
            return
        
        if options['cancelar']:
            self.cancelar_agendamentos()
            return
        
        periodo = options['periodo']
        dias_str = options['dias_antecedencia']
        template_nome = options['template']
        
        # Processar dias de antecedência
        try:
            dias_lista = [int(d.strip()) for d in dias_str.split(',')]
        except ValueError:
            self.stdout.write(
                self.style.ERROR('Formato inválido para dias-antecedencia. Use números separados por vírgula.')
            )
            return
        
        # Obter template
        template = self.obter_template(template_nome)
        if not template:
            self.stdout.write(
                self.style.ERROR('Template não encontrado!')
            )
            return
        
        # Obter usuário sistema
        usuario_sistema = User.objects.filter(is_superuser=True).first()
        if not usuario_sistema:
            self.stdout.write(
                self.style.ERROR('Usuário administrador não encontrado!')
            )
            return
        
        self.stdout.write(f'Criando agendamentos para verificação {periodo}...')
        
        agendamentos_criados = 0
        
        for dias in dias_lista:
            nome_campanha = f'Vencimento Contratos - {dias} dias'
            
            # Verificar se já existe
            if NotificacaoAgendada.objects.filter(
                nome_campanha=nome_campanha,
                status__in=['AGENDADA', 'PROCESSANDO']
            ).exists():
                self.stdout.write(
                    f'⚠️  Agendamento "{nome_campanha}" já existe'
                )
                continue
            
            # Calcular próximo envio
            if periodo == 'diario':
                proximo_envio = timezone.now() + timedelta(hours=1)
                recorrencia = 'DIARIA'
                intervalo = 1
            else:  # semanal
                proximo_envio = timezone.now() + timedelta(hours=1)
                recorrencia = 'SEMANAL'
                intervalo = 1
            
            # Criar agendamento
            agendamento = NotificacaoAgendada.objects.create(
                template=template,
                nome_campanha=nome_campanha,
                descricao=f'Verificação automática de contratos com vencimento em {dias} dias',
                data_envio=proximo_envio,
                proximo_envio=proximo_envio,
                recorrencia=recorrencia,
                intervalo_recorrencia=intervalo,
                filtro_personalizado={
                    'vencimento_proximo': dias,
                    'contratos_ativos': True,
                    'comando_personalizado': f'verificar_vencimentos --dias {dias}'
                },
                prioridade='ALTA',
                usuario_criador=usuario_sistema
            )
            
            agendamentos_criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Agendamento criado: {nome_campanha} ({recorrencia.lower()})'
                )
            )
        
        self.stdout.write(f'\nTotal de agendamentos criados: {agendamentos_criados}')
        
        if agendamentos_criados > 0:
            self.stdout.write('\nPara ativar o processamento automático, execute:')
            self.stdout.write('python manage.py servico_notificacoes')
    
    def obter_template(self, template_nome=None):
        """Obtém template de notificação"""
        try:
            if template_nome:
                return TemplateNotificacao.objects.get(
                    nome__icontains=template_nome,
                    ativo=True
                )
            else:
                return TemplateNotificacao.objects.filter(
                    tipo='VENCIMENTO',
                    ativo=True,
                    padrao=True
                ).first() or TemplateNotificacao.objects.filter(
                    tipo='VENCIMENTO',
                    ativo=True
                ).first()
        except TemplateNotificacao.DoesNotExist:
            return None
    
    def listar_agendamentos(self):
        """Lista agendamentos de verificação existentes"""
        agendamentos = NotificacaoAgendada.objects.filter(
            nome_campanha__startswith='Vencimento Contratos'
        ).order_by('nome_campanha')
        
        if not agendamentos.exists():
            self.stdout.write('Nenhum agendamento de verificação encontrado.')
            return
        
        self.stdout.write('AGENDAMENTOS DE VERIFICAÇÃO:')
        self.stdout.write('='*50)
        
        for agendamento in agendamentos:
            status_color = {
                'AGENDADA': self.style.SUCCESS,
                'PROCESSANDO': self.style.WARNING,
                'ENVIADA': self.style.SUCCESS,
                'ERRO': self.style.ERROR,
                'CANCELADA': self.style.ERROR,
            }.get(agendamento.status, self.style.SUCCESS)
            
            self.stdout.write(
                f'• {agendamento.nome_campanha}'
            )
            self.stdout.write(
                f'  Status: {status_color(agendamento.status)}'
            )
            self.stdout.write(
                f'  Recorrência: {agendamento.get_recorrencia_display()}'
            )
            self.stdout.write(
                f'  Próximo envio: {agendamento.proximo_envio.strftime("%d/%m/%Y %H:%M") if agendamento.proximo_envio else "N/A"}'
            )
            self.stdout.write('')
    
    def cancelar_agendamentos(self):
        """Cancela agendamentos existentes"""
        agendamentos = NotificacaoAgendada.objects.filter(
            nome_campanha__startswith='Vencimento Contratos',
            status__in=['AGENDADA', 'PROCESSANDO']
        )
        
        if not agendamentos.exists():
            self.stdout.write('Nenhum agendamento ativo encontrado.')
            return
        
        count = agendamentos.count()
        agendamentos.update(status='CANCELADA')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} agendamentos cancelados.')
        )