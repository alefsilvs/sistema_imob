from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import json
import logging
import hashlib
import hmac

from .models import PagamentoOnline, LogPagamento, ConfiguracaoPagamento
from financeiro.models import Parcela
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def validar_numero_cartao(numero):
    """Valida número do cartão usando algoritmo de Luhn"""
    numero = re.sub(r'\D', '', numero)
    if len(numero) < 13 or len(numero) > 19:
        return False
    
    # Algoritmo de Luhn
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10
    
    return luhn_checksum(numero) == 0

def validar_validade_cartao(validade):
    """Valida data de validade do cartão"""
    try:
        if not re.match(r'^\d{2}/\d{2}$', validade):
            return False
        
        mes, ano = validade.split('/')
        mes = int(mes)
        ano = int('20' + ano)
        
        if mes < 1 or mes > 12:
            return False
        
        # Verificar se não está expirado
        hoje = datetime.now()
        if ano < hoje.year or (ano == hoje.year and mes < hoje.month):
            return False
        
        return True
    except:
        return False

def detectar_bandeira(numero):
    """Detecta a bandeira do cartão"""
    numero = re.sub(r'\D', '', numero)
    
    if numero.startswith('4'):
        return 'Visa'
    elif numero.startswith(('51', '52', '53', '54', '55')):
        return 'Mastercard'
    elif numero.startswith(('34', '37')):
        return 'American Express'
    elif numero.startswith('6011') or numero.startswith('65'):
        return 'Discover'
    elif numero.startswith(('4011', '4312', '4389', '4514', '4573')):
        return 'Elo'
    else:
        return 'Desconhecida'

class PagamentoView(TemplateView):
    """View para exibir a página de pagamento"""
    template_name = 'pagamentos/pagamento.html'

class PagamentoProfissionalView(TemplateView):
    """View profissional para pagamentos com melhor UX"""
    template_name = 'pagamentos/pagamento_profissional.html'
    
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')
        
        try:
            pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
            
            # Verificar se o pagamento ainda é válido
            if pagamento.esta_expirado:
                pagamento.expirar()
                context['erro'] = 'Este link de pagamento expirou.'
                return context
            
            if pagamento.status != 'PENDENTE':
                context['erro'] = f'Este pagamento já foi {pagamento.get_status_display().lower()}.'
                return context
            
            # Buscar configurações
            config = ConfiguracaoPagamento.get_configuracao()
            
            context.update({
                'pagamento': pagamento,
                'parcela': pagamento.parcela,
                'contrato': pagamento.parcela.contrato,
                'inquilino': pagamento.parcela.contrato.inquilino,
                'imovel': pagamento.parcela.contrato.imovel,
                'config': config,
                'metodos_disponiveis': self.get_metodos_disponiveis(config),
            })
            
            # Log de acesso
            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='TENTATIVA',
                descricao='Página de pagamento profissional acessada',
                ip_origem=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
        except Exception as e:
            logger.error(f"Erro ao carregar pagamento {token}: {str(e)}")
            context['erro'] = 'Pagamento não encontrado ou inválido.'
        
        return context
    
    def get_metodos_disponiveis(self, config):
        """Retorna os métodos de pagamento disponíveis"""
        metodos = []
        
        if config.pix_habilitado and config.pix_chave:
            metodos.append({
                'codigo': 'PIX',
                'nome': 'PIX',
                'icone': 'fab fa-pix',
                'descricao': 'Pagamento instantâneo',
                'detalhes': 'Aprovação imediata'
            })
        
        if config.cartao_habilitado and config.gateway_api_key:
            metodos.append({
                'codigo': 'CARTAO_CREDITO',
                'nome': 'Cartão de Crédito',
                'icone': 'fas fa-credit-card',
                'descricao': 'Parcelamento disponível',
                'detalhes': 'Até 12x sem juros'
            })
        
        if config.boleto_habilitado:
            metodos.append({
                'codigo': 'BOLETO',
                'nome': 'Boleto Bancário',
                'icone': 'fas fa-barcode',
                'descricao': 'Pague em qualquer banco',
                'detalhes': 'Aprovação em 1-2 dias úteis'
            })
        
        return metodos
    
    def get_client_ip(self):
         """Obtém o IP do cliente"""
         x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
         if x_forwarded_for:
             ip = x_forwarded_for.split(',')[0]
         else:
             ip = self.request.META.get('REMOTE_ADDR')
         return ip


class SucessoProfissionalView(TemplateView):
    """View para página de sucesso do pagamento"""
    template_name = 'pagamentos/sucesso_profissional.html'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            self.pagamento = PagamentoOnline.objects.get(
                token_pagamento=kwargs['token'],
                status='APROVADO'
            )
        except PagamentoOnline.DoesNotExist:
            messages.error(request, 'Pagamento não encontrado ou não aprovado.')
            return redirect('core:dashboard')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'pagamento': self.pagamento,
            'parcela': self.pagamento.parcela,
            'contrato': self.pagamento.parcela.contrato,
            'inquilino': self.pagamento.parcela.contrato.inquilino,
            'imovel': self.pagamento.parcela.contrato.imovel,
            'valor_formatado': f"R$ {self.pagamento.valor_pago:.2f}".replace('.', ','),
        })
        
        # Log de acesso à página de sucesso
        LogPagamento.objects.create(
            pagamento=self.pagamento,
            tipo='SUCESSO',
            descricao='Página de sucesso acessada',
            ip_origem=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return context
    
    def get_client_ip(self):
        """Obtém o IP do cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def get_metodos_disponiveis(self, config):
        """Retorna os métodos de pagamento disponíveis"""
        metodos = []
        
        if config.pix_habilitado and config.pix_chave:
            metodos.append({
                'codigo': 'PIX',
                'nome': 'PIX',
                'icone': 'fas fa-qrcode',
                'descricao': 'Pagamento instantâneo'
            })
        
        if config.cartao_habilitado and config.gateway_api_key:
            metodos.extend([
                {
                    'codigo': 'CARTAO_CREDITO',
                    'nome': 'Cartão de Crédito',
                    'icone': 'fas fa-credit-card',
                    'descricao': 'Visa, Mastercard, Elo'
                },
                {
                    'codigo': 'CARTAO_DEBITO',
                    'nome': 'Cartão de Débito',
                    'icone': 'fas fa-credit-card',
                    'descricao': 'Débito online'
                }
            ])
        
        if config.boleto_habilitado:
            metodos.append({
                'codigo': 'BOLETO',
                'nome': 'Boleto Bancário',
                'icone': 'fas fa-barcode',
                'descricao': 'Vencimento em 3 dias úteis'
            })
        
        return metodos
    
    def get_client_ip(self):
        """Obtém o IP do cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

@require_http_methods(["POST"])
@csrf_exempt
def processar_pagamento(request, token):
    """Processa o pagamento baseado no método escolhido"""
    try:
        pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
        
        # Verificações de segurança
        if not pagamento.pode_processar:
            return JsonResponse({
                'success': False,
                'error': 'Pagamento não pode ser processado'
            }, status=400)
        
        # Obter dados do POST
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        metodo = data.get('metodo_pagamento')
        
        if not metodo:
            return JsonResponse({
                'success': False,
                'error': 'Método de pagamento não informado'
            }, status=400)
        
        # Atualizar dados do pagamento
        pagamento.metodo_pagamento = metodo
        pagamento.nome_pagador = data.get('nome_pagador', '')
        pagamento.email_pagador = data.get('email_pagador', '')
        pagamento.telefone_pagador = data.get('telefone_pagador', '')
        pagamento.ip_origem = get_client_ip(request)
        pagamento.user_agent = request.META.get('HTTP_USER_AGENT', '')
        pagamento.tentativas_processamento += 1
        pagamento.save()
        
        # Log da tentativa
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='TENTATIVA',
            descricao=f'Tentativa de pagamento via {metodo}',
            dados_extras={
                'metodo': metodo,
                'nome_pagador': pagamento.nome_pagador,
                'email_pagador': pagamento.email_pagador
            },
            ip_origem=pagamento.ip_origem,
            user_agent=pagamento.user_agent
        )
        
        # Processar baseado no método
        if metodo == 'PIX':
            return processar_pix(pagamento, data)
        elif metodo in ['CARTAO_CREDITO', 'CARTAO_DEBITO']:
            return processar_cartao(pagamento, data)
        elif metodo == 'BOLETO':
            return processar_boleto(pagamento, data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Método de pagamento não suportado'
            }, status=400)
    
    except Exception as e:
        logger.error(f"Erro ao processar pagamento {token}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

def processar_pix(pagamento, data):
    """Processa pagamento via PIX"""
    try:
        from .utils import gerar_codigo_pix_real, gerar_qr_code_pix, gerar_link_pagamento, gerar_qr_code_link_pagamento
        
        config = ConfiguracaoPagamento.get_configuracao()
        
        # Dados para geração do PIX
        pix_data = {
            'chave': config.pix_chave,
            'valor': float(pagamento.valor_original),
            'nome_recebedor': config.pix_nome_recebedor,
            'cidade': 'SAO PAULO',
            'identificador': pagamento.token_pagamento[:25]
        }
        
        # Gerar código PIX real
        codigo_pix = gerar_codigo_pix_real(pix_data)
        
        # Gerar QR code do código PIX
        qr_code_pix = gerar_qr_code_pix(codigo_pix)
        
        # Gerar link de pagamento
        link_pagamento = gerar_link_pagamento(pagamento.parcela.id)
        
        # Gerar QR code do link de pagamento
        qr_code_link = gerar_qr_code_link_pagamento(link_pagamento) if link_pagamento else None
        
        # Atualizar status
        pagamento.status = 'PROCESSANDO'
        pagamento.gateway_response = {
            'tipo': 'PIX',
            'codigo_pix': codigo_pix,
            'qr_code_pix': qr_code_pix,
            'qr_code_link': qr_code_link,
            'link_pagamento': link_pagamento,
            'pix_data': pix_data
        }
        pagamento.save()
        
        # Para demonstração: simular aprovação automática após 10 segundos
        if pagamento.metadata and pagamento.metadata.get('tipo') == 'assinatura_plano':
            import threading
            import time
            
            def simular_aprovacao_pix():
                time.sleep(10)  # Aguardar 10 segundos
                try:
                    pagamento_atual = PagamentoOnline.objects.get(id=pagamento.id)
                    if pagamento_atual.status == 'PROCESSANDO':
                        pagamento_atual.marcar_como_pago(
                            valor_pago=pagamento_atual.valor_original,
                            transaction_id=f'PIX_{timezone.now().strftime("%Y%m%d%H%M%S")}',
                            gateway_response={
                                'status': 'APROVADO',
                                'metodo': 'PIX',
                                'simulacao': True
                            }
                        )
                        # Ativar plano automaticamente
                        ativar_plano_automaticamente(pagamento_atual)
                        logger.info(f'PIX simulado aprovado para pagamento {pagamento_atual.id}')
                except Exception as e:
                    logger.error(f'Erro na simulação PIX: {str(e)}')
            
            # Executar simulação em thread separada
            thread = threading.Thread(target=simular_aprovacao_pix)
            thread.daemon = True
            thread.start()
        
        return JsonResponse({
            'success': True,
            'tipo': 'PIX',
            'codigo_pix': codigo_pix,
            'valor': float(pagamento.valor_original),
            'redirect_url': reverse('pagamentos:aguardar_confirmacao', kwargs={'token': pagamento.token_pagamento})
        })
    
    except Exception as e:
        logger.error(f"Erro ao processar PIX: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar PIX'
        }, status=500)

def processar_cartao(pagamento, data):
    """Processa pagamento via cartão com suporte a parcelamento"""
    try:
        # Validar dados do cartão
        numero_cartao = data.get('numero_cartao', '').replace(' ', '')
        nome_titular = data.get('nome_titular', '')
        validade = data.get('validade', '')
        cvv = data.get('cvv', '')
        parcelas = int(data.get('parcelas', 1))
        
        if not all([numero_cartao, nome_titular, validade, cvv]):
            return JsonResponse({
                'success': False,
                'error': 'Dados do cartão incompletos'
            }, status=400)
        
        # Validar número de parcelas
        if parcelas < 1 or parcelas > 12:
            return JsonResponse({
                'success': False,
                'error': 'Número de parcelas inválido'
            }, status=400)
        
        # Validar formato do cartão
        if not validar_numero_cartao(numero_cartao):
            return JsonResponse({
                'success': False,
                'error': 'Número do cartão inválido'
            }, status=400)
        
        # Validar validade
        if not validar_validade_cartao(validade):
            return JsonResponse({
                'success': False,
                'error': 'Data de validade inválida'
            }, status=400)
        
        # Simular processamento do cartão
        # Em produção, aqui seria feita a integração com o gateway de pagamento
        transaction_id = f"TXN_{pagamento.token_pagamento[:10]}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calcular valor da parcela
        valor_parcela = float(pagamento.valor_original) / parcelas
        
        # Simular aprovação (90% de chance de aprovação)
        import random
        aprovado = random.random() > 0.1
        
        if aprovado:
            pagamento.marcar_como_pago(
                transaction_id=transaction_id,
                gateway_response={
                    'tipo': 'CARTAO_CREDITO',
                    'transaction_id': transaction_id,
                    'bandeira': detectar_bandeira(numero_cartao),
                    'ultimos_digitos': numero_cartao[-4:],
                    'parcelas': parcelas,
                    'valor_parcela': valor_parcela,
                    'nome_titular': nome_titular
                }
            )
            
            # Ativar plano automaticamente se for assinatura
            if hasattr(pagamento, 'metadata') and pagamento.metadata and pagamento.metadata.get('tipo') == 'assinatura_plano':
                ativar_plano_automaticamente(pagamento)
            
            return JsonResponse({
                'success': True,
                'tipo': 'CARTAO_CREDITO',
                'transaction_id': transaction_id,
                'parcelas': parcelas,
                'valor_parcela': f'{valor_parcela:.2f}',
                'redirect_url': reverse('pagamentos:sucesso_profissional', kwargs={'token': pagamento.token_pagamento})
            })
        else:
            pagamento.status = 'REJEITADO'
            pagamento.ultimo_erro = 'Transação rejeitada pelo banco'
            pagamento.save()
            
            return JsonResponse({
                'success': False,
                'error': 'Transação rejeitada pelo banco. Verifique os dados do cartão e tente novamente.'
            }, status=400)
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos fornecidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao processar cartão: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar cartão. Tente novamente.'
        }, status=500)

def processar_boleto(pagamento, data):
    """Processa pagamento via boleto"""
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        
        # Gerar dados do boleto
        vencimento = timezone.now().date() + timezone.timedelta(days=3)
        linha_digitavel = gerar_linha_digitavel(pagamento)
        
        pagamento.status = 'PROCESSANDO'
        pagamento.gateway_response = {
            'tipo': 'BOLETO',
            'linha_digitavel': linha_digitavel,
            'vencimento': vencimento.isoformat(),
            'banco': config.banco_codigo
        }
        pagamento.save()
        
        return JsonResponse({
            'success': True,
            'tipo': 'BOLETO',
            'linha_digitavel': linha_digitavel,
            'vencimento': vencimento.strftime('%d/%m/%Y'),
            'redirect_url': reverse('pagamentos:boleto', kwargs={'token': pagamento.token_pagamento})
        })
    
    except Exception as e:
        logger.error(f"Erro ao processar boleto: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Erro ao gerar boleto'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_confirmacao(request):
    """Webhook para receber confirmações de pagamento"""
    try:
        # Verificar assinatura do webhook (se configurada)
        signature = request.META.get('HTTP_X_SIGNATURE')
        if signature:
            if not verificar_assinatura_webhook(request.body, signature):
                return HttpResponse('Unauthorized', status=401)

        data = json.loads(request.body or b"{}")

        asaas_token = request.META.get("HTTP_ASAAS_ACCESS_TOKEN") or request.META.get("HTTP_ASAAS-ACCESS-TOKEN")
        is_asaas_payload = bool(asaas_token) or ("event" in data and "payment" in data)

        if is_asaas_payload:
            config = ConfiguracaoPagamento.get_configuracao()
            expected_token = (config.gateway_secret_key or "").strip()
            if expected_token and (asaas_token or "").strip() != expected_token:
                return HttpResponse("Unauthorized", status=401)

            event = (data.get("event") or "").strip().upper()
            payment = data.get("payment") or {}
            payment_status = (payment.get("status") or "").strip().upper()

            token = payment.get("externalReference") or data.get("externalReference")
            if token:
                token = str(token)
            if not token:
                return HttpResponse("externalReference não informado", status=400)

            transaction_id = payment.get("id")
            valor_pago = payment.get("value") or payment.get("netValue")

            pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)

            paid_events = {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED", "PAYMENT_APPROVED"}
            paid_statuses = {"RECEIVED", "CONFIRMED"}

            if (event in paid_events or payment_status in paid_statuses) and pagamento.status != "APROVADO":
                pagamento.marcar_como_pago(
                    valor_pago=valor_pago,
                    transaction_id=str(transaction_id) if transaction_id else None,
                    gateway_response=data,
                )

                if pagamento.metadata and pagamento.metadata.get("tipo") == "assinatura_plano":
                    ativar_plano_automaticamente(pagamento)

                LogPagamento.objects.create(
                    pagamento=pagamento,
                    tipo="APROVACAO",
                    descricao="Pagamento confirmado via webhook (Asaas)",
                    dados_extras=data,
                )

            return HttpResponse("OK", status=200)

        token = data.get('token_pagamento')
        status = data.get('status')
        transaction_id = data.get('transaction_id')
        valor_pago = data.get('valor_pago')

        if not token:
            return HttpResponse('Token não informado', status=400)

        pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)

        if status == 'APROVADO':
            pagamento.marcar_como_pago(
                valor_pago=valor_pago,
                transaction_id=transaction_id,
                gateway_response=data
            )

            # Ativar plano automaticamente se for pagamento de assinatura
            if pagamento.metadata and pagamento.metadata.get('tipo') == 'assinatura_plano':
                ativar_plano_automaticamente(pagamento)

            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='APROVACAO',
                descricao='Pagamento confirmado via webhook',
                dados_extras=data
            )

        elif status == 'REJEITADO':
            pagamento.status = 'REJEITADO'
            pagamento.ultimo_erro = data.get('motivo_rejeicao', 'Rejeitado pelo gateway')
            pagamento.save()

            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='REJEICAO',
                descricao='Pagamento rejeitado via webhook',
                dados_extras=data
            )

        return HttpResponse('OK', status=200)
    
    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return HttpResponse('Erro interno', status=500)

def sucesso(request, token):
    """Página de sucesso do pagamento"""
    pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
    
    if pagamento.status != 'APROVADO':
        return redirect('pagamentos:pagamento', token=token)
    
    return render(request, 'pagamentos/sucesso.html', {
        'pagamento': pagamento,
        'parcela': pagamento.parcela
    })

def aguardar_confirmacao(request, token):
    """Página de aguardo de confirmação (PIX)"""
    pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
    
    return render(request, 'pagamentos/aguardar.html', {
        'pagamento': pagamento,
        'codigo_pix': pagamento.gateway_response.get('codigo_pix') if pagamento.gateway_response else None
    })

def boleto(request, token):
    """Página do boleto"""
    pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
    
    return render(request, 'pagamentos/boleto.html', {
        'pagamento': pagamento,
        'boleto_data': pagamento.gateway_response if pagamento.gateway_response else None
    })

def status_pagamento(request, token):
    """API para verificar status do pagamento"""
    try:
        pagamento = get_object_or_404(PagamentoOnline, token_pagamento=token)
        
        return JsonResponse({
            'status': pagamento.status,
            'status_display': pagamento.get_status_display(),
            'data_pagamento': pagamento.data_pagamento.isoformat() if pagamento.data_pagamento else None,
            'valor_pago': float(pagamento.valor_pago) if pagamento.valor_pago else None,
            'metodo': pagamento.get_metodo_pagamento_display() if pagamento.metodo_pagamento else None
        })
    
    except Exception as e:
        return JsonResponse({
            'error': 'Pagamento não encontrado'
        }, status=404)

# Funções auxiliares

def get_client_ip(request):
    """Obtém o IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def gerar_codigo_pix(data):
    """Gera código PIX simulado"""
    # Em produção, usar biblioteca específica para PIX
    import base64
    pix_string = f"{data['chave']}|{data['valor']}|{data['identificador']}"
    return base64.b64encode(pix_string.encode()).decode()[:50]

def detectar_bandeira(numero_cartao):
    """Detecta a bandeira do cartão"""
    numero = numero_cartao.replace(' ', '')
    if numero.startswith('4'):
        return 'Visa'
    elif numero.startswith('5') or numero.startswith('2'):
        return 'Mastercard'
    elif numero.startswith('6'):
        return 'Elo'
    else:
        return 'Desconhecida'

def gerar_linha_digitavel(pagamento):
    """Gera linha digitável do boleto simulada"""
    # Em produção, usar biblioteca específica para boletos
    import random
    return f"{random.randint(10000, 99999)}.{random.randint(10000, 99999)} {random.randint(10000, 99999)}.{random.randint(100000, 999999)} {random.randint(10000, 99999)}.{random.randint(100000, 999999)} {random.randint(1, 9)} {random.randint(10000000000000, 99999999999999)}"

def verificar_assinatura_webhook(payload, signature):
    """Verifica a assinatura do webhook"""
    # Em produção, implementar verificação real baseada no gateway usado
    return True

def ativar_plano_automaticamente(pagamento):
    """Ativa o plano automaticamente após confirmação de pagamento"""
    try:
        from saas.models import PlanoComercial, Tenant
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta
        
        # Obter dados do pagamento
        plano_id = pagamento.metadata.get('plano_id')
        user_id = pagamento.metadata.get('user_id')
        
        if not plano_id or not user_id:
            logger.error(f'Dados insuficientes para ativar plano: plano_id={plano_id}, user_id={user_id}')
            return False
        
        # Verificar se plano e usuário existem
        try:
            plano = PlanoComercial.objects.get(id=plano_id)
            user = User.objects.get(id=user_id)
        except (PlanoComercial.DoesNotExist, User.DoesNotExist) as e:
            logger.error(f'Plano ou usuário não encontrado: {str(e)}')
            return False
        
        # Verificar se já existe tenant para o usuário
        tenant_existente = Tenant.objects.filter(usuario_admin=user).first()
        
        if tenant_existente:
            # Atualizar tenant existente (pode estar com status 'pendente_pagamento')
            tenant_existente.plano_comercial = plano
            tenant_existente.status = 'ativo'
            tenant_existente.data_ativacao = timezone.now()
            tenant_existente.data_vencimento = timezone.now() + timedelta(days=30)
            tenant_existente.save()
            
            logger.info(f'Tenant {tenant_existente.id} ativado com plano {plano.nome} - Status alterado para ativo')
            
        else:
            # Criar novo tenant
            from django.utils.text import slugify
            
            # Gerar slug único
            base_slug = slugify(user.get_full_name() or user.username)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Gerar subdomínio único
            base_subdomain = slug
            subdomain = base_subdomain
            counter = 1
            while Tenant.objects.filter(subdominio=subdomain).exists():
                subdomain = f"{base_subdomain}{counter}"
                counter += 1
            
            tenant = Tenant.objects.create(
                nome_empresa=user.get_full_name() or user.username,
                slug=slug,
                subdominio=subdomain,
                usuario_admin=user,
                plano_comercial=plano,
                status='ativo',
                data_ativacao=timezone.now(),
                data_vencimento=timezone.now() + timedelta(days=30)
            )
            
            logger.info(f'Novo tenant {tenant.id} criado com plano {plano.nome}')
        
        # Registrar log de ativação
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='ATIVACAO_PLANO',
            descricao=f'Plano {plano.nome} ativado automaticamente',
            dados_extras={
                'plano_id': plano.id,
                'plano_nome': plano.nome,
                'user_id': user.id,
                'tenant_id': tenant_existente.id if tenant_existente else tenant.id
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f'Erro ao ativar plano automaticamente: {str(e)}')
        return False

# ===== VIEWS ESPECÍFICAS PARA RELATÓRIOS DE PAGAMENTOS DE INQUILINOS =====

def relatorio_pagamentos_inquilinos(request):
    """
    Relatório específico para pagamentos de inquilinos
    """
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('core:dashboard')
    
    # Filtros
    status_filtro = request.GET.get('status', '')
    metodo_filtro = request.GET.get('metodo', '')
    categoria_filtro = request.GET.get('categoria', 'INQUILINO')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Filtrar apenas pagamentos de inquilinos
    pagamentos = PagamentoOnline.objects.filter(
        categoria_pagamento='INQUILINO'
    ).order_by('-data_criacao')
    
    if status_filtro:
        pagamentos = pagamentos.filter(status=status_filtro)
    
    if metodo_filtro:
        pagamentos = pagamentos.filter(metodo_pagamento=metodo_filtro)
    
    if data_inicio:
        pagamentos = pagamentos.filter(data_criacao__date__gte=data_inicio)
    
    if data_fim:
        pagamentos = pagamentos.filter(data_criacao__date__lte=data_fim)
    
    # Estatísticas específicas para inquilinos
    total_pagamentos = pagamentos.count()
    total_aprovados = pagamentos.filter(status='APROVADO').count()
    total_pendentes = pagamentos.filter(status='PENDENTE').count()
    total_rejeitados = pagamentos.filter(status='REJEITADO').count()
    valor_total_aprovado = sum(p.valor_pago or 0 for p in pagamentos.filter(status='APROVADO'))
    valor_total_pendente = sum(p.valor_total or 0 for p in pagamentos.filter(status='PENDENTE'))
    
    # Estatísticas por método de pagamento
    stats_metodo = {}
    for metodo, nome in PagamentoOnline.METODO_CHOICES:
        count = pagamentos.filter(metodo_pagamento=metodo).count()
        valor = sum(p.valor_pago or 0 for p in pagamentos.filter(metodo_pagamento=metodo, status='APROVADO'))
        stats_metodo[metodo] = {'count': count, 'valor': valor, 'nome': nome}
    
    context = {
        'pagamentos': pagamentos[:100],  # Limitar a 100 registros
        'total_pagamentos': total_pagamentos,
        'total_aprovados': total_aprovados,
        'total_pendentes': total_pendentes,
        'total_rejeitados': total_rejeitados,
        'valor_total_aprovado': valor_total_aprovado,
        'valor_total_pendente': valor_total_pendente,
        'stats_metodo': stats_metodo,
        'status_choices': PagamentoOnline.STATUS_CHOICES,
        'metodo_choices': PagamentoOnline.METODO_CHOICES,
        'categoria_choices': PagamentoOnline.CATEGORIA_CHOICES,
        'filtros': {
            'status': status_filtro,
            'metodo': metodo_filtro,
            'categoria': categoria_filtro,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        },
        'tipo_relatorio': 'Pagamentos de Inquilinos'
    }
    
    return render(request, 'pagamentos/relatorio_inquilinos.html', context)

def relatorio_pagamentos_outros(request):
    """
    Relatório específico para outros tipos de pagamentos (não inquilinos nem assinaturas)
    """
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('core:dashboard')
    
    # Filtros
    status_filtro = request.GET.get('status', '')
    metodo_filtro = request.GET.get('metodo', '')
    categoria_filtro = request.GET.get('categoria', 'OUTROS')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Filtrar pagamentos que não são de inquilinos nem assinaturas
    pagamentos = PagamentoOnline.objects.filter(
        categoria_pagamento='OUTROS'
    ).order_by('-data_criacao')
    
    if status_filtro:
        pagamentos = pagamentos.filter(status=status_filtro)
    
    if metodo_filtro:
        pagamentos = pagamentos.filter(metodo_pagamento=metodo_filtro)
    
    if data_inicio:
        pagamentos = pagamentos.filter(data_criacao__date__gte=data_inicio)
    
    if data_fim:
        pagamentos = pagamentos.filter(data_criacao__date__lte=data_fim)
    
    # Estatísticas
    total_pagamentos = pagamentos.count()
    total_aprovados = pagamentos.filter(status='APROVADO').count()
    total_pendentes = pagamentos.filter(status='PENDENTE').count()
    valor_total = sum(p.valor_pago or 0 for p in pagamentos.filter(status='APROVADO'))
    
    context = {
        'pagamentos': pagamentos[:100],  # Limitar a 100 registros
        'total_pagamentos': total_pagamentos,
        'total_aprovados': total_aprovados,
        'total_pendentes': total_pendentes,
        'valor_total': valor_total,
        'status_choices': PagamentoOnline.STATUS_CHOICES,
        'metodo_choices': PagamentoOnline.METODO_CHOICES,
        'categoria_choices': PagamentoOnline.CATEGORIA_CHOICES,
        'filtros': {
            'status': status_filtro,
            'metodo': metodo_filtro,
            'categoria': categoria_filtro,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        },
        'tipo_relatorio': 'Outros Pagamentos'
    }
    
    return render(request, 'pagamentos/relatorio_outros.html', context)

def dashboard_pagamentos_separados(request):
    """
    Dashboard com visão separada dos tipos de pagamento
    """
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('core:dashboard')
    
    # Estatísticas de pagamentos de inquilinos
    pagamentos_inquilinos = PagamentoOnline.objects.filter(categoria_pagamento='INQUILINO')
    stats_inquilinos = {
        'total': pagamentos_inquilinos.count(),
        'aprovados': pagamentos_inquilinos.filter(status='APROVADO').count(),
        'pendentes': pagamentos_inquilinos.filter(status='PENDENTE').count(),
        'valor_total': sum(p.valor_pago or 0 for p in pagamentos_inquilinos.filter(status='APROVADO'))
    }
    
    # Estatísticas de outros pagamentos
    pagamentos_outros = PagamentoOnline.objects.filter(categoria_pagamento='OUTROS')
    stats_outros = {
        'total': pagamentos_outros.count(),
        'aprovados': pagamentos_outros.filter(status='APROVADO').count(),
        'pendentes': pagamentos_outros.filter(status='PENDENTE').count(),
        'valor_total': sum(p.valor_pago or 0 for p in pagamentos_outros.filter(status='APROVADO'))
    }
    
    # Importar estatísticas de assinaturas
    try:
        from assinaturas.models import PagamentoAssinatura
        pagamentos_assinaturas = PagamentoAssinatura.objects.all()
        stats_assinaturas = {
            'total': pagamentos_assinaturas.count(),
            'aprovados': pagamentos_assinaturas.filter(status='APROVADO').count(),
            'pendentes': pagamentos_assinaturas.filter(status='PENDENTE').count(),
            'valor_total': sum(p.valor_pago or 0 for p in pagamentos_assinaturas.filter(status='APROVADO'))
        }
    except ImportError:
        stats_assinaturas = {
            'total': 0,
            'aprovados': 0,
            'pendentes': 0,
            'valor_total': 0
        }
    
    context = {
        'stats_inquilinos': stats_inquilinos,
        'stats_assinaturas': stats_assinaturas,
        'stats_outros': stats_outros,
    }
    
    return render(request, 'pagamentos/dashboard_separado.html', context)


class PagamentoAssinaturaView(TemplateView):
    """View para pagamento de assinatura após configuração inicial"""
    template_name = 'pagamentos/pagamento_assinatura.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar se usuário está autenticado
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obter tenant da sessão ou do usuário logado
        tenant_id = self.request.session.get('tenant_id')
        tenant = None
        
        if tenant_id:
            try:
                from saas.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                tenant = None
        
        # Se não encontrou tenant na sessão, tentar pelo usuário logado
        if not tenant and self.request.user.is_authenticated:
            try:
                from saas.models import Tenant
                tenant = Tenant.objects.get(usuario_admin=self.request.user)
                # Atualizar sessão com o tenant correto
                self.request.session['tenant_id'] = tenant.id
            except Tenant.DoesNotExist:
                pass
        
        if not tenant:
            context['erro'] = 'Nenhum plano encontrado. Configure seu plano primeiro.'
            return context
            
        try:
            
            # Buscar configurações de pagamento
            config = ConfiguracaoPagamento.get_configuracao()
            
            context.update({
                'tenant': tenant,
                'plano': tenant.plano,
                'valor_mensal': tenant.plano.preco_mensal,
                'valor_anual': tenant.plano.preco_anual or (tenant.plano.preco_mensal * 12),
                'config': config,
                'pix_habilitado': config.pix_habilitado if config else False,
                'cartao_habilitado': config.cartao_habilitado if config else False,
                'boleto_habilitado': config.boleto_habilitado if config else False,
            })
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do tenant: {e}")
            context['erro'] = 'Erro ao carregar informações. Tente novamente.'
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Processar escolha do método de pagamento"""
        # Obter tenant da sessão ou do usuário logado
        tenant_id = request.session.get('tenant_id')
        tenant = None
        
        if tenant_id:
            try:
                from saas.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                tenant = None
        
        # Se não encontrou tenant na sessão, tentar pelo usuário logado
        if not tenant and request.user.is_authenticated:
            try:
                from saas.models import Tenant
                tenant = Tenant.objects.get(usuario_admin=request.user)
                # Atualizar sessão com o tenant correto
                request.session['tenant_id'] = tenant.id
            except Tenant.DoesNotExist:
                pass
        
        if not tenant:
            messages.error(request, 'Sessão expirada. Faça login novamente.')
            return redirect('saas:registro')
            
        try:
            from assinaturas.models import PagamentoAssinatura
            metodo_pagamento = request.POST.get('metodo_pagamento')
            periodicidade = request.POST.get('periodicidade', 'mensal')
            
            # Calcular valor baseado na periodicidade
            if periodicidade == 'anual':
                valor = tenant.plano.preco_anual or (tenant.plano.preco_mensal * 12)
            else:
                valor = tenant.plano.preco_mensal
            
            # Criar registro de pagamento de assinatura
            pagamento_assinatura = PagamentoAssinatura.objects.create(
                tenant=tenant,
                plano=tenant.plano,
                valor=valor,
                metodo_pagamento=metodo_pagamento,
                periodicidade=periodicidade,
                status='PENDENTE'
            )
            
            # Redirecionar baseado no método escolhido
            if metodo_pagamento == 'PIX':
                # Gerar PIX e redirecionar para página de PIX
                return redirect('pagamentos:processar_pix_assinatura', pagamento_id=pagamento_assinatura.id)
            elif metodo_pagamento == 'CARTAO':
                # Redirecionar para formulário de cartão
                return redirect('pagamentos:cartao_assinatura', pagamento_id=pagamento_assinatura.id)
            elif metodo_pagamento == 'BOLETO':
                # Gerar boleto e redirecionar
                return redirect('pagamentos:boleto_assinatura', pagamento_id=pagamento_assinatura.id)
            else:
                messages.error(request, 'Método de pagamento inválido.')
                return self.get(request, *args, **kwargs)
                
        except Exception as e:
            logger.error(f"Erro ao processar pagamento de assinatura: {e}")
            messages.error(request, 'Erro ao processar pagamento. Tente novamente.')
            return self.get(request, *args, **kwargs)

