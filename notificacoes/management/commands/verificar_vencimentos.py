from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime, timedelta
import logging
from contratos.models import Contrato
from notificacoes.models import TemplateNotificacao, Notificacao
from notificacoes.services import WhatsAppService
from core.models import Inquilino
from pagamentos.models import ConfiguracaoPagamento

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica contratos próximos do vencimento e envia notificações automáticas via Email e WhatsApp'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Dias de antecedência para notificar (padrão: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem enviar notificações (apenas mostra o que seria enviado)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o envio mesmo se já foi enviado recentemente',
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Nome específico do template a usar (opcional)',
        )
    
    def handle(self, *args, **options):
        dias_antecedencia = options['dias']
        dry_run = options['dry_run']
        force = options['force']
        template_nome = options['template']
        
        self.stdout.write(f'Verificando contratos com vencimento em {dias_antecedencia} dias...')
        
        # Calcular data limite
        data_limite = timezone.now().date() + timedelta(days=dias_antecedencia)
        
        # Buscar contratos próximos do vencimento
        contratos_vencendo = Contrato.objects.filter(
            status='ATIVO',
            data_fim__lte=data_limite,
            data_fim__gte=timezone.now().date()
        ).select_related('inquilino', 'imovel')
        
        if not contratos_vencendo.exists():
            self.stdout.write(
                self.style.SUCCESS('Nenhum contrato próximo do vencimento encontrado.')
            )
            return
        
        self.stdout.write(f'Encontrados {contratos_vencendo.count()} contratos próximos do vencimento.')
        
        # Obter template de notificação
        template = self.obter_template(template_nome)
        if not template:
            self.stdout.write(
                self.style.ERROR('Template de notificação não encontrado!')
            )
            return
        
        # Inicializar serviço WhatsApp
        whatsapp_service = WhatsAppService()
        
        enviadas = 0
        erros = 0
        duplicatas = 0
        
        for contrato in contratos_vencendo:
            try:
                # Verificar se já foi enviada notificação recentemente (últimos 7 dias)
                if not force and self.ja_notificado_recentemente(contrato, dias=7):
                    duplicatas += 1
                    self.stdout.write(
                        f'⚠️  Contrato {contrato.numero} - já notificado recentemente'
                    )
                    continue
                
                # Verificar se inquilino tem email ou telefone
                tem_email = bool(contrato.inquilino.email)
                tem_telefone = bool(contrato.inquilino.telefone)
                
                if not tem_email and not tem_telefone:
                    self.stdout.write(
                        f'⚠️  Contrato {contrato.numero} - inquilino sem email nem telefone cadastrado'
                    )
                    continue
                
                if dry_run:
                    canais = []
                    if tem_email:
                        canais.append('EMAIL')
                    if tem_telefone:
                        canais.append('WHATSAPP')
                    
                    self.stdout.write(
                        f'[DRY RUN] Enviaria notificação para: {contrato.inquilino.nome} '
                        f'(Contrato {contrato.numero}, vence em {(contrato.data_fim - timezone.now().date()).days} dias) '
                        f'via {" e ".join(canais)}'
                    )
                    continue
                
                # Criar contexto para o template
                contexto = self.criar_contexto(contrato)
                
                # Renderizar template
                assunto = template.renderizar_assunto(contexto)
                corpo = template.renderizar_corpo(contexto)
                
                # Contadores para este contrato
                sucesso_email = False
                sucesso_whatsapp = False
                
                # Enviar por EMAIL se disponível
                if tem_email:
                    notificacao_email = Notificacao.objects.create(
                        template=template,
                        inquilino=contrato.inquilino,
                        contrato=contrato,
                        canal='EMAIL',
                        destinatario=contrato.inquilino.email,
                        assunto=assunto,
                        corpo=corpo,
                        prioridade='ALTA',
                        usuario_id=1  # Sistema
                    )
                    sucesso_email = self.enviar_email(notificacao_email, assunto, corpo)
                
                # Enviar por WHATSAPP se disponível
                if tem_telefone:
                    notificacao_whatsapp = Notificacao.objects.create(
                        template=template,
                        inquilino=contrato.inquilino,
                        contrato=contrato,
                        canal='WHATSAPP',
                        destinatario=contrato.inquilino.telefone,
                        assunto=assunto,
                        corpo=corpo,
                        prioridade='ALTA',
                        usuario_id=1  # Sistema
                    )
                    # Obter QR code PIX do contexto se disponível
                    qr_code_pix = contexto.get('pix', {}).get('qr_code_base64', None)
                    sucesso_whatsapp = self.enviar_whatsapp(whatsapp_service, notificacao_whatsapp, corpo, qr_code_pix)
                
                # Verificar resultado geral
                if (tem_email and sucesso_email) or (tem_telefone and sucesso_whatsapp):
                    enviadas += 1
                    dias_restantes = (contrato.data_fim - timezone.now().date()).days
                    canais_enviados = []
                    if sucesso_email:
                        canais_enviados.append('EMAIL')
                    if sucesso_whatsapp:
                        canais_enviados.append('WHATSAPP')
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Notificação enviada: {contrato.inquilino.nome} '
                            f'(Contrato {contrato.numero}, vence em {dias_restantes} dias) '
                            f'via {" e ".join(canais_enviados)}'
                        )
                    )
                else:
                    erros += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Erro ao enviar para: {contrato.inquilino.nome} '
                            f'(Contrato {contrato.numero}) - Falha em todos os canais'
                        )
                    )
                
            except Exception as e:
                erros += 1
                logger.error(f'Erro ao processar contrato {contrato.numero}: {e}')
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Erro ao processar contrato {contrato.numero}: {e}'
                    )
                )
        
        # Resumo final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMO DA EXECUÇÃO:')
        self.stdout.write(f'Contratos verificados: {contratos_vencendo.count()}')
        self.stdout.write(f'Notificações enviadas: {enviadas}')
        self.stdout.write(f'Erros: {erros}')
        self.stdout.write(f'Duplicatas evitadas: {duplicatas}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n*** MODO DRY-RUN - Nenhuma notificação foi enviada ***'))
    
    def obter_template(self, template_nome=None):
        """Obtém template de notificação para vencimento"""
        try:
            if template_nome:
                return TemplateNotificacao.objects.get(
                    nome__icontains=template_nome,
                    ativo=True
                )
            else:
                # Buscar template padrão para vencimento
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
    
    def ja_notificado_recentemente(self, contrato, dias=7):
        """Verifica se já foi enviada notificação recentemente"""
        data_limite = timezone.now() - timedelta(days=dias)
        return Notificacao.objects.filter(
            contrato=contrato,
            canal='WHATSAPP',
            template__tipo='VENCIMENTO',
            created_at__gte=data_limite,
            status__in=['ENVIADA', 'ENTREGUE']
        ).exists()
    
    def criar_contexto(self, contrato):
        """Cria contexto para renderização do template"""
        dias_restantes = (contrato.data_fim - timezone.now().date()).days
        
        # Buscar parcela pendente mais próxima do vencimento
        parcela_pendente = contrato.parcelas.filter(
            status='PENDENTE'
        ).order_by('data_vencimento').first()
        
        # Gerar link de pagamento e QR code PIX se houver parcela pendente
        link_pagamento = ''
        qr_code_pix = ''
        codigo_pix = ''
        
        if parcela_pendente:
            try:
                from pagamentos.utils import (
                    gerar_link_pagamento, 
                    gerar_codigo_pix_real, 
                    gerar_qr_code_pix
                )
                
                # Gerar link de pagamento
                link_pagamento = gerar_link_pagamento(parcela_pendente.id) or ''
                
                # Obter configuração PIX
                config_pix = ConfiguracaoPagamento.get_configuracao()
                
                # Gerar código PIX
                dados_pix = {
                    'chave': config_pix.pix_chave or 'exemplo@email.com',
                    'valor': float(parcela_pendente.valor_total),
                    'nome_recebedor': config_pix.pix_nome_recebedor or 'SISTEMA IMOBILIARIO',
                    'cidade': 'SAO PAULO',  # Campo fixo pois não existe no modelo
                    'identificador': f'PARC{parcela_pendente.id}'
                }
                
                codigo_pix = gerar_codigo_pix_real(dados_pix)
                qr_code_pix = gerar_qr_code_pix(codigo_pix) if codigo_pix else ''
                
            except ImportError:
                logger.warning('Módulo de pagamentos não disponível')
            except Exception as e:
                logger.error(f'Erro ao gerar dados de pagamento PIX: {e}')
        
        contexto = {
            # Variáveis diretas para compatibilidade com template
            'inquilino_nome': contrato.inquilino.nome,
            'imovel_endereco': getattr(contrato.imovel, 'endereco_completo', 'N/A'),
            'valor_aluguel': contrato.valor_aluguel,
            'data_vencimento': parcela_pendente.data_vencimento.strftime('%d/%m/%Y') if parcela_pendente else contrato.data_fim.strftime('%d/%m/%Y'),
            'dias_restantes': dias_restantes,
            'link_pagamento': link_pagamento,
            'empresa_nome': getattr(settings, 'SISTEMA_NOME', 'Sistema Imobiliário'),
            
            # Estruturas aninhadas para compatibilidade com outros templates
            'inquilino': {
                'nome': contrato.inquilino.nome,
                'telefone': contrato.inquilino.telefone,
                'email': contrato.inquilino.email,
            },
            'contrato': {
                'numero': contrato.numero,
                'valor_aluguel': contrato.valor_aluguel,
                'data_inicio': contrato.data_inicio.strftime('%d/%m/%Y'),
                'data_fim': contrato.data_fim.strftime('%d/%m/%Y'),
                'data_vencimento_contrato': contrato.data_fim.strftime('%d/%m/%Y'),
                'dias_para_vencer': dias_restantes,
            },
            'imovel': {
                'endereco': getattr(contrato.imovel, 'endereco_completo', 'N/A'),
                'codigo': getattr(contrato.imovel, 'codigo', 'N/A'),
            },
            'parcela': {
                'valor': parcela_pendente.valor_total if parcela_pendente else contrato.valor_aluguel,
                'data_vencimento': parcela_pendente.data_vencimento.strftime('%d/%m/%Y') if parcela_pendente else '',
                'tipo': parcela_pendente.get_tipo_display() if parcela_pendente else 'Aluguel',
            },
            'pix': {
                'codigo_pix': codigo_pix,
                'qr_code_base64': qr_code_pix,
                'disponivel': bool(codigo_pix and qr_code_pix)
            },
            'data_atual': timezone.now().strftime('%d/%m/%Y'),
            'sistema': {
                'nome': getattr(settings, 'SISTEMA_NOME', 'Sistema Imobiliário'),
                'telefone': getattr(settings, 'EMPRESA_TELEFONE', ''),
                'email': getattr(settings, 'EMPRESA_EMAIL', ''),
            }
        }
        
        return contexto
    
    def enviar_email(self, notificacao, assunto, mensagem):
        """Envia mensagem via Email"""
        try:
            notificacao.status = 'ENVIANDO'
            notificacao.save()
            
            # Enviar email
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notificacao.destinatario],
                fail_silently=False
            )
            
            notificacao.status = 'ENVIADA'
            notificacao.data_envio = timezone.now()
            notificacao.save()
            return True
            
        except Exception as e:
            logger.error(f'Erro ao enviar email para {notificacao.destinatario}: {e}')
            notificacao.status = 'ERRO'
            notificacao.erro_envio = str(e)
            notificacao.tentativas_realizadas += 1
            notificacao.save()
            return False
    
    def enviar_whatsapp(self, whatsapp_service, notificacao, mensagem, qr_code_pix=None):
        """Envia mensagem via WhatsApp com QR code PIX opcional"""
        try:
            notificacao.status = 'ENVIANDO'
            notificacao.save()
            
            # Salvar QR Code nos anexos se disponível
            if qr_code_pix:
                notificacao.anexos = [{
                    'tipo': 'qr_code_pix',
                    'nome': 'qr_code_pix.png',
                    'data': qr_code_pix,
                    'media_type': 'image/png'
                }]
            
            # Enviar mensagem com QR code se disponível
            resultado = whatsapp_service.send_message(
                to_number=notificacao.destinatario,
                message=mensagem,
                media_base64=qr_code_pix if qr_code_pix else None,
                media_type='image'
            )
            
            if resultado.get('success', False):
                notificacao.status = 'ENVIADA'
                notificacao.data_envio = timezone.now()
                notificacao.tracking_id = resultado.get('message_id')
            else:
                notificacao.status = 'ERRO'
                notificacao.erro_envio = resultado.get('error', 'Erro desconhecido')
            
            notificacao.save()
            return resultado.get('success', False)
            
        except Exception as e:
            logger.error(f'Erro ao enviar WhatsApp para {notificacao.destinatario}: {e}')
            notificacao.status = 'ERRO'
            notificacao.erro_envio = str(e)
            notificacao.tentativas_realizadas += 1
            notificacao.save()
            return False