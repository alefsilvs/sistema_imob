from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import logging
from notificacoes.models import NotificacaoAgendada, Notificacao, TemplateNotificacao
from core.models import Inquilino
from contratos.models import Contrato

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processa notificações agendadas e envia quando necessário'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem enviar notificações (apenas mostra o que seria enviado)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o processamento mesmo se já foi executado recentemente',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write('Iniciando processamento de notificações agendadas...')
        
        # Buscar notificações agendadas que devem ser processadas
        agora = timezone.now()
        notificacoes_pendentes = NotificacaoAgendada.objects.filter(
            status='AGENDADA',
            proximo_envio__lte=agora
        ).select_related('template')
        
        if not notificacoes_pendentes.exists():
            self.stdout.write(
                self.style.SUCCESS('Nenhuma notificação agendada para processar.')
            )
            return
        
        processadas = 0
        erros = 0
        
        for agendamento in notificacoes_pendentes:
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Processaria: {agendamento.nome_campanha}'
                    )
                    continue
                
                # Marcar como processando
                agendamento.status = 'PROCESSANDO'
                agendamento.save()
                
                # Processar envio
                sucesso = self.processar_agendamento(agendamento)
                
                if sucesso:
                    # Calcular próximo envio se for recorrente
                    if agendamento.recorrencia != 'UNICA':
                        proximo_envio = self.calcular_proximo_envio(
                            agendamento.data_envio, 
                            agendamento.recorrencia,
                            agendamento.intervalo_recorrencia
                        )
                        
                        if (agendamento.data_fim_recorrencia is None or 
                            proximo_envio <= agendamento.data_fim_recorrencia):
                            agendamento.proximo_envio = proximo_envio
                            agendamento.status = 'AGENDADA'
                        else:
                            agendamento.status = 'ENVIADA'
                    else:
                        agendamento.status = 'ENVIADA'
                    
                    processadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Processada: {agendamento.nome_campanha}'
                        )
                    )
                else:
                    agendamento.status = 'ERRO'
                    erros += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Erro ao processar: {agendamento.nome_campanha}'
                        )
                    )
                
                agendamento.ultima_tentativa = agora
                agendamento.tentativas_realizadas += 1
                agendamento.save()
                
            except Exception as e:
                logger.error(f'Erro ao processar agendamento {agendamento.id}: {e}')
                agendamento.status = 'ERRO'
                agendamento.save()
                erros += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processamento concluído: {processadas} enviadas, {erros} erros'
            )
        )
    
    def processar_agendamento(self, agendamento):
        """Processa um agendamento específico"""
        try:
            # Obter inquilinos baseado nos filtros
            inquilinos = self.obter_inquilinos(agendamento)
            
            if not inquilinos:
                logger.warning(f'Nenhum inquilino encontrado para {agendamento.nome_campanha}')
                return False
            
            enviadas = 0
            for inquilino in inquilinos:
                try:
                    # Criar contexto para o template
                    contexto = self.criar_contexto(inquilino, agendamento)
                    
                    # Renderizar template
                    assunto = agendamento.template.renderizar_assunto(contexto)
                    corpo = agendamento.template.renderizar_corpo(contexto)
                    
                    # Criar notificação
                    notificacao = Notificacao.objects.create(
                        template=agendamento.template,
                        agendamento=agendamento,
                        inquilino=inquilino,
                        contrato=self.obter_contrato_ativo(inquilino),
                        canal='EMAIL',  # Por enquanto apenas email
                        destinatario=inquilino.email,
                        assunto=assunto,
                        corpo=corpo,
                        corpo_html=corpo if agendamento.template.formato == 'HTML' else '',
                        prioridade=agendamento.prioridade,
                        usuario=agendamento.usuario_criador
                    )
                    
                    # Enviar notificação
                    if self.enviar_notificacao(notificacao):
                        enviadas += 1
                    
                except Exception as e:
                    logger.error(f'Erro ao processar inquilino {inquilino.id}: {e}')
                    continue
            
            return enviadas > 0
            
        except Exception as e:
            logger.error(f'Erro no processamento do agendamento: {e}')
            return False
    
    def obter_inquilinos(self, agendamento):
        """Obtém lista de inquilinos baseado nos filtros do agendamento"""
        if agendamento.inquilinos.exists():
            return agendamento.inquilinos.all()
        
        # Aplicar filtros personalizados se existirem
        inquilinos = Inquilino.objects.filter(ativo=True)
        
        if agendamento.filtro_personalizado:
            filtros = agendamento.filtro_personalizado
            
            # Exemplos de filtros possíveis
            if 'contratos_ativos' in filtros and filtros['contratos_ativos']:
                inquilinos = inquilinos.filter(
                    contrato__data_fim__gte=timezone.now().date()
                )
            
            if 'vencimento_proximo' in filtros:
                dias = filtros['vencimento_proximo']
                data_limite = timezone.now().date() + timedelta(days=dias)
                inquilinos = inquilinos.filter(
                    contrato__data_fim__lte=data_limite
                )
        
        return inquilinos
    
    def criar_contexto(self, inquilino, agendamento):
        """Cria contexto para renderização do template"""
        contrato = self.obter_contrato_ativo(inquilino)
        
        contexto = {
            'inquilino': {
                'nome': inquilino.nome,
                'email': inquilino.email,
                'telefone': inquilino.telefone,
                'cpf': inquilino.cpf,
            },
            'data_atual': timezone.now().strftime('%d/%m/%Y'),
            'campanha': agendamento.nome_campanha,
        }
        
        if contrato:
            contexto['contrato'] = {
                'numero': contrato.numero,
                'valor': contrato.valor_aluguel,
                'data_inicio': contrato.data_inicio.strftime('%d/%m/%Y'),
                'data_fim': contrato.data_fim.strftime('%d/%m/%Y'),
                'dia_vencimento': contrato.dia_vencimento,
            }
            
            if hasattr(contrato, 'imovel'):
                contexto['imovel'] = {
                    'endereco': contrato.imovel.endereco_completo,
                    'codigo': contrato.imovel.codigo,
                }
        
        return contexto
    
    def obter_contrato_ativo(self, inquilino):
        """Obtém contrato ativo do inquilino"""
        return Contrato.objects.filter(
            inquilino=inquilino,
            data_fim__gte=timezone.now().date()
        ).first()
    
    def enviar_notificacao(self, notificacao):
        """Envia uma notificação por email"""
        try:
            notificacao.status = 'ENVIANDO'
            notificacao.save()
            
            # Configurar email
            from_email = settings.DEFAULT_FROM_EMAIL
            
            # Enviar email
            send_mail(
                subject=notificacao.assunto,
                message=notificacao.corpo,
                from_email=from_email,
                recipient_list=[notificacao.destinatario],
                html_message=notificacao.corpo_html if notificacao.corpo_html else None,
                fail_silently=False
            )
            
            # Marcar como enviada
            notificacao.status = 'ENVIADA'
            notificacao.data_envio = timezone.now()
            notificacao.save()
            
            return True
            
        except Exception as e:
            logger.error(f'Erro ao enviar notificação {notificacao.id}: {e}')
            notificacao.status = 'ERRO'
            notificacao.erro_envio = str(e)
            notificacao.tentativas_realizadas += 1
            notificacao.save()
            return False
    
    def calcular_proximo_envio(self, data_base, recorrencia, intervalo):
        """Calcula a próxima data de envio baseada na recorrência"""
        if recorrencia == 'DIARIA':
            return data_base + timedelta(days=intervalo)
        elif recorrencia == 'SEMANAL':
            return data_base + timedelta(weeks=intervalo)
        elif recorrencia == 'MENSAL':
            # Aproximação: 30 dias por mês
            return data_base + timedelta(days=30 * intervalo)
        elif recorrencia == 'ANUAL':
            return data_base + timedelta(days=365 * intervalo)
        else:
            return data_base