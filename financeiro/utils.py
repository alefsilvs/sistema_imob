import hashlib
import random
from datetime import datetime
from django.conf import settings

class NFEUtils:
    """Utilitários para NFe"""
    
    @staticmethod
    def gerar_chave_acesso(nota_fiscal):
        """Gera chave de acesso da NFe seguindo padrão nacional"""
        # Código UF (2 dígitos)
        codigo_uf = getattr(settings, 'NFE_CODIGO_UF', '35')  # SP por padrão
        
        # Data de emissão (AAMM)
        data_emissao = nota_fiscal.data_emissao.strftime('%y%m')
        
        # CNPJ do emitente (14 dígitos)
        cnpj_emitente = settings.NFE_EMPRESA_CNPJ.replace('.', '').replace('/', '').replace('-', '')
        
        # Modelo (2 dígitos) - 99 para NFSe
        modelo = '99'
        
        # Série (3 dígitos)
        serie = str(nota_fiscal.serie).zfill(3)
        
        # Número da NFe (9 dígitos)
        numero = str(nota_fiscal.numero).zfill(9)
        
        # Tipo de emissão (1 dígito) - 1 = Normal
        tipo_emissao = '1'
        
        # Código numérico (8 dígitos) - Gerado aleatoriamente
        codigo_numerico = str(random.randint(10000000, 99999999))
        
        # Monta chave sem DV
        chave_sem_dv = (
            codigo_uf + data_emissao + cnpj_emitente + modelo + 
            serie + numero + tipo_emissao + codigo_numerico
        )
        
        # Calcula dígito verificador
        dv = NFEUtils._calcular_dv_chave_acesso(chave_sem_dv)
        
        # Chave completa
        chave_acesso = chave_sem_dv + str(dv)
        
        return chave_acesso
    
    @staticmethod
    def _calcular_dv_chave_acesso(chave):
        """Calcula dígito verificador da chave de acesso"""
        # Sequência de multiplicadores
        multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
        
        soma = 0
        multiplicador_index = 0
        
        # Percorre a chave de trás para frente
        for i in range(len(chave) - 1, -1, -1):
            soma += int(chave[i]) * multiplicadores[multiplicador_index]
            multiplicador_index = (multiplicador_index + 1) % len(multiplicadores)
        
        resto = soma % 11
        
        if resto < 2:
            return 0
        else:
            return 11 - resto
    
    @staticmethod
    def formatar_chave_acesso(chave):
        """Formata chave de acesso para exibição"""
        if not chave or len(chave) != 44:
            return chave
        
        # Formato: 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
        return ' '.join([chave[i:i+4] for i in range(0, len(chave), 4)])
    
    @staticmethod
    def validar_chave_acesso(chave):
        """Valida chave de acesso da NFe"""
        if not chave:
            return False
        
        # Remove espaços e formatação
        chave = chave.replace(' ', '').replace('-', '')
        
        # Deve ter 44 dígitos
        if len(chave) != 44 or not chave.isdigit():
            return False
        
        # Valida dígito verificador
        chave_sem_dv = chave[:43]
        dv_calculado = NFEUtils._calcular_dv_chave_acesso(chave_sem_dv)
        dv_informado = int(chave[43])
        
        return dv_calculado == dv_informado
    
    @staticmethod
    def gerar_codigo_verificacao():
        """Gera código de verificação para NFSe"""
        # Gera um hash MD5 baseado no timestamp atual
        timestamp = str(datetime.now().timestamp())
        hash_obj = hashlib.md5(timestamp.encode())
        return hash_obj.hexdigest()[:8].upper()
    
    @staticmethod
    def formatar_valor_monetario(valor):
        """Formata valor monetário para exibição"""
        if valor is None:
            return 'R$ 0,00'
        
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def validar_inscricao_municipal(inscricao):
        """Valida inscrição municipal"""
        if not inscricao:
            return False
        
        # Remove formatação
        inscricao = inscricao.replace('.', '').replace('-', '').replace('/', '')
        
        # Deve ter entre 6 e 15 dígitos
        if len(inscricao) < 6 or len(inscricao) > 15:
            return False
        
        # Deve conter apenas números
        return inscricao.isdigit()


from functools import wraps
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from .forms import ConfirmacaoSenhaForm


def requer_confirmacao_senha(template_confirmacao='financeiro/confirmar_senha.html'):
    """
    Decorator que exige confirmação de senha para operações críticas
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Se é POST e não tem confirmação de senha na sessão
            if request.method == 'POST':
                # Verifica se já foi confirmada a senha nesta sessão
                session_key = f'senha_confirmada_{request.user.id}_{view_func.__name__}'
                
                if not request.session.get(session_key, False):
                    # Se não foi confirmada, mostra formulário de confirmação
                    form = ConfirmacaoSenhaForm(user=request.user, data=request.POST)
                    
                    if 'confirmar_senha' in request.POST:
                        if form.is_valid():
                            # Senha confirmada, marca na sessão por 5 minutos
                            request.session[session_key] = True
                            request.session.set_expiry(300)  # 5 minutos
                            
                            # Remove o campo de confirmação do POST para não interferir na view original
                            post_data = request.POST.copy()
                            if 'confirmar_senha' in post_data:
                                del post_data['confirmar_senha']
                            if 'senha' in post_data:
                                del post_data['senha']
                            request.POST = post_data
                            
                            # Continua com a operação original
                            return view_func(request, *args, **kwargs)
                        else:
                            # Senha incorreta, mostra erro
                            messages.error(request, 'Senha incorreta. Operação cancelada.')
                            return redirect(request.META.get('HTTP_REFERER', '/'))
                    else:
                        # Primeira tentativa, mostra formulário de confirmação
                        context = {
                            'form': ConfirmacaoSenhaForm(user=request.user),
                            'operacao': view_func.__name__.replace('_', ' ').title(),
                            'post_data': request.POST,
                            'request_path': request.path,
                        }
                        return render(request, template_confirmacao, context)
                else:
                    # Senha já foi confirmada nesta sessão
                    return view_func(request, *args, **kwargs)
            else:
                # GET request, executa normalmente
                return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator