from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import AssinaturaUsuario, ConfiguracaoSistema
from .pagamento_service import PagamentoService

class ControleAssinaturaMiddleware(MiddlewareMixin):
    """
    Middleware para controlar o acesso baseado na assinatura do usuário
    """
    
    # URLs que não precisam de verificação de assinatura
    URLS_LIBERADAS = [
        '/admin/',
        '/login/',
        '/logout/',
        '/assinaturas/',
        '/static/',
        '/media/',
        '/__debug__/',
    ]
    
    # URLs específicas que sempre são liberadas
    URLS_ESPECIFICAS_LIBERADAS = [
        '/',
        '/accounts/login/',
        '/accounts/logout/',
        '/assinaturas/planos/',
        '/assinaturas/assinar/',
        '/assinaturas/pagamento/',
        '/assinaturas/bloqueado/',
    ]
    
    def process_request(self, request):
        # Verificar se a URL atual precisa de verificação
        if self._url_liberada(request.path):
            return None
        
        # Verificar se o usuário está autenticado
        if isinstance(request.user, AnonymousUser):
            return None  # Usuário não autenticado, deixar o sistema de autenticação lidar
        
        # Verificar se o usuário tem acesso
        if not self._usuario_tem_acesso(request.user):
            messages.error(request, 'Sua assinatura expirou ou não foi encontrada. Escolha um plano para continuar.')
            return redirect('assinaturas:planos')
    
    def _usuario_tem_acesso(self, user):
        """
        Verifica se o usuário tem acesso ao sistema
        """
        # Superusuários sempre têm acesso
        if user.is_superuser:
            return True
        
        try:
            # Verificar se existe configuração do sistema
            config = ConfiguracaoSistema.objects.first()
            if not config or not config.bloquear_acesso_vencido:
                return True  # Sistema desabilitado, liberar acesso
            
            # Verificar assinatura do usuário
            assinatura = AssinaturaUsuario.objects.filter(
                usuario=user,
                status='ATIVA'
            ).first()
            
            if assinatura:
                # Verificar se a assinatura não expirou
                if assinatura.data_fim >= timezone.now().date():
                    return True
                else:
                    # Assinatura expirada, verificar período de graça
                    dias_graca = config.dias_graca or 0
                    if dias_graca > 0:
                        data_limite = assinatura.data_fim + timezone.timedelta(days=dias_graca)
                        if timezone.now().date() <= data_limite:
                            return True
                    
                    # Bloquear assinatura expirada
                    assinatura.status = 'EXPIRADA'
                    assinatura.save()
                    return False
            
            # Verificar se permite trial
            if config.permitir_trial:
                # Verificar se usuário já teve trial
                trial_anterior = AssinaturaUsuario.objects.filter(
                    usuario=user,
                    plano__tipo='TRIAL'
                ).exists()
                
                if not trial_anterior:
                    # Criar trial automático
                    from .models import PlanoAssinatura
                    plano_trial = PlanoAssinatura.objects.filter(
                        tipo='TRIAL',
                        ativo=True
                    ).first()
                    
                    if plano_trial:
                        AssinaturaUsuario.objects.create(
                            usuario=user,
                            plano=plano_trial,
                            data_inicio=timezone.now().date(),
                            data_fim=timezone.now().date() + timezone.timedelta(days=config.trial_dias),
                            status='ATIVA',
                            valor_pago=0,
                            forma_pagamento='TRIAL'
                        )
                        return True
            
            return False
            
        except Exception as e:
            # Em caso de erro, liberar acesso para não quebrar o sistema
            print(f"Erro no middleware de assinatura: {e}")
            return True
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Executado antes de cada view
        """
        # Verificar assinaturas vencidas periodicamente
        if request.user.is_authenticated and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            try:
                PagamentoService.verificar_assinaturas_vencidas()
            except Exception:
                pass  # Não quebrar o sistema se houver erro
        
        return None
        
        # Verificar se o usuário está autenticado
        if isinstance(request.user, AnonymousUser):
            return redirect('login')
        
        # Verificar se o usuário é superuser (admin)
        if request.user.is_superuser:
            return None
        
        # Verificar assinatura do usuário
        try:
            assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
            
            # Verificar se a assinatura está ativa
            if not assinatura.esta_ativa:
                # Verificar se ainda está no período de graça
                config = self._get_configuracao()
                if config and config.dias_graca > 0:
                    if assinatura.dias_restantes >= -config.dias_graca:
                        # Ainda no período de graça, apenas avisar
                        messages.warning(
                            request,
                            f'Sua assinatura expirou! Você tem {config.dias_graca + assinatura.dias_restantes} dias para renovar.'
                        )
                        return None
                
                # Assinatura expirada, bloquear acesso
                messages.error(request, 'Sua assinatura expirou. Renove para continuar usando o sistema.')
                return redirect('assinaturas:bloqueio_acesso')
            
            # Verificar se precisa renovar em breve
            if assinatura.precisa_renovar and assinatura.dias_restantes > 0:
                messages.warning(
                    request,
                    f'Sua assinatura expira em {assinatura.dias_restantes} dias. Renove agora para não perder o acesso!'
                )
        
        except AssinaturaUsuario.DoesNotExist:
            # Usuário sem assinatura
            config = self._get_configuracao()
            if config and config.permitir_trial:
                # Criar assinatura trial
                self._criar_trial(request.user)
                messages.info(request, f'Trial gratuito de {config.trial_dias} dias ativado!')
                return None
            else:
                # Não permite trial, bloquear
                messages.error(request, 'Você precisa de uma assinatura para acessar o sistema.')
                return redirect('assinaturas:planos')
        
        return None
    
    def _url_liberada(self, path):
        """Verifica se a URL está liberada da verificação de assinatura"""
        # Verificar URLs específicas
        if path in self.URLS_ESPECIFICAS_LIBERADAS:
            return True
        
        # Verificar URLs que começam com padrões liberados
        for url_liberada in self.URLS_LIBERADAS:
            if path.startswith(url_liberada):
                return True
        
        return False
    
    def _get_configuracao(self):
        """Obtém a configuração do sistema"""
        try:
            return ConfiguracaoSistema.objects.first()
        except:
            return None
    
    def _criar_trial(self, usuario):
        """Cria uma assinatura trial para o usuário"""
        from .models import PlanoAssinatura
        
        try:
            # Buscar plano trial ou criar um básico
            plano_trial, created = PlanoAssinatura.objects.get_or_create(
                tipo='TRIAL',
                defaults={
                    'nome': 'Trial Gratuito',
                    'descricao': 'Período de teste gratuito',
                    'preco': 0.00,
                    'duracao_dias': 7,
                    'max_imoveis': 5,
                    'max_contratos': 5,
                    'max_usuarios': 1,
                }
            )
            
            # Criar assinatura trial
            AssinaturaUsuario.objects.create(
                usuario=usuario,
                plano=plano_trial,
                status='TRIAL',
                valor_pago=0.00,
                forma_pagamento='Trial Gratuito'
            )
        
        except Exception as e:
            print(f'Erro ao criar trial: {e}')

class LimiteRecursosMiddleware(MiddlewareMixin):
    """
    Middleware para verificar limites de recursos baseado no plano
    """
    
    def process_request(self, request):
        # Só verificar para usuários autenticados
        if isinstance(request.user, AnonymousUser) or request.user.is_superuser:
            return None
        
        # Verificar apenas em URLs específicas
        if not self._deve_verificar_limite(request.path):
            return None
        
        try:
            assinatura = AssinaturaUsuario.objects.get(usuario=request.user)
            
            # Verificar limite de imóveis
            if '/imoveis/cadastrar' in request.path:
                if not self._verificar_limite_imoveis(assinatura):
                    messages.error(request, 'Limite de imóveis atingido para seu plano. Faça upgrade!')
                    return redirect('assinaturas:planos')
            
            # Verificar limite de contratos
            if '/contratos/cadastrar' in request.path:
                if not self._verificar_limite_contratos(assinatura):
                    messages.error(request, 'Limite de contratos atingido para seu plano. Faça upgrade!')
                    return redirect('assinaturas:planos')
        
        except AssinaturaUsuario.DoesNotExist:
            pass
        
        return None
    
    def _deve_verificar_limite(self, path):
        """Verifica se deve verificar limites para esta URL"""
        urls_verificar = [
            '/imoveis/cadastrar',
            '/contratos/cadastrar',
        ]
        
        for url in urls_verificar:
            if url in path:
                return True
        
        return False
    
    def _verificar_limite_imoveis(self, assinatura):
        """Verifica se o usuário pode cadastrar mais imóveis"""
        if assinatura.plano.max_imoveis == 0:  # Ilimitado
            return True
        
        from imoveis.models import Imovel
        total_imoveis = Imovel.objects.filter(proprietario=assinatura.usuario).count()
        
        return total_imoveis < assinatura.plano.max_imoveis
    
    def _verificar_limite_contratos(self, assinatura):
        """Verifica se o usuário pode cadastrar mais contratos"""
        if assinatura.plano.max_contratos == 0:  # Ilimitado
            return True
        
        from contratos.models import Contrato
        total_contratos = Contrato.objects.filter(
            imovel__proprietario=assinatura.usuario
        ).count()
        
        return total_contratos < assinatura.plano.max_contratos