# Guia de Implementação de Pagamentos Reais

## Visão Geral

Atualmente o sistema possui uma estrutura completa para pagamentos, mas está configurado em modo de simulação. Este guia explica como implementar pagamentos reais com PIX, cartão de crédito e boleto bancário.

## Estrutura Atual do Sistema

### 1. Modelos Principais
- **ConfiguracaoPagamento**: Configurações dos gateways
- **PagamentoOnline**: Controle de pagamentos
- **LogPagamento**: Auditoria de transações

### 2. Arquivos Importantes
- `pagamentos/models.py` - Modelos de dados
- `pagamentos/views.py` - Lógica de processamento
- `pagamentos/utils.py` - Funções auxiliares
- `pagamentos/admin.py` - Interface administrativa

## Ordem Correta de Implementação

### ETAPA 1: Configuração Administrativa

1. **Acesse o Django Admin**:
   ```
   http://127.0.0.1:8000/admin/
   ```

2. **Configure os Pagamentos**:
   - Vá em "Configurações de Pagamento"
   - Configure cada método de pagamento:

#### PIX:
- ✅ **pix_habilitado**: True
- ✅ **pix_chave**: Sua chave PIX (CPF, CNPJ, email ou telefone)
- ✅ **pix_nome_recebedor**: Nome do recebedor

#### Cartão de Crédito:
- ✅ **cartao_habilitado**: True
- ✅ **gateway_api_key**: Chave da API do gateway
- ✅ **gateway_secret_key**: Chave secreta
- ✅ **gateway_endpoint**: URL da API do gateway

#### Boleto:
- ✅ **boleto_habilitado**: True
- ✅ **banco_codigo**: Código do banco
- ✅ **agencia**: Número da agência
- ✅ **conta**: Número da conta

### ETAPA 2: Escolha dos Gateways de Pagamento

#### Opções Recomendadas no Brasil:

1. **Mercado Pago** (Mais Popular)
   - PIX: ✅
   - Cartão: ✅
   - Boleto: ✅
   - Taxa: ~3.99% cartão, R$ 0,99 PIX
   - Documentação: https://www.mercadopago.com.br/developers

2. **PagSeguro**
   - PIX: ✅
   - Cartão: ✅
   - Boleto: ✅
   - Taxa: ~4.99% cartão, R$ 0,99 PIX

3. **Stripe** (Internacional)
   - PIX: ✅
   - Cartão: ✅
   - Boleto: ❌
   - Taxa: ~3.4% + R$ 0,30

4. **Asaas** (Focado em SaaS)
   - PIX: ✅
   - Cartão: ✅
   - Boleto: ✅
   - Taxa: ~2.99% cartão, R$ 0,50 PIX

### ETAPA 3: Implementação por Gateway

#### A. Mercado Pago (Recomendado)

1. **Instalar SDK**:
   ```bash
   pip install mercadopago
   ```

2. **Configurar no Admin**:
   - gateway_api_key: Seu Access Token
   - gateway_endpoint: https://api.mercadopago.com

3. **Modificar `pagamentos/views.py`**:
   ```python
   # Substituir a função processar_pix
   def processar_pix_mercadopago(pagamento, data):
       import mercadopago
       
       config = ConfiguracaoPagamento.get_configuracao()
       sdk = mercadopago.SDK(config.gateway_api_key)
       
       payment_data = {
           "transaction_amount": float(pagamento.valor_original),
           "description": f"Pagamento - {pagamento.parcela.contrato.inquilino.nome}",
           "payment_method_id": "pix",
           "payer": {
               "email": pagamento.email_pagador,
               "first_name": pagamento.nome_pagador.split()[0],
               "last_name": " ".join(pagamento.nome_pagador.split()[1:]) if len(pagamento.nome_pagador.split()) > 1 else ""
           }
       }
       
       payment_response = sdk.payment().create(payment_data)
       
       if payment_response["status"] == 201:
           payment = payment_response["response"]
           
           pagamento.transaction_id = payment["id"]
           pagamento.status = 'PROCESSANDO'
           pagamento.gateway_response = {
               'tipo': 'PIX',
               'codigo_pix': payment["point_of_interaction"]["transaction_data"]["qr_code"],
               'qr_code_base64': payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
               'payment_id': payment["id"]
           }
           pagamento.save()
           
           return JsonResponse({
               'success': True,
               'redirect_url': f'/pagamentos/aguardar/{pagamento.token_pagamento}/'
           })
   ```

#### B. Asaas (Alternativa Nacional)

1. **Instalar requests**:
   ```bash
   pip install requests
   ```

2. **Implementar PIX**:
   ```python
   def processar_pix_asaas(pagamento, data):
       import requests
       
       config = ConfiguracaoPagamento.get_configuracao()
       
       headers = {
           'access_token': config.gateway_api_key,
           'Content-Type': 'application/json'
       }
       
       payment_data = {
           "customer": pagamento.email_pagador,
           "billingType": "PIX",
           "value": float(pagamento.valor_original),
           "dueDate": pagamento.data_expiracao.strftime('%Y-%m-%d')
       }
       
       response = requests.post(
           f"{config.gateway_endpoint}/v3/payments",
           headers=headers,
           json=payment_data
       )
       
       if response.status_code == 200:
           payment = response.json()
           
           # Buscar QR Code PIX
           qr_response = requests.get(
               f"{config.gateway_endpoint}/v3/payments/{payment['id']}/pixQrCode",
               headers=headers
           )
           
           if qr_response.status_code == 200:
               qr_data = qr_response.json()
               
               pagamento.transaction_id = payment['id']
               pagamento.status = 'PROCESSANDO'
               pagamento.gateway_response = {
                   'tipo': 'PIX',
                   'codigo_pix': qr_data['payload'],
                   'qr_code_base64': qr_data['encodedImage'],
                   'payment_id': payment['id']
               }
               pagamento.save()
   ```

### ETAPA 4: Webhooks (Confirmação Automática)

1. **Criar endpoint para webhooks**:
   ```python
   # Em pagamentos/views.py
   @csrf_exempt
   def webhook_mercadopago(request):
       if request.method == 'POST':
           data = json.loads(request.body)
           
           if data.get('type') == 'payment':
               payment_id = data['data']['id']
               
               # Buscar pagamento no sistema
               try:
                   pagamento = PagamentoOnline.objects.get(transaction_id=payment_id)
                   
                   # Consultar status no Mercado Pago
                   import mercadopago
                   config = ConfiguracaoPagamento.get_configuracao()
                   sdk = mercadopago.SDK(config.gateway_api_key)
                   
                   payment_info = sdk.payment().get(payment_id)
                   
                   if payment_info['response']['status'] == 'approved':
                       pagamento.marcar_como_pago(
                           valor_pago=payment_info['response']['transaction_amount'],
                           transaction_id=payment_id,
                           gateway_response=payment_info['response']
                       )
                       
               except PagamentoOnline.DoesNotExist:
                   pass
           
           return HttpResponse(status=200)
   ```

2. **Configurar URL do webhook**:
   ```python
   # Em pagamentos/urls.py
   urlpatterns = [
       # ... outras URLs
       path('webhook/mercadopago/', webhook_mercadopago, name='webhook_mercadopago'),
   ]
   ```

3. **Registrar webhook no gateway**:
   - Mercado Pago: https://www.mercadopago.com.br/developers/panel/webhooks
   - URL: `https://seudominio.com/pagamentos/webhook/mercadopago/`

### ETAPA 5: Testes

1. **Ambiente de Sandbox**:
   - Use as credenciais de teste do gateway
   - Teste todos os fluxos de pagamento

2. **Cartões de Teste** (Mercado Pago):
   - Visa: 4509 9535 6623 3704
   - Mastercard: 5031 7557 3453 0604
   - CVV: 123
   - Validade: 11/25

### ETAPA 6: Produção

1. **Trocar credenciais**:
   - Substitua as chaves de teste pelas de produção
   - Configure o webhook em produção

2. **SSL obrigatório**:
   - Certifique-se de que o site tem HTTPS
   - Gateways exigem SSL para produção

## Arquivos que Precisam ser Modificados

### 1. `pagamentos/views.py`
- Substituir `processar_pix()` pela integração real
- Substituir `processar_cartao()` pela integração real
- Adicionar webhook endpoints

### 2. `pagamentos/utils.py`
- Adicionar funções de validação específicas do gateway
- Implementar retry logic para falhas de rede

### 3. `requirements.txt`
- Adicionar SDK do gateway escolhido

### 4. `settings.py`
- Configurar variáveis de ambiente para chaves

## Custos Estimados

### Taxas dos Gateways:
- **PIX**: R$ 0,50 - R$ 0,99 por transação
- **Cartão**: 2,99% - 4,99% do valor
- **Boleto**: R$ 2,50 - R$ 3,50 por boleto

### Exemplo para R$ 199,90:
- PIX: R$ 0,99 (você recebe R$ 198,91)
- Cartão: R$ 7,98 (você recebe R$ 191,92)
- Boleto: R$ 3,50 (você recebe R$ 196,40)

## Próximos Passos

1. ✅ Escolher gateway de pagamento
2. ✅ Criar conta no gateway
3. ✅ Configurar no Django Admin
4. ✅ Implementar integração
5. ✅ Configurar webhooks
6. ✅ Testar em sandbox
7. ✅ Colocar em produção

## Suporte

Para implementar, você precisará:
1. **Conta no gateway** (Mercado Pago, Asaas, etc.)
2. **Chaves de API** (sandbox e produção)
3. **Domínio com SSL** para webhooks
4. **Conhecimento básico** de APIs REST

---

**Recomendação**: Comece com o **Mercado Pago** por ter a melhor documentação e suporte no Brasil.