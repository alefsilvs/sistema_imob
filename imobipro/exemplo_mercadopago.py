#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Implementação com Mercado Pago

Este arquivo mostra como integrar pagamentos reais usando o Mercado Pago.
Substitua as funções em pagamentos/views.py pelas versões abaixo.

Pré-requisitos:
1. pip install mercadopago
2. Conta no Mercado Pago
3. Access Token (sandbox e produção)
"""

import json
import mercadopago
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import PagamentoOnline, ConfiguracaoPagamento, LogPagamento


def processar_pix_mercadopago(pagamento, data):
    """
    Processa pagamento PIX via Mercado Pago
    
    Args:
        pagamento: Instância de PagamentoOnline
        data: Dados do formulário
    
    Returns:
        JsonResponse com resultado do processamento
    """
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        
        # Validar configuração
        if not config.pix_habilitado or not config.gateway_api_key:
            return JsonResponse({
                'success': False,
                'error': 'PIX não configurado corretamente'
            }, status=400)
        
        # Inicializar SDK do Mercado Pago
        sdk = mercadopago.SDK(config.gateway_api_key)
        
        # Preparar dados do pagamento
        payment_data = {
            "transaction_amount": float(pagamento.valor_original),
            "description": f"Pagamento {pagamento.parcela.get_tipo_display()} - {pagamento.parcela.contrato.inquilino.nome}",
            "payment_method_id": "pix",
            "payer": {
                "email": pagamento.email_pagador or "cliente@exemplo.com",
                "first_name": pagamento.nome_pagador.split()[0] if pagamento.nome_pagador else "Cliente",
                "last_name": " ".join(pagamento.nome_pagador.split()[1:]) if pagamento.nome_pagador and len(pagamento.nome_pagador.split()) > 1 else "Sistema"
            },
            "external_reference": pagamento.token_pagamento,
            "notification_url": f"{config.url_sucesso or 'https://seusite.com'}/pagamentos/webhook/mercadopago/"
        }
        
        # Criar pagamento no Mercado Pago
        payment_response = sdk.payment().create(payment_data)
        
        # Log da tentativa
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='TENTATIVA',
            descricao='Tentativa de criação de PIX no Mercado Pago',
            dados_extras={
                'payment_data': payment_data,
                'response_status': payment_response.get('status')
            }
        )
        
        if payment_response["status"] == 201:
            payment = payment_response["response"]
            
            # Extrair dados do PIX
            pix_data = payment.get("point_of_interaction", {}).get("transaction_data", {})
            
            # Atualizar pagamento
            pagamento.transaction_id = str(payment["id"])
            pagamento.status = 'PROCESSANDO'
            pagamento.gateway_response = {
                'tipo': 'PIX',
                'gateway': 'mercadopago',
                'payment_id': payment["id"],
                'status': payment["status"],
                'codigo_pix': pix_data.get("qr_code", ""),
                'qr_code_base64': pix_data.get("qr_code_base64", ""),
                'ticket_url': pix_data.get("ticket_url", ""),
                'created_at': payment.get("date_created"),
                'expires_at': payment.get("date_of_expiration")
            }
            pagamento.save()
            
            # Log de sucesso
            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='CRIACAO',
                descricao='PIX criado com sucesso no Mercado Pago',
                dados_extras={
                    'payment_id': payment["id"],
                    'status': payment["status"]
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'PIX gerado com sucesso',
                'redirect_url': f'/pagamentos/aguardar/{pagamento.token_pagamento}/'
            })
        else:
            # Log de erro
            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='ERRO',
                descricao='Erro ao criar PIX no Mercado Pago',
                dados_extras=payment_response
            )
            
            return JsonResponse({
                'success': False,
                'error': 'Erro ao gerar PIX. Tente novamente.'
            }, status=400)
            
    except Exception as e:
        # Log de exceção
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='ERRO',
            descricao=f'Exceção ao processar PIX: {str(e)}',
            dados_extras={'exception': str(e)}
        )
        
        return JsonResponse({
            'success': False,
            'error': 'Erro interno. Tente novamente.'
        }, status=500)


def processar_cartao_mercadopago(pagamento, data):
    """
    Processa pagamento com cartão via Mercado Pago
    
    Args:
        pagamento: Instância de PagamentoOnline
        data: Dados do cartão do formulário
    
    Returns:
        JsonResponse com resultado do processamento
    """
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        
        # Validar configuração
        if not config.cartao_habilitado or not config.gateway_api_key:
            return JsonResponse({
                'success': False,
                'error': 'Cartão não configurado corretamente'
            }, status=400)
        
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
        
        # Inicializar SDK
        sdk = mercadopago.SDK(config.gateway_api_key)
        
        # Identificar bandeira do cartão
        def identificar_bandeira(numero):
            numero = numero.replace(' ', '')
            if numero.startswith('4'):
                return 'visa'
            elif numero.startswith(('5', '2')):
                return 'master'
            elif numero.startswith('3'):
                return 'amex'
            elif numero.startswith('6'):
                return 'elo'
            else:
                return 'visa'  # default
        
        bandeira = identificar_bandeira(numero_cartao)
        
        # Preparar dados do pagamento
        payment_data = {
            "transaction_amount": float(pagamento.valor_original),
            "token": data.get('card_token'),  # Token do cartão (gerado no frontend)
            "description": f"Pagamento {pagamento.parcela.get_tipo_display()} - {pagamento.parcela.contrato.inquilino.nome}",
            "installments": parcelas,
            "payment_method_id": bandeira,
            "issuer_id": data.get('issuer_id'),  # ID do emissor (obtido via API)
            "payer": {
                "email": pagamento.email_pagador or "cliente@exemplo.com",
                "identification": {
                    "type": "CPF",
                    "number": data.get('cpf', '00000000000')
                },
                "first_name": pagamento.nome_pagador.split()[0] if pagamento.nome_pagador else "Cliente",
                "last_name": " ".join(pagamento.nome_pagador.split()[1:]) if pagamento.nome_pagador and len(pagamento.nome_pagador.split()) > 1 else "Sistema"
            },
            "external_reference": pagamento.token_pagamento,
            "notification_url": f"{config.url_sucesso or 'https://seusite.com'}/pagamentos/webhook/mercadopago/"
        }
        
        # Criar pagamento
        payment_response = sdk.payment().create(payment_data)
        
        # Log da tentativa
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='TENTATIVA',
            descricao='Tentativa de pagamento com cartão no Mercado Pago',
            dados_extras={
                'bandeira': bandeira,
                'parcelas': parcelas,
                'response_status': payment_response.get('status')
            }
        )
        
        if payment_response["status"] == 201:
            payment = payment_response["response"]
            
            # Atualizar pagamento
            pagamento.transaction_id = str(payment["id"])
            
            # Definir status baseado na resposta
            mp_status = payment.get("status")
            if mp_status == "approved":
                pagamento.status = 'APROVADO'
                pagamento.data_pagamento = timezone.now()
                pagamento.data_confirmacao = timezone.now()
            elif mp_status == "pending":
                pagamento.status = 'PROCESSANDO'
            elif mp_status == "rejected":
                pagamento.status = 'REJEITADO'
            else:
                pagamento.status = 'PROCESSANDO'
            
            pagamento.gateway_response = {
                'tipo': 'CARTAO',
                'gateway': 'mercadopago',
                'payment_id': payment["id"],
                'status': payment["status"],
                'status_detail': payment.get("status_detail"),
                'bandeira': bandeira,
                'parcelas': parcelas,
                'valor_parcela': float(pagamento.valor_original) / parcelas,
                'created_at': payment.get("date_created"),
                'approved_at': payment.get("date_approved")
            }
            pagamento.save()
            
            # Se aprovado, marcar como pago
            if mp_status == "approved":
                pagamento.marcar_como_pago(
                    valor_pago=payment.get("transaction_amount"),
                    transaction_id=str(payment["id"]),
                    gateway_response=pagamento.gateway_response
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Pagamento aprovado!',
                    'redirect_url': f'/pagamentos/sucesso/{pagamento.token_pagamento}/'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': 'Pagamento em processamento',
                    'redirect_url': f'/pagamentos/aguardar/{pagamento.token_pagamento}/'
                })
        else:
            # Log de erro
            LogPagamento.objects.create(
                pagamento=pagamento,
                tipo='ERRO',
                descricao='Erro ao processar cartão no Mercado Pago',
                dados_extras=payment_response
            )
            
            return JsonResponse({
                'success': False,
                'error': 'Cartão recusado. Verifique os dados e tente novamente.'
            }, status=400)
            
    except Exception as e:
        # Log de exceção
        LogPagamento.objects.create(
            pagamento=pagamento,
            tipo='ERRO',
            descricao=f'Exceção ao processar cartão: {str(e)}',
            dados_extras={'exception': str(e)}
        )
        
        return JsonResponse({
            'success': False,
            'error': 'Erro interno. Tente novamente.'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_mercadopago(request):
    """
    Webhook para receber notificações do Mercado Pago
    
    Configure esta URL no painel do Mercado Pago:
    https://seusite.com/pagamentos/webhook/mercadopago/
    """
    try:
        # Parse do JSON
        data = json.loads(request.body.decode('utf-8'))
        
        # Log da notificação
        print(f"Webhook Mercado Pago: {data}")
        
        # Verificar se é notificação de pagamento
        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if payment_id:
                # Buscar pagamento no sistema
                try:
                    pagamento = PagamentoOnline.objects.get(transaction_id=str(payment_id))
                    
                    # Consultar status atualizado no Mercado Pago
                    config = ConfiguracaoPagamento.get_configuracao()
                    sdk = mercadopago.SDK(config.gateway_api_key)
                    
                    payment_info = sdk.payment().get(payment_id)
                    
                    if payment_info['status'] == 200:
                        payment = payment_info['response']
                        mp_status = payment.get('status')
                        
                        # Log da consulta
                        LogPagamento.objects.create(
                            pagamento=pagamento,
                            tipo='TENTATIVA',
                            descricao=f'Webhook recebido - Status: {mp_status}',
                            dados_extras={
                                'payment_id': payment_id,
                                'status': mp_status,
                                'webhook_data': data
                            }
                        )
                        
                        # Atualizar status do pagamento
                        if mp_status == 'approved' and pagamento.status != 'APROVADO':
                            pagamento.marcar_como_pago(
                                valor_pago=payment.get('transaction_amount'),
                                transaction_id=str(payment_id),
                                gateway_response=payment
                            )
                            
                            LogPagamento.objects.create(
                                pagamento=pagamento,
                                tipo='APROVACAO',
                                descricao='Pagamento aprovado via webhook',
                                dados_extras={'payment_data': payment}
                            )
                            
                        elif mp_status == 'rejected':
                            pagamento.status = 'REJEITADO'
                            pagamento.save()
                            
                            LogPagamento.objects.create(
                                pagamento=pagamento,
                                tipo='REJEICAO',
                                descricao='Pagamento rejeitado via webhook',
                                dados_extras={'payment_data': payment}
                            )
                        
                except PagamentoOnline.DoesNotExist:
                    print(f"Pagamento não encontrado: {payment_id}")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Erro no webhook: {str(e)}")
        return HttpResponse(status=500)


# Função auxiliar para obter métodos de pagamento disponíveis
def get_payment_methods_mercadopago():
    """
    Obtém métodos de pagamento disponíveis no Mercado Pago
    
    Returns:
        dict: Métodos de pagamento disponíveis
    """
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        sdk = mercadopago.SDK(config.gateway_api_key)
        
        payment_methods = sdk.payment_methods().list_all()
        
        if payment_methods['status'] == 200:
            methods = payment_methods['response']
            
            # Filtrar apenas cartões de crédito
            credit_cards = [
                method for method in methods 
                if method.get('payment_type_id') == 'credit_card'
            ]
            
            return {
                'success': True,
                'credit_cards': credit_cards,
                'all_methods': methods
            }
        else:
            return {
                'success': False,
                'error': 'Erro ao consultar métodos de pagamento'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Exemplo de uso no Django Admin
def test_mercadopago_connection():
    """
    Testa a conexão com o Mercado Pago
    
    Returns:
        dict: Resultado do teste
    """
    try:
        config = ConfiguracaoPagamento.get_configuracao()
        
        if not config.gateway_api_key:
            return {
                'success': False,
                'message': 'Access Token não configurado'
            }
        
        sdk = mercadopago.SDK(config.gateway_api_key)
        
        # Testar com uma consulta simples
        payment_methods = sdk.payment_methods().list_all()
        
        if payment_methods['status'] == 200:
            return {
                'success': True,
                'message': 'Conexão com Mercado Pago OK',
                'methods_count': len(payment_methods['response'])
            }
        else:
            return {
                'success': False,
                'message': 'Erro na conexão com Mercado Pago',
                'details': payment_methods
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro: {str(e)}'
        }


"""
PARA USAR ESTE CÓDIGO:

1. Instale o SDK:
   pip install mercadopago

2. Configure no Django Admin:
   - Vá em "Configurações de Pagamento"
   - Marque "cartao_habilitado" e "pix_habilitado"
   - Adicione seu Access Token em "gateway_api_key"
   - Configure "gateway_endpoint" como "https://api.mercadopago.com"

3. Substitua as funções em pagamentos/views.py:
   - processar_pix() -> processar_pix_mercadopago()
   - processar_cartao() -> processar_cartao_mercadopago()

4. Adicione a URL do webhook em pagamentos/urls.py:
   path('webhook/mercadopago/', webhook_mercadopago, name='webhook_mercadopago'),

5. Configure o webhook no Mercado Pago:
   https://www.mercadopago.com.br/developers/panel/webhooks
   URL: https://seusite.com/pagamentos/webhook/mercadopago/

6. Para testes, use as credenciais de sandbox:
   https://www.mercadopago.com.br/developers/panel/credentials
"""