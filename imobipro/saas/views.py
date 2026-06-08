from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import uuid
import random
import string
import time
import logging
import requests

from .models import PlanoComercial, Tenant, ConfiguracaoTenant, VerificacaoEmail, PagamentoPlano
from .forms import RegistroEmpresaForm, ConfiguracaoInicialForm, CriarEmpresaForm
from .admin_utils import is_system_admin, get_admin_tenant_for_user

logger = logging.getLogger(__name__)

def _ensure_default_planos():
    try:
        defaults = [
            {
                "nome": "Trial Gratuito",
                "tipo": "trial",
                "preco_mensal": Decimal("0.00"),
                "max_usuarios": 1,
                "max_imoveis": 50,
                "max_contratos": 10,
                "storage_gb": 1,
                "api_calls_mes": 1000,
                "suporte_prioritario": False,
                "backup_automatico": False,
                "subdominio_personalizado": False,
                "ativo": True,
                "is_trial": True,
            },
            {
                "nome": "Básico",
                "tipo": "basico",
                "preco_mensal": Decimal("299.99"),
                "max_usuarios": 3,
                "max_imoveis": 200,
                "max_contratos": 200,
                "storage_gb": 5,
                "api_calls_mes": 5000,
                "suporte_prioritario": False,
                "backup_automatico": False,
                "subdominio_personalizado": False,
                "ativo": True,
                "is_trial": False,
            },
            {
                "nome": "Profissional",
                "tipo": "profissional",
                "preco_mensal": Decimal("499.99"),
                "max_usuarios": -1,
                "max_imoveis": -1,
                "max_contratos": -1,
                "storage_gb": 50,
                "api_calls_mes": 20000,
                "suporte_prioritario": True,
                "backup_automatico": True,
                "subdominio_personalizado": True,
                "ativo": True,
                "is_trial": False,
            },
        ]
        for data in defaults:
            obj, _ = PlanoComercial.objects.get_or_create(nome=data["nome"], defaults=data)
            needs_update = False
            for k, v in data.items():
                if getattr(obj, k, None) != v:
                    setattr(obj, k, v)
                    needs_update = True
            if needs_update:
                obj.save(update_fields=list(data.keys()))
    except Exception:
        return

def _plano_features(plano):
    features = []
    if getattr(plano, "is_trial", False) or getattr(plano, "tipo", "") == "trial":
        features.append("7 dias grátis")
    if getattr(plano, "max_usuarios", None) == -1:
        features.append("Usuários ilimitados")
    elif getattr(plano, "max_usuarios", None) is not None:
        features.append(f"Até {plano.max_usuarios} usuários")
    if getattr(plano, "max_imoveis", None) == -1:
        features.append("Imóveis ilimitados")
    elif getattr(plano, "max_imoveis", None) is not None:
        features.append(f"Até {plano.max_imoveis} imóveis")
    if getattr(plano, "max_contratos", None) == -1:
        features.append("Contratos ilimitados")
    elif getattr(plano, "max_contratos", None) is not None:
        features.append(f"Até {plano.max_contratos} contratos")
    if getattr(plano, "storage_gb", None) is not None:
        features.append(f"{plano.storage_gb}GB armazenamento")
    if getattr(plano, "suporte_prioritario", False):
        features.append("Suporte prioritário")
    if getattr(plano, "backup_automatico", False):
        features.append("Backup automático")
    if getattr(plano, "subdominio_personalizado", False):
        features.append("Subdomínio personalizado")
    return features

def _asaas_is_sandbox(api_base_url: str) -> bool:
    if not api_base_url:
        return False
    return "sandbox" in api_base_url.lower()

def _asaas_checkout_host(api_base_url: str) -> str:
    return "https://sandbox.asaas.com" if _asaas_is_sandbox(api_base_url) else "https://asaas.com"

def _asaas_api_base_url(config) -> str:
    base = (getattr(config, "gateway_endpoint", "") or "").strip()
    return base.rstrip("/")

def _asaas_api_headers(config) -> dict:
    api_key = (getattr(config, "gateway_api_key", "") or "").strip()
    return {
        "Content-Type": "application/json",
        "User-Agent": "sistema-imo",
        "access_token": api_key,
    }

def _asaas_webhook_token_from_request(request) -> str:
    token = request.META.get("HTTP_ASAAS_ACCESS_TOKEN")
    if token:
        return token.strip()
    token = request.META.get("HTTP_ASAAS-ACCESS-TOKEN")
    if token:
        return token.strip()
    return ""

def _asaas_event_is_paid(event: str, payment_status: str) -> bool:
    paid_events = {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED", "PAYMENT_APPROVED"}
    paid_statuses = {"RECEIVED", "CONFIRMED"}
    if event and event.upper() in paid_events:
        return True
    if payment_status and payment_status.upper() in paid_statuses:
        return True
    return False

def _asaas_extract_external_reference(payload: dict) -> str:
    payment = payload.get("payment") or {}
    external_reference = payment.get("externalReference") or payload.get("externalReference")
    if external_reference:
        return str(external_reference)
    checkout = payload.get("checkoutSession") or {}
    external_reference = checkout.get("externalReference")
    if external_reference:
        return str(external_reference)
    return ""

def _asaas_create_checkout_for_pagamento(request, pagamento: PagamentoPlano, billing_type: str) -> str:
    from pagamentos.models import ConfiguracaoPagamento

    config = ConfiguracaoPagamento.get_configuracao()
    api_base_url = _asaas_api_base_url(config)
    if not api_base_url:
        raise ValueError("Endpoint do Asaas não configurado.")
    if not getattr(config, "gateway_api_key", ""):
        raise ValueError("API Key do Asaas não configurada.")

    success_url = request.build_absolute_uri(reverse("saas:planos"))
    cancel_url = request.build_absolute_uri(reverse("saas:planos"))
    expired_url = request.build_absolute_uri(reverse("saas:planos"))

    item_name = f"Assinatura {pagamento.plano.nome}"
    item_description = pagamento.descricao or f"Assinatura do plano {pagamento.plano.nome}"

    payload = {
        "billingTypes": [billing_type],
        "chargeTypes": ["DETACHED"],
        "minutesToExpire": 60,
        "callback": {"successUrl": success_url, "cancelUrl": cancel_url, "expiredUrl": expired_url},
        "items": [
            {
                "externalReference": pagamento.token_pagamento,
                "name": item_name,
                "description": item_description,
                "quantity": 1,
                "value": float(pagamento.valor),
            }
        ],
        "customerData": {
            "name": pagamento.nome_pagador,
            "email": pagamento.email_pagador,
            "cpfCnpj": pagamento.documento_pagador or None,
            "phone": pagamento.telefone_pagador or None,
        },
    }

    response = requests.post(f"{api_base_url}/checkouts", headers=_asaas_api_headers(config), json=payload, timeout=30)
    if response.status_code not in (200, 201):
        try:
            error_json = response.json()
        except Exception:
            error_json = {"raw": response.text}
        raise RuntimeError(f"Asaas retornou {response.status_code}: {error_json}")

    data = response.json() or {}
    checkout_id = data.get("id") or data.get("checkoutSessionId") or data.get("sessionId")
    if not checkout_id:
        raise RuntimeError("Asaas não retornou o id da sessão de checkout.")

    checkout_url = f"{_asaas_checkout_host(api_base_url)}/checkoutSession/show?id={checkout_id}"

    pagamento.transaction_id = str(checkout_id)
    metadata = pagamento.metadata or {}
    metadata.update(
        {
            "asaas_checkout_id": str(checkout_id),
            "asaas_checkout_url": checkout_url,
            "asaas_billing_type": billing_type,
        }
    )
    pagamento.metadata = metadata
    pagamento.gateway_response = data
    pagamento.save(update_fields=["transaction_id", "metadata", "gateway_response"])

    return checkout_url

class PlanosPublicosView(TemplateView):
    """View pública para exibir os planos disponíveis - Primeira página do fluxo Netflix"""
    template_name = 'saas/planos_publicos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _ensure_default_planos()
        planos = list(PlanoComercial.objects.filter(ativo=True).order_by('preco_mensal'))
        for p in planos:
            p.features_joined = "||".join(_plano_features(p))
            p.price_str = "{:.2f}".format(p.preco_mensal or Decimal("0.00"))
            p.price_display = p.price_str.replace(".", ",")
        context['planos'] = planos
        return context


class PlanosView(TemplateView):
    """View para exibir os planos disponíveis - Passo 2 do fluxo Netflix (após login)"""
    template_name = 'saas/planos.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Fluxo Netflix: Passo 2 - Escolher plano (requer autenticação)
        if not request.user.is_authenticated:
            # Usuário não autenticado vai para login (Passo 1)
            return redirect('login')
        
        # Verificar se é admin do sistema
        if is_system_admin(request.user):
            # Admin do sistema pode acessar normalmente
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar se o usuário tem um tenant
        try:
            tenant = Tenant.objects.get(usuario_admin=request.user)
            
            # Se o tenant está ativo, redirecionar para o dashboard
            if tenant.status == 'ativo':
                return redirect('/dashboard/')
            
            # Se o tenant está em trial, verificar se expirou
            elif tenant.status == 'trial':
                if not tenant.is_trial_ativo:
                    # Trial expirado, precisa fazer pagamento
                    # Verificar se há pagamento pendente
                    pagamento_pendente = PagamentoPlano.objects.filter(
                        usuario=request.user,
                        status='pendente'
                    ).first()
                    
                    if pagamento_pendente:
                        return redirect('saas:pagamento_plano', token=pagamento_pendente.token)
                else:
                    # Trial ainda válido, ir para dashboard
                    return redirect('/dashboard/')
            
            # Se o tenant está suspenso ou inativo, verificar pagamento pendente
            elif tenant.status in ['suspenso', 'inativo']:
                pagamento_pendente = PagamentoPlano.objects.filter(
                    usuario=request.user,
                    status='pendente'
                ).first()
                
                if pagamento_pendente:
                    return redirect('saas:pagamento_plano', token=pagamento_pendente.token)
            
        except Tenant.DoesNotExist:
            # Usuário não tem tenant, pode continuar para escolher plano
            pass
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _ensure_default_planos()
        planos = list(PlanoComercial.objects.filter(ativo=True).order_by('preco_mensal'))
        for p in planos:
            p.features_joined = "||".join(_plano_features(p))
            p.price_str = "{:.2f}".format(p.preco_mensal or Decimal("0.00"))
            p.price_display = p.price_str.replace(".", ",")
        context['planos'] = planos
        
        # Verificar se o usuário é admin do sistema
        if self.request.user.is_authenticated and is_system_admin(self.request.user):
            context['is_system_admin'] = True
            context['admin_message'] = 'Você é um administrador do sistema e tem acesso gratuito a todos os planos.'
        
        return context

class RegistroView(TemplateView):
    """View para registro de nova empresa"""
    template_name = 'saas/registro.html'
    
    def _create_tenant_for_user(self, *, user, nome_empresa, plano):
        base_slug = slugify(nome_empresa)
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        base_subdominio = slugify(nome_empresa).replace('-', '')
        subdominio = base_subdominio
        counter = 1
        while Tenant.objects.filter(subdominio=subdominio).exists():
            subdominio = f"{base_subdominio}{counter}"
            counter += 1

        tenant = Tenant.objects.create(
            nome_empresa=nome_empresa,
            slug=slug,
            subdominio=subdominio,
            usuario_admin=user,
            plano=plano,
            status='trial',
            trial_ate=(timezone.now() + timedelta(days=7)),
            data_expiracao=None,
        )
        try:
            self.request.session['tenant_id'] = tenant.id
            self.request.session.modified = True
        except Exception:
            pass
        return tenant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _ensure_default_planos()

        is_authenticated = bool(getattr(self.request.user, "is_authenticated", False))
        context['modo'] = 'criar_empresa' if is_authenticated else 'criar_conta'

        plano_id = self.request.POST.get('plano_id') or self.request.GET.get('plano')
        if plano_id:
            try:
                plano_sel = PlanoComercial.objects.get(id=plano_id, ativo=True)
                plano_sel.features_joined = "||".join(_plano_features(plano_sel))
                plano_sel.price_str = "{:.2f}".format(plano_sel.preco_mensal or Decimal("0.00"))
                plano_sel.price_display = plano_sel.price_str.replace(".", ",")
                context['plano_selecionado'] = plano_sel
            except PlanoComercial.DoesNotExist:
                pass

        planos = list(PlanoComercial.objects.filter(ativo=True).order_by('preco_mensal'))
        for p in planos:
            p.features_joined = "||".join(_plano_features(p))
            p.price_str = "{:.2f}".format(p.preco_mensal or Decimal("0.00"))
            p.price_display = p.price_str.replace(".", ",")
        context['planos'] = planos

        if 'form' not in context:
            context['form'] = CriarEmpresaForm() if is_authenticated else RegistroEmpresaForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        is_authenticated = bool(getattr(request.user, "is_authenticated", False))
        form = (CriarEmpresaForm(request.POST) if is_authenticated else RegistroEmpresaForm(request.POST))
        if not form.is_valid():
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)
        return self.form_valid(form)
    
    def form_valid(self, form):
        _ensure_default_planos()

        plano_id = self.request.POST.get('plano_id') or self.request.GET.get('plano')
        if not plano_id:
            form.add_error(None, 'Selecione um plano para continuar.')
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)

        plano = PlanoComercial.objects.filter(id=plano_id, ativo=True).first()
        if not plano:
            form.add_error(None, 'Plano inválido. Selecione novamente.')
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)

        try:
            self.request.session['plano_selecionado'] = str(plano.id)
        except Exception:
            pass

        is_authenticated = bool(getattr(self.request.user, "is_authenticated", False))
        if is_authenticated:
            if Tenant.objects.filter(usuario_admin=self.request.user).exists():
                return redirect('/dashboard/')
            tenant = self._create_tenant_for_user(
                user=self.request.user,
                nome_empresa=form.cleaned_data['nome_empresa'],
                plano=plano,
            )
            messages.success(self.request, 'Empresa criada com sucesso! Escolha a forma de pagamento.')
            return redirect('saas:escolher_pagamento')

        email = (form.cleaned_data.get('email') or '').strip().lower()
        if not email:
            form.add_error('email', 'E-mail é obrigatório.')
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=form.cleaned_data['senha'],
            first_name='',
            last_name=''
        )

        nome_empresa = email.split('@')[0] if '@' in email else email
        nome_empresa = (nome_empresa or 'Minha Empresa')[:200]

        tenant = self._create_tenant_for_user(
            user=user,
            nome_empresa=nome_empresa,
            plano=plano,
        )

        verificacao, created = VerificacaoEmail.objects.get_or_create(
            usuario=user,
            defaults={'email_verificado': False}
        )
        email_enviado = verificacao.enviar_email_verificacao(self.request)

        self.request.session['registro_pendente'] = {
            'user_id': user.id,
            'tenant_id': tenant.id,
            'email': user.email
        }
        self.request.session['email_verificacao_enviado'] = email_enviado

        if email_enviado:
            messages.success(self.request, 'Conta criada com sucesso! Confirme seu e-mail para entrar.')
        else:
            messages.warning(
                self.request,
                'Conta criada, mas o e-mail de confirmacao nao foi enviado agora. '
                'Use o botao de reenviar nesta pagina apos ajustarmos o SMTP.'
            )
        return redirect('saas:email_enviado')

class EscolherPagamentoView(TemplateView):
    """View para escolher forma de pagamento após registro"""
    template_name = 'saas/escolher_pagamento.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar se o usuário está autenticado
        if not request.user.is_authenticated:
            return redirect('saas:planos')
        
        # Verificar se o usuário tem um tenant
        try:
            tenant = Tenant.objects.get(usuario_admin=request.user)
            
            # Se o tenant já está ativo, redirecionar para dashboard
            if tenant.status == 'ativo':
                return redirect('/dashboard/')
            
            # Se não está em trial nem pendente de pagamento, redirecionar para planos
            if tenant.status not in ['trial', 'pendente_pagamento']:
                return redirect('saas:planos')
                
        except Tenant.DoesNotExist:
            # Se não tem tenant, redirecionar para registro
            return redirect('saas:registro')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _ensure_default_planos()
        tenant = Tenant.objects.get(usuario_admin=self.request.user)
        planos = list(PlanoComercial.objects.filter(ativo=True).order_by('preco_mensal'))
        for p in planos:
            p.features_joined = "||".join(_plano_features(p))
            p.price_str = "{:.2f}".format(p.preco_mensal or Decimal("0.00"))
            p.price_display = p.price_str.replace(".", ",")

        plano = None
        plano_id = self.request.session.get('plano_selecionado')
        if plano_id:
            plano = PlanoComercial.objects.filter(id=plano_id, ativo=True).first()
        if not plano and getattr(tenant, "plano_id", None):
            plano = PlanoComercial.objects.filter(id=tenant.plano_id, ativo=True).first()
        if not plano:
            plano = PlanoComercial.objects.filter(ativo=True).order_by('preco_mensal').first()

        context.update({
            'tenant': tenant,
            'plano': plano,
            'planos': planos,
            'plano_recursos': _plano_features(plano) if plano else [],
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Processar a escolha da forma de pagamento"""
        try:
            # Obter dados do formulário
            plano_id = request.POST.get('plano_id')
            metodo_pagamento = request.POST.get('metodo_pagamento')
            tipo_cartao = request.POST.get('tipo_cartao', '')
            
            if not plano_id or not metodo_pagamento:
                messages.error(request, 'Por favor, selecione um plano e forma de pagamento.')
                return self.get(request, *args, **kwargs)
            
            # Obter o tenant
            tenant = Tenant.objects.get(usuario_admin=request.user)
            plano = PlanoComercial.objects.get(id=plano_id)
            
            # Criar registro de pagamento
            pagamento = PagamentoPlano.objects.create(
                usuario=request.user,
                tenant=tenant,
                plano=plano,
                metodo_pagamento=metodo_pagamento,
                valor=plano.preco_mensal,
                status='pendente',
                nome_pagador=request.user.get_full_name() or request.user.username,
                email_pagador=request.user.email
            )
            
            billing_type_map = {
                "pix": "PIX",
                "cartao": "CREDIT_CARD",
                "boleto": "BOLETO",
            }
            billing_type = billing_type_map.get(metodo_pagamento)
            if not billing_type:
                messages.error(request, "Forma de pagamento inválida.")
                return self.get(request, *args, **kwargs)

            checkout_url = _asaas_create_checkout_for_pagamento(request, pagamento, billing_type)
            
            # Armazenar token na sessão
            request.session['pagamento_token'] = pagamento.token_pagamento
            
            return redirect(checkout_url)
            
        except Exception as e:
            logger.exception("Erro ao processar pagamento (EscolherPagamentoView)")
            messages.error(request, f'Erro ao processar pagamento: {str(e)}')
            return self.get(request, *args, **kwargs)

class ConfiguracaoInicialView(TemplateView):
    """View para configuração inicial do tenant"""
    template_name = 'saas/configuracao_inicial.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.session.get('tenant_id')
        if tenant_id:
            try:
                context['tenant'] = Tenant.objects.get(id=tenant_id)
                context['form'] = ConfiguracaoInicialForm()
            except Tenant.DoesNotExist:
                pass
        return context
    
    def post(self, request, *args, **kwargs):
        tenant_id = request.session.get('tenant_id')
        if not tenant_id:
            return redirect('saas:registro')
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return redirect('saas:registro')
        
        form = ConfiguracaoInicialForm(request.POST)
        if form.is_valid():
            # Criar ou atualizar configuração
            config, created = ConfiguracaoTenant.objects.get_or_create(
                tenant=tenant,
                defaults={
                    'email_contato': form.cleaned_data['email_contato'],
                    'telefone_contato': form.cleaned_data['telefone_contato'],
                    'endereco': form.cleaned_data['endereco'],
                    'cor_primaria': form.cleaned_data['cor_primaria'],
                    'cor_secundaria': form.cleaned_data['cor_secundaria']
                }
            )
            
            if not created:
                config.email_contato = form.cleaned_data['email_contato']
                config.telefone_contato = form.cleaned_data['telefone_contato']
                config.endereco = form.cleaned_data['endereco']
                config.cor_primaria = form.cleaned_data['cor_primaria']
                config.cor_secundaria = form.cleaned_data['cor_secundaria']
                config.save()
            
            messages.success(request, 'Configuração inicial concluída com sucesso!')
            return redirect('pagamentos:pagamento_assinatura')  # Redirecionar para página de pagamento
        
        return render(request, self.template_name, {
            'tenant': tenant,
            'form': form
        })

@csrf_exempt
def webhook_pagamento(request):
    """Webhook para processar confirmações de pagamento"""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    try:
        from pagamentos.models import ConfiguracaoPagamento

        config = ConfiguracaoPagamento.get_configuracao()
        expected_token = (getattr(config, "gateway_secret_key", "") or "").strip()
        provided_token = _asaas_webhook_token_from_request(request)
        if expected_token and provided_token != expected_token:
            return HttpResponse("Unauthorized", status=401)

        data = json.loads(request.body or b"{}")
        event = (data.get("event") or "").strip()
        payment = data.get("payment") or {}
        payment_status = (payment.get("status") or "").strip()

        token_pagamento = _asaas_extract_external_reference(data)
        if not token_pagamento:
            return HttpResponse("externalReference não informado", status=400)

        pagamento = PagamentoPlano.objects.filter(token_pagamento=token_pagamento).first()
        if not pagamento:
            return HttpResponse("Pagamento não encontrado", status=404)

        if _asaas_event_is_paid(event, payment_status) and pagamento.status != "aprovado":
            transaction_id = payment.get("id") or pagamento.transaction_id
            pagamento.marcar_como_pago(
                transaction_id=str(transaction_id) if transaction_id else None,
                gateway_response=data,
            )

        return HttpResponse("OK", status=200)
    except Exception:
        logger.exception("Erro no webhook de pagamento (saas)")
        return HttpResponse("Erro interno", status=500)

def dashboard_saas(request):
    """Dashboard específico para gestão SaaS"""
    if not request.user.is_staff:
        return redirect('core:dashboard')
    
    context = {
        'total_tenants': Tenant.objects.count(),
        'tenants_ativos': Tenant.objects.filter(status='ativo').count(),
        'tenants_trial': Tenant.objects.filter(status='trial').count(),
        'tenants_suspensos': Tenant.objects.filter(status='suspenso').count(),
        'planos': PlanoComercial.objects.filter(ativo=True),
        'tenants_recentes': Tenant.objects.order_by('-data_criacao')[:10]
    }
    
    return render(request, 'saas/dashboard.html', context)

@require_http_methods(["POST"])
def processar_pagamento_plano(request):
    """Processa o pagamento de um plano selecionado"""
    try:
        plano_id = request.POST.get('plano_id')
        forma_pagamento = request.POST.get('forma_pagamento')
        
        if not plano_id or not forma_pagamento:
            return JsonResponse({
                'status': 'error',
                'message': 'Plano e forma de pagamento são obrigatórios'
            })
        
        # Verificar se o plano existe
        try:
            plano = PlanoComercial.objects.get(id=plano_id, ativo=True)
        except PlanoComercial.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Plano não encontrado'
            })
        
        # Verificar se o usuário está autenticado
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Usuário deve estar logado para processar pagamento'
            })
        
        # Verificar se o usuário já tem uma empresa/tenant criada
        try:
            tenant = Tenant.objects.get(usuario_admin=request.user)
            return JsonResponse({
                'status': 'error',
                'message': 'Você já possui uma empresa cadastrada. Acesse o dashboard para gerenciar sua assinatura.',
                'redirect_url': '/saas/dashboard/'
            })
        except Tenant.DoesNotExist:
            # Usuário não tem tenant, precisa criar conta primeiro
            return JsonResponse({
                'status': 'error',
                'message': 'Você precisa criar sua conta empresarial antes de assinar um plano.',
                'redirect_url': f'/saas/registro/?plano={plano_id}'
            })
        
        # Obter configuração de pagamento
        from pagamentos.models import ConfiguracaoPagamento
        config = ConfiguracaoPagamento.get_configuracao()
        
        if not config:
            return JsonResponse({
                'status': 'error',
                'message': 'Configuração de pagamento não encontrada'
            })
        
        # Verificar se a forma de pagamento está habilitada
        if forma_pagamento == 'pix' and not config.pix_habilitado:
            return JsonResponse({
                'status': 'error',
                'message': 'PIX não está habilitado'
            })
        elif forma_pagamento == 'cartao' and not config.cartao_habilitado:
            return JsonResponse({
                'status': 'error',
                'message': 'Cartão de crédito não está habilitado'
            })
        elif forma_pagamento == 'boleto' and not config.boleto_habilitado:
            return JsonResponse({
                'status': 'error',
                'message': 'Boleto não está habilitado'
            })
        
        # Criar registro de pagamento
        from .models import PagamentoPlano
        
        pagamento = PagamentoPlano.objects.create(
            plano=plano,
            valor=plano.preco_mensal,
            metodo_pagamento=forma_pagamento,
            status='pendente',
            email_pagador=request.user.email,
            nome_pagador=request.user.get_full_name() or request.user.username,
            telefone_pagador=request.POST.get('telefone', ''),
            documento_pagador=request.POST.get('documento', ''),
            descricao=f'Assinatura do plano {plano.nome}',
            metadata={
                'plano_id': plano.id,
                'user_id': request.user.id,
                'tipo': 'assinatura_plano'
            }
        )
        
        # Redirecionar para página de pagamento
        return JsonResponse({
            'status': 'success',
            'redirect_url': f'/saas/pagamento/{pagamento.token_pagamento}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erro interno: {str(e)}'
        })

class PagamentoPlanoView(TemplateView):
    """View para exibir a página de pagamento de planos"""
    template_name = 'saas/pagamento_plano.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')
        
        try:
            from .models import PagamentoPlano
            pagamento = get_object_or_404(PagamentoPlano, token_pagamento=token)
            
            # Verificar se o pagamento ainda é válido
            if pagamento.esta_expirado:
                pagamento.status = 'expirado'
                pagamento.save()
                context['erro'] = 'Este link de pagamento expirou.'
                return context
            
            if pagamento.status != 'pendente':
                context['erro'] = f'Este pagamento já foi {pagamento.get_status_display().lower()}.'
                return context
            
            # Buscar configurações
            from pagamentos.models import ConfiguracaoPagamento
            config = ConfiguracaoPagamento.get_configuracao()
            
            context.update({
                'pagamento': pagamento,
                'config': config,
                'plano': pagamento.plano,
            })
            
        except Exception as e:
            context['erro'] = f'Erro ao carregar pagamento: {str(e)}'
        
        return context

@require_http_methods(["POST"])
def processar_pagamento_plano_final(request, token):
    """Processa o pagamento final do plano"""
    try:
        from .models import PagamentoPlano
        pagamento = get_object_or_404(PagamentoPlano, token_pagamento=token)
        
        if not pagamento.pode_processar:
            return JsonResponse({
                'status': 'error',
                'message': 'Pagamento não pode ser processado'
            })

        metodo_pagamento = request.POST.get("metodo_pagamento") or pagamento.metodo_pagamento
        if metodo_pagamento not in {"pix", "cartao", "boleto"}:
            return JsonResponse({"status": "error", "message": "Forma de pagamento inválida"})

        if pagamento.metodo_pagamento != metodo_pagamento:
            pagamento.metodo_pagamento = metodo_pagamento
            pagamento.save(update_fields=["metodo_pagamento"])

        billing_type_map = {
            "pix": "PIX",
            "cartao": "CREDIT_CARD",
            "boleto": "BOLETO",
        }
        billing_type = billing_type_map[metodo_pagamento]

        checkout_url = (pagamento.metadata or {}).get("asaas_checkout_url")
        existing_billing_type = (pagamento.metadata or {}).get("asaas_billing_type")
        if not checkout_url or existing_billing_type != billing_type:
            checkout_url = _asaas_create_checkout_for_pagamento(request, pagamento, billing_type)

        return JsonResponse({
            'status': 'success',
            'message': 'Redirecionando para o checkout do Asaas',
            'redirect_url': checkout_url
        })
        
    except Exception as e:
        logger.exception("Erro ao processar pagamento final (saas)")
        return JsonResponse({
            'status': 'error',
            'message': f'Erro ao processar pagamento: {str(e)}'
        })

class EmailEnviadoView(TemplateView):
    """View para mostrar que o email de verificação foi enviado"""
    template_name = 'saas/email_enviado.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro_pendente = self.request.session.get('registro_pendente')
        if registro_pendente:
            context['email'] = registro_pendente.get('email')
        context['email_enviado'] = bool(self.request.session.get('email_verificacao_enviado', True))
        return context

def verificar_email(request, token):
    """View para verificar email através do token"""
    try:
        verificacao = VerificacaoEmail.objects.get(token=token)
        
        if verificacao.email_verificado:
            messages.info(request, 'Este email já foi verificado anteriormente.')
            return redirect('login')
        
        # Verificar email
        verificacao.verificar_email()
        
        tenant = Tenant.objects.filter(usuario_admin=verificacao.usuario).first()
        if tenant:
            request.session['tenant_id'] = tenant.id
            if tenant.plano_id:
                request.session['plano_selecionado'] = str(tenant.plano_id)

        pagamento_pendente = PagamentoPlano.objects.filter(
            usuario=verificacao.usuario,
            status='pendente'
        ).order_by('-data_criacao').first()
        if pagamento_pendente:
            request.session['pagamento_token'] = pagamento_pendente.token_pagamento

        # Obter informações do registro pendente
        registro_pendente = request.session.get('registro_pendente')

        if registro_pendente and registro_pendente.get('user_id') == verificacao.usuario.id:
            # Limpar sessão de registro pendente
            del request.session['registro_pendente']
        request.session.pop('email_verificacao_enviado', None)

        # O link de verificacao pode ser aberto em outro navegador/dispositivo.
        login(request, verificacao.usuario, backend='django.contrib.auth.backends.ModelBackend')

        if tenant:
            if tenant.status == 'ativo':
                messages.success(request, 'Email verificado com sucesso! Sua conta ja esta ativa.')
                return redirect('/dashboard/')

            messages.success(
                request,
                'Email verificado com sucesso! Agora voce pode escolher sua forma de pagamento.'
            )
            return redirect('saas:escolher_pagamento')

        messages.success(request, 'Email verificado com sucesso! Agora voce pode fazer login.')
        return redirect('login')
        
    except VerificacaoEmail.DoesNotExist:
        messages.error(request, 'Token de verificação inválido ou expirado.')
        return redirect('saas:planos')

def reenviar_email_verificacao(request):
    """View para reenviar email de verificação"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Email é obrigatório.')
            return redirect('saas:email_enviado')
        
        try:
            user = User.objects.get(email=email)
            verificacao = VerificacaoEmail.objects.get(usuario=user)
            
            if verificacao.email_verificado:
                messages.info(request, 'Este email já foi verificado.')
                return redirect('login')
            
            if not verificacao.pode_reenviar:
                messages.warning(
                    request, 
                    'Você só pode solicitar um novo email de verificação a cada hora. '
                    'Tente novamente mais tarde.'
                )
                return redirect('saas:email_enviado')
            
            # Gerar novo token e reenviar
            verificacao.gerar_novo_token()
            
            if verificacao.enviar_email_verificacao(request):
                messages.success(
                    request, 
                    f'Novo email de verificação enviado para {email}. '
                    f'Verifique sua caixa de entrada.'
                )
            else:
                messages.error(
                    request,
                    'Erro ao enviar email de verificação. Tente novamente mais tarde.'
                )
            
        except (User.DoesNotExist, VerificacaoEmail.DoesNotExist):
            messages.error(request, 'Email não encontrado ou não cadastrado.')
        
        return redirect('saas:email_enviado')
    
    return redirect('saas:planos')


def pagamento_pix_view(request, token):
    """View para exibir a página de pagamento PIX"""
    try:
        pagamento = get_object_or_404(PagamentoPlano, token_pagamento=token)

        checkout_url = (pagamento.metadata or {}).get("asaas_checkout_url")
        if checkout_url:
            return redirect(checkout_url)

        checkout_url = _asaas_create_checkout_for_pagamento(request, pagamento, "PIX")
        return redirect(checkout_url)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar pagamento PIX: {str(e)}')
        return redirect('saas:planos')


def verificar_pagamento_pix(request, token):
    """View para verificar status do pagamento PIX via AJAX"""
    try:
        pagamento = get_object_or_404(PagamentoPlano, token_pagamento=token)
        
        return JsonResponse({
            'status': pagamento.status,
            'message': 'Pagamento verificado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'erro',
            'message': f'Erro ao verificar pagamento: {str(e)}'
        }, status=400)
