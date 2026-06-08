from django.core.management.base import BaseCommand
from django.utils import timezone
from pagamentos.models import PagamentoOnline
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Processa pagamentos pendentes e verifica status de transações'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações, apenas mostra o que seria feito',
        )
        parser.add_argument(
            '--timeout-horas',
            type=int,
            default=24,
            help='Horas para considerar um pagamento como timeout (padrão: 24)',
        )
        parser.add_argument(
            '--gateway',
            type=str,
            choices=['PIX', 'CARTAO', 'BOLETO'],
            help='Processar apenas pagamentos de um gateway específico',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        timeout_horas = options['timeout_horas']
        gateway_filtro = options.get('gateway')
        
        self.stdout.write(f'Iniciando processamento de pagamentos pendentes...')
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita'))
        
        agora = timezone.now()
        data_timeout = agora - timedelta(hours=timeout_horas)
        
        # Filtros base
        filtros = {
            'status__in': ['PENDENTE', 'PROCESSANDO']
        }
        
        if gateway_filtro:
            filtros['metodo_pagamento'] = gateway_filtro
        
        # Buscar pagamentos pendentes
        pagamentos_pendentes = PagamentoOnline.objects.filter(**filtros)
        
        total_processados = 0
        total_aprovados = 0
        total_rejeitados = 0
        total_timeout = 0
        total_erros = 0
        
        self.stdout.write(f'\nEncontrados {pagamentos_pendentes.count()} pagamentos para processar...')
        
        for pagamento in pagamentos_pendentes:
            total_processados += 1
            
            self.stdout.write(
                f'Processando pagamento {pagamento.id}: '
                f'{pagamento.metodo_pagamento} - '
                f'R$ {pagamento.valor_original} - '
                f'Status: {pagamento.status} - '
                f'Criado: {pagamento.data_criacao}'
            )
            
            if not dry_run:
                try:
                    # Verificar se o pagamento está em timeout
                    if pagamento.data_criacao < data_timeout:
                        pagamento.status = 'CANCELADO'
                        pagamento.data_atualizacao = agora
                        pagamento.observacoes = f'Cancelado por timeout após {timeout_horas}h'
                        pagamento.save()
                        
                        total_timeout += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ! Pagamento {pagamento.id} cancelado por timeout'
                            )
                        )
                        logger.warning(f'Pagamento {pagamento.id} cancelado por timeout')
                        continue
                    
                    # Processar baseado no método de pagamento
                    if pagamento.metodo_pagamento == 'PIX':
                        resultado = self._processar_pix(pagamento)
                    elif pagamento.metodo_pagamento == 'CARTAO':
                        resultado = self._processar_cartao(pagamento)
                    elif pagamento.metodo_pagamento == 'BOLETO':
                        resultado = self._processar_boleto(pagamento)
                    else:
                        resultado = {'status': 'ERRO', 'mensagem': 'Método de pagamento não suportado'}
                    
                    # Atualizar status baseado no resultado
                    if resultado['status'] == 'APROVADO':
                        pagamento.status = 'APROVADO'
                        pagamento.data_aprovacao = agora
                        total_aprovados += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Pagamento {pagamento.id} aprovado'
                            )
                        )
                        logger.info(f'Pagamento {pagamento.id} aprovado')
                        
                    elif resultado['status'] == 'REJEITADO':
                        pagamento.status = 'REJEITADO'
                        total_rejeitados += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Pagamento {pagamento.id} rejeitado: {resultado.get("mensagem", "")}'
                            )
                        )
                        logger.warning(f'Pagamento {pagamento.id} rejeitado: {resultado.get("mensagem", "")}')
                        
                    elif resultado['status'] == 'PENDENTE':
                        # Mantém pendente, apenas atualiza data
                        self.stdout.write(
                            f'  - Pagamento {pagamento.id} ainda pendente'
                        )
                        
                    else:
                        total_erros += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Erro ao processar pagamento {pagamento.id}: {resultado.get("mensagem", "")}'
                            )
                        )
                        logger.error(f'Erro ao processar pagamento {pagamento.id}: {resultado.get("mensagem", "")}')
                    
                    # Atualizar observações se houver
                    if resultado.get('mensagem'):
                        pagamento.observacoes = resultado['mensagem']
                    
                    pagamento.data_atualizacao = agora
                    pagamento.save()
                    
                except Exception as e:
                    total_erros += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Erro inesperado ao processar pagamento {pagamento.id}: {str(e)}'
                        )
                    )
                    logger.error(f'Erro inesperado ao processar pagamento {pagamento.id}: {str(e)}')
        
        # Resumo final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMO DO PROCESSAMENTO:'))
        self.stdout.write(f'• Total de pagamentos processados: {total_processados}')
        self.stdout.write(f'• Pagamentos aprovados: {total_aprovados}')
        self.stdout.write(f'• Pagamentos rejeitados: {total_rejeitados}')
        self.stdout.write(f'• Pagamentos cancelados por timeout: {total_timeout}')
        self.stdout.write(f'• Erros encontrados: {total_erros}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nNenhuma alteração foi feita (modo dry-run)'))
        else:
            self.stdout.write(self.style.SUCCESS('\nProcessamento concluído com sucesso!'))
        
        logger.info(f'Processamento de pagamentos concluído: {total_processados} processados, {total_aprovados} aprovados, {total_rejeitados} rejeitados, {total_timeout} timeout, {total_erros} erros')
    
    def _processar_pix(self, pagamento):
        """
        Processa pagamento PIX
        Aqui você implementaria a integração com o gateway PIX
        """
        try:
            # Exemplo de verificação de status PIX
            # Substitua pela integração real com seu provedor PIX
            
            # Simulação de verificação de status
            if pagamento.transaction_id:
                # Aqui você faria a consulta real ao gateway
                # status_gateway = consultar_status_pix(pagamento.transaction_id)
                
                # Por enquanto, simulação baseada no tempo
                import random
                if random.choice([True, False]):  # 50% de chance de aprovação
                    return {'status': 'APROVADO', 'mensagem': 'PIX confirmado'}
                else:
                    return {'status': 'PENDENTE', 'mensagem': 'PIX ainda não confirmado'}
            else:
                return {'status': 'ERRO', 'mensagem': 'Transaction ID não encontrado'}
                
        except Exception as e:
            return {'status': 'ERRO', 'mensagem': f'Erro ao consultar PIX: {str(e)}'}
    
    def _processar_cartao(self, pagamento):
        """
        Processa pagamento com cartão
        Aqui você implementaria a integração com o gateway de cartão
        """
        try:
            # Exemplo de verificação de status de cartão
            # Substitua pela integração real com seu provedor
            
            if pagamento.transaction_id:
                # Aqui você faria a consulta real ao gateway
                # status_gateway = consultar_status_cartao(pagamento.transaction_id)
                
                # Simulação
                import random
                chance = random.random()
                if chance > 0.8:  # 20% de chance de rejeição
                    return {'status': 'REJEITADO', 'mensagem': 'Cartão recusado'}
                elif chance > 0.1:  # 70% de chance de aprovação
                    return {'status': 'APROVADO', 'mensagem': 'Cartão aprovado'}
                else:  # 10% ainda pendente
                    return {'status': 'PENDENTE', 'mensagem': 'Processando cartão'}
            else:
                return {'status': 'ERRO', 'mensagem': 'Transaction ID não encontrado'}
                
        except Exception as e:
            return {'status': 'ERRO', 'mensagem': f'Erro ao consultar cartão: {str(e)}'}
    
    def _processar_boleto(self, pagamento):
        """
        Processa pagamento com boleto
        Aqui você implementaria a integração com o gateway de boleto
        """
        try:
            # Exemplo de verificação de status de boleto
            # Substitua pela integração real com seu provedor
            
            if pagamento.transaction_id:
                # Aqui você faria a consulta real ao gateway
                # status_gateway = consultar_status_boleto(pagamento.transaction_id)
                
                # Simulação
                import random
                chance = random.random()
                if chance > 0.7:  # 30% de chance de pagamento
                    return {'status': 'APROVADO', 'mensagem': 'Boleto pago'}
                else:  # 70% ainda pendente
                    return {'status': 'PENDENTE', 'mensagem': 'Boleto não pago'}
            else:
                return {'status': 'ERRO', 'mensagem': 'Transaction ID não encontrado'}
                
        except Exception as e:
            return {'status': 'ERRO', 'mensagem': f'Erro ao consultar boleto: {str(e)}'}