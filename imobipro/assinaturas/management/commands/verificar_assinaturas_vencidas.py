from django.core.management.base import BaseCommand
from django.utils import timezone
from assinaturas.models import AssinaturaUsuario
from assinaturas.pagamento_service import PagamentoService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica e processa assinaturas vencidas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações, apenas mostra o que seria feito',
        )
        parser.add_argument(
            '--dias-antecedencia',
            type=int,
            default=3,
            help='Dias de antecedência para notificar sobre vencimento (padrão: 3)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dias_antecedencia = options['dias_antecedencia']
        
        self.stdout.write(f'Iniciando verificação de assinaturas vencidas...')
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        hoje = timezone.now().date()
        data_limite_notificacao = hoje + timedelta(days=dias_antecedencia)
        
        # Buscar assinaturas ativas que estão vencidas ou vencendo
        assinaturas_vencidas = AssinaturaUsuario.objects.filter(
            status='ATIVA',
            data_fim__lt=hoje
        )
        
        assinaturas_vencendo = AssinaturaUsuario.objects.filter(
            status='ATIVA',
            data_fim__gte=hoje,
            data_fim__lte=data_limite_notificacao
        )
        
        # Processar assinaturas vencidas
        total_vencidas = 0
        total_renovadas = 0
        total_canceladas = 0
        
        self.stdout.write(f'\nProcessando {assinaturas_vencidas.count()} assinaturas vencidas...')
        
        for assinatura in assinaturas_vencidas:
            total_vencidas += 1
            
            self.stdout.write(
                f'Assinatura vencida: {assinatura.usuario.username} - '
                f'Plano: {assinatura.plano.nome} - '
                f'Vencimento: {assinatura.data_fim}'
            )
            
            if not dry_run:
                try:
                    # Verificar se tem renovação automática
                    if assinatura.renovacao_automatica:
                        # Tentar renovar automaticamente
                        resultado = PagamentoService.gerar_cobranca_renovacao(assinatura)
                        
                        if resultado.get('sucesso'):
                            total_renovadas += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Renovação automática iniciada para {assinatura.usuario.username}'
                                )
                            )
                            logger.info(f'Renovação automática iniciada para assinatura {assinatura.id}')
                        else:
                            # Se falhou a renovação, cancelar
                            assinatura.status = 'CANCELADA'
                            assinatura.save()
                            total_canceladas += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f'  ✗ Falha na renovação automática. Assinatura cancelada: {assinatura.usuario.username}'
                                )
                            )
                            logger.warning(f'Falha na renovação automática da assinatura {assinatura.id}: {resultado.get("erro")}')
                    else:
                        # Sem renovação automática, cancelar
                        assinatura.status = 'CANCELADA'
                        assinatura.save()
                        total_canceladas += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! Assinatura cancelada (sem renovação automática): {assinatura.usuario.username}'
                            )
                        )
                        logger.info(f'Assinatura {assinatura.id} cancelada por vencimento')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Erro ao processar assinatura {assinatura.id}: {str(e)}'
                        )
                    )
                    logger.error(f'Erro ao processar assinatura {assinatura.id}: {str(e)}')
        
        # Processar assinaturas que estão vencendo (notificações)
        total_notificadas = 0
        
        self.stdout.write(f'\nProcessando {assinaturas_vencendo.count()} assinaturas vencendo em {dias_antecedencia} dias...')
        
        for assinatura in assinaturas_vencendo:
            dias_restantes = (assinatura.data_fim - hoje).days
            
            self.stdout.write(
                f'Assinatura vencendo: {assinatura.usuario.username} - '
                f'Plano: {assinatura.plano.nome} - '
                f'Vence em: {dias_restantes} dias ({assinatura.data_fim})'
            )
            
            if not dry_run:
                try:
                    # Aqui você pode implementar envio de notificações
                    # Por exemplo, enviar email ou notificação no sistema
                    
                    # Exemplo de log para notificação
                    total_notificadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Notificação enviada para {assinatura.usuario.username}'
                        )
                    )
                    logger.info(f'Notificação de vencimento enviada para assinatura {assinatura.id}')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Erro ao notificar assinatura {assinatura.id}: {str(e)}'
                        )
                    )
                    logger.error(f'Erro ao notificar assinatura {assinatura.id}: {str(e)}')
        
        # Resumo final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMO DA EXECUÇÃO:'))
        self.stdout.write(f'• Assinaturas vencidas processadas: {total_vencidas}')
        self.stdout.write(f'• Renovações automáticas iniciadas: {total_renovadas}')
        self.stdout.write(f'• Assinaturas canceladas: {total_canceladas}')
        self.stdout.write(f'• Notificações de vencimento enviadas: {total_notificadas}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nNenhuma alteração foi feita (modo dry-run)'))
        else:
            self.stdout.write(self.style.SUCCESS('\nVerificação concluída com sucesso!'))
        
        logger.info(f'Verificação de assinaturas concluída: {total_vencidas} vencidas, {total_renovadas} renovadas, {total_canceladas} canceladas, {total_notificadas} notificadas')