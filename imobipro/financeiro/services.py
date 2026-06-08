import requests
import json
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.core.files.base import ContentFile
from .models import NotaFiscal

logger = logging.getLogger('nfe')

class NFEServiceException(Exception):
    """Exceção personalizada para erros do serviço de NFe"""
    pass

class BaseNFEProvider:
    """Classe base para provedores de NFe"""
    
    def __init__(self):
        self.base_url = None
        self.token = None
        self.timeout = 30
    
    def emitir_nfe(self, nota_fiscal):
        """Método abstrato para emissão de NFe"""
        raise NotImplementedError
    
    def consultar_nfe(self, provider_id):
        """Método abstrato para consulta de NFe"""
        raise NotImplementedError
    
    def cancelar_nfe(self, provider_id, motivo):
        """Método abstrato para cancelamento de NFe"""
        raise NotImplementedError
    
    def download_pdf(self, provider_id):
        """Método abstrato para download de PDF"""
        raise NotImplementedError
    
    def download_xml(self, provider_id):
        """Método abstrato para download de XML"""
        raise NotImplementedError

class FocusNFEProvider(BaseNFEProvider):
    """Provedor Focus NFe"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.focusnfe.com.br"
        self.token = settings.FOCUS_NFE_TOKEN
        self.ambiente = settings.FOCUS_NFE_AMBIENTE  # 1 = produção, 2 = homologação
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição para a API Focus NFe"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição Focus NFe: {e}")
            raise NFEServiceException(f"Erro na comunicação com Focus NFe: {e}")
    
    def emitir_nfe(self, nota_fiscal):
        """Emite NFe via Focus NFe"""
        try:
            # Monta dados da NFe
            nfe_data = self._build_nfe_data(nota_fiscal)
            
            # Faz requisição para emissão
            endpoint = f"/v2/nfse?ref={nota_fiscal.numero}"
            response = self._make_request('POST', endpoint, nfe_data)
            
            # Atualiza nota fiscal com resposta
            nota_fiscal.provider_id = response.get('id')
            nota_fiscal.provider_response = json.dumps(response)
            nota_fiscal.chave_acesso = response.get('numero')
            nota_fiscal.protocolo_autorizacao = response.get('codigo_verificacao')
            
            if response.get('status') == 'autorizado':
                nota_fiscal.status = 'AUTORIZADA'
                nota_fiscal.data_autorizacao = datetime.now()
            else:
                nota_fiscal.status = 'PROCESSANDO'
            
            nota_fiscal.save()
            
            logger.info(f"NFe {nota_fiscal.numero} enviada para Focus NFe com sucesso")
            return response
            
        except Exception as e:
            nota_fiscal.ultimo_erro = str(e)
            nota_fiscal.tentativas_envio += 1
            nota_fiscal.save()
            logger.error(f"Erro ao emitir NFe {nota_fiscal.numero}: {e}")
            raise
    
    def _build_nfe_data(self, nota_fiscal):
        """Constrói dados da NFe para Focus NFe"""
        # Dados da empresa (prestador)
        prestador = {
            "cnpj": settings.NFE_EMPRESA_CNPJ,
            "inscricao_municipal": settings.NFE_EMPRESA_INSCRICAO_MUNICIPAL,
            "codigo_municipio": settings.NFE_EMPRESA_CODIGO_MUNICIPIO
        }
        
        # Dados do tomador (cliente)
        tomador = {
            "cnpj": nota_fiscal.cliente_cnpj or "",
            "cpf": nota_fiscal.cliente_cpf or "",
            "razao_social": nota_fiscal.cliente_nome,
            "endereco": {
                "logradouro": nota_fiscal.cliente_endereco or "",
                "numero": nota_fiscal.cliente_numero or "",
                "bairro": nota_fiscal.cliente_bairro or "",
                "codigo_municipio": nota_fiscal.cliente_codigo_municipio or settings.NFE_EMPRESA_CODIGO_MUNICIPIO,
                "cep": nota_fiscal.cliente_cep or "",
                "uf": nota_fiscal.cliente_uf or settings.NFE_EMPRESA_UF
            }
        }
        
        # Serviços
        servicos = [{
            "codigo_cnae": settings.NFE_CODIGO_CNAE,
            "discriminacao": nota_fiscal.discriminacao_servicos,
            "codigo_municipio": settings.NFE_EMPRESA_CODIGO_MUNICIPIO,
            "valor_servicos": str(nota_fiscal.valor_servicos),
            "iss_retido": False,
            "valor_iss": str(nota_fiscal.valor_iss)
        }]
        
        return {
            "data_emissao": nota_fiscal.data_emissao.strftime("%Y-%m-%dT%H:%M:%S"),
            "prestador": prestador,
            "tomador": tomador,
            "servicos": servicos,
            "valor_total": str(nota_fiscal.valor_total)
        }
    
    def consultar_nfe(self, provider_id):
        """Consulta status da NFe"""
        endpoint = f"/v2/nfse/{provider_id}"
        return self._make_request('GET', endpoint)
    
    def cancelar_nfe(self, provider_id, motivo):
        """Cancela NFe"""
        endpoint = f"/v2/nfse/{provider_id}"
        data = {"justificativa": motivo}
        return self._make_request('DELETE', endpoint, data)
    
    def download_pdf(self, provider_id):
        """Download PDF da NFe"""
        url = f"{self.base_url}/v2/nfse/{provider_id}.pdf"
        headers = {'Authorization': f'Token {self.token}'}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        return response.content
    
    def download_xml(self, provider_id):
        """Download XML da NFe"""
        url = f"{self.base_url}/v2/nfse/{provider_id}.xml"
        headers = {'Authorization': f'Token {self.token}'}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        return response.content

class WebmaniaNFEProvider(BaseNFEProvider):
    """Provedor WebMania NFe"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://webmaniabr.com/api/1/nfse"
        self.consumer_key = settings.WEBMANIA_CONSUMER_KEY
        self.consumer_secret = settings.WEBMANIA_CONSUMER_SECRET
        self.access_token = settings.WEBMANIA_ACCESS_TOKEN
        self.access_token_secret = settings.WEBMANIA_ACCESS_TOKEN_SECRET
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição para a API WebMania"""
        url = f"{self.base_url}{endpoint}"
        
        auth_data = {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret,
            'access_token': self.access_token,
            'access_token_secret': self.access_token_secret
        }
        
        if data:
            data.update(auth_data)
        else:
            data = auth_data
        
        try:
            if method == 'POST':
                response = requests.post(url, data=data, timeout=self.timeout)
            elif method == 'GET':
                response = requests.get(url, params=data, timeout=self.timeout)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição WebMania: {e}")
            raise NFEServiceException(f"Erro na comunicação com WebMania: {e}")
    
    def emitir_nfe(self, nota_fiscal):
        """Emite NFe via WebMania"""
        try:
            nfe_data = self._build_nfe_data(nota_fiscal)
            response = self._make_request('POST', '/emissao/', nfe_data)
            
            # Atualiza nota fiscal
            nota_fiscal.provider_id = response.get('nfse_id')
            nota_fiscal.provider_response = json.dumps(response)
            nota_fiscal.chave_acesso = response.get('numero_nfse')
            nota_fiscal.protocolo_autorizacao = response.get('codigo_verificacao')
            
            if response.get('status') == 'aprovado':
                nota_fiscal.status = 'AUTORIZADA'
                nota_fiscal.data_autorizacao = datetime.now()
            else:
                nota_fiscal.status = 'PROCESSANDO'
            
            nota_fiscal.save()
            
            logger.info(f"NFe {nota_fiscal.numero} enviada para WebMania com sucesso")
            return response
            
        except Exception as e:
            nota_fiscal.ultimo_erro = str(e)
            nota_fiscal.tentativas_envio += 1
            nota_fiscal.save()
            logger.error(f"Erro ao emitir NFe {nota_fiscal.numero}: {e}")
            raise
    
    def _build_nfe_data(self, nota_fiscal):
        """Constrói dados da NFe para WebMania"""
        return {
            'operacao': '1',  # Emissão
            'natureza_operacao': 'Prestação de serviços',
            'modelo': '1',  # NFS-e
            'finalidade': '1',  # Normal
            'ambiente': '2' if settings.DEBUG else '1',  # Homologação/Produção
            
            # Dados do cliente
            'cliente_nome': nota_fiscal.cliente_nome,
            'cliente_cpf': nota_fiscal.cliente_cpf or '',
            'cliente_cnpj': nota_fiscal.cliente_cnpj or '',
            'cliente_endereco': nota_fiscal.cliente_endereco or '',
            'cliente_numero': nota_fiscal.cliente_numero or '',
            'cliente_bairro': nota_fiscal.cliente_bairro or '',
            'cliente_cidade': nota_fiscal.cliente_cidade or '',
            'cliente_uf': nota_fiscal.cliente_uf or '',
            'cliente_cep': nota_fiscal.cliente_cep or '',
            
            # Dados do serviço
            'codigo_servico': settings.NFE_CODIGO_SERVICO,
            'discriminacao': nota_fiscal.discriminacao_servicos,
            'valor_servicos': str(nota_fiscal.valor_servicos),
            'valor_total': str(nota_fiscal.valor_total),
            'iss_retido': 'false',
            'valor_iss': str(nota_fiscal.valor_iss)
        }
    
    def consultar_nfe(self, provider_id):
        """Consulta NFe"""
        data = {'nfse_id': provider_id}
        return self._make_request('GET', '/consulta/', data)
    
    def cancelar_nfe(self, provider_id, motivo):
        """Cancela NFe"""
        data = {
            'nfse_id': provider_id,
            'motivo_cancelamento': motivo
        }
        return self._make_request('POST', '/cancelamento/', data)
    
    def download_pdf(self, provider_id):
        """Download PDF"""
        # WebMania retorna URL do PDF na consulta
        consulta = self.consultar_nfe(provider_id)
        pdf_url = consulta.get('url_pdf')
        
        if pdf_url:
            response = requests.get(pdf_url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        
        raise NFEServiceException("URL do PDF não encontrada")
    
    def download_xml(self, provider_id):
        """Download XML"""
        consulta = self.consultar_nfe(provider_id)
        xml_url = consulta.get('url_xml')
        
        if xml_url:
            response = requests.get(xml_url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        
        raise NFEServiceException("URL do XML não encontrada")

class NFEService:
    """Serviço principal para gerenciamento de NFe"""
    
    def __init__(self):
        self.provider = self._get_provider()
    
    def _get_provider(self):
        """Retorna o provedor ativo"""
        provider_name = settings.NFE_PROVIDER_ATIVO
        
        if provider_name == 'focus':
            return FocusNFEProvider()
        elif provider_name == 'webmania':
            return WebmaniaNFEProvider()
        else:
            raise NFEServiceException(f"Provedor '{provider_name}' não suportado")
    
    def emitir_nfe(self, nota_fiscal):
        """Emite NFe usando o provedor ativo"""
        try:
            logger.info(f"Iniciando emissão da NFe {nota_fiscal.numero}")
            
            # Valida dados antes do envio
            self._validar_dados_nfe(nota_fiscal)
            
            # Emite via provedor
            response = self.provider.emitir_nfe(nota_fiscal)
            
            # Tenta fazer download dos arquivos
            self._download_arquivos(nota_fiscal)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na emissão da NFe {nota_fiscal.numero}: {e}")
            raise
    
    def _validar_dados_nfe(self, nota_fiscal):
        """Valida dados obrigatórios da NFe"""
        erros = []
        
        if not nota_fiscal.cliente_nome:
            erros.append("Nome do cliente é obrigatório")
        
        if not nota_fiscal.cliente_cpf and not nota_fiscal.cliente_cnpj:
            erros.append("CPF ou CNPJ do cliente é obrigatório")
        
        if not nota_fiscal.discriminacao_servicos:
            erros.append("Discriminação dos serviços é obrigatória")
        
        if nota_fiscal.valor_servicos <= 0:
            erros.append("Valor dos serviços deve ser maior que zero")
        
        if erros:
            raise NFEServiceException("Dados inválidos: " + "; ".join(erros))
    
    def _download_arquivos(self, nota_fiscal):
        """Faz download dos arquivos PDF e XML"""
        if not nota_fiscal.provider_id:
            return
        
        try:
            # Download PDF
            pdf_content = self.provider.download_pdf(nota_fiscal.provider_id)
            if pdf_content:
                filename = f"nfe_{nota_fiscal.numero}.pdf"
                nota_fiscal.arquivo_pdf.save(filename, ContentFile(pdf_content))
            
            # Download XML
            xml_content = self.provider.download_xml(nota_fiscal.provider_id)
            if xml_content:
                filename = f"nfe_{nota_fiscal.numero}.xml"
                nota_fiscal.arquivo_xml.save(filename, ContentFile(xml_content))
                nota_fiscal.xml_content = xml_content.decode('utf-8')
            
            nota_fiscal.save()
            
        except Exception as e:
            logger.warning(f"Erro ao baixar arquivos da NFe {nota_fiscal.numero}: {e}")
    
    def consultar_status(self, nota_fiscal):
        """Consulta status atual da NFe"""
        if not nota_fiscal.provider_id:
            raise NFEServiceException("NFe não possui ID do provedor")
        
        try:
            response = self.provider.consultar_nfe(nota_fiscal.provider_id)
            
            # Atualiza status baseado na resposta
            self._atualizar_status_nfe(nota_fiscal, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao consultar NFe {nota_fiscal.numero}: {e}")
            raise
    
    def _atualizar_status_nfe(self, nota_fiscal, response):
        """Atualiza status da NFe baseado na resposta do provedor"""
        # Lógica específica para cada provedor
        if isinstance(self.provider, FocusNFEProvider):
            status = response.get('status')
            if status == 'autorizado':
                nota_fiscal.status = 'AUTORIZADA'
                nota_fiscal.data_autorizacao = datetime.now()
            elif status == 'cancelado':
                nota_fiscal.status = 'CANCELADA'
                nota_fiscal.data_cancelamento = datetime.now()
            elif status == 'erro':
                nota_fiscal.status = 'REJEITADA'
                nota_fiscal.ultimo_erro = response.get('mensagem_retorno', '')
        
        elif isinstance(self.provider, WebmaniaNFEProvider):
            status = response.get('status')
            if status == 'aprovado':
                nota_fiscal.status = 'AUTORIZADA'
                nota_fiscal.data_autorizacao = datetime.now()
            elif status == 'cancelado':
                nota_fiscal.status = 'CANCELADA'
                nota_fiscal.data_cancelamento = datetime.now()
            elif status == 'rejeitado':
                nota_fiscal.status = 'REJEITADA'
                nota_fiscal.ultimo_erro = response.get('motivo_rejeicao', '')
        
        nota_fiscal.save()
    
    def cancelar_nfe(self, nota_fiscal, motivo):
        """Cancela NFe"""
        if not nota_fiscal.provider_id:
            raise NFEServiceException("NFe não possui ID do provedor")
        
        if nota_fiscal.status != 'AUTORIZADA':
            raise NFEServiceException("Apenas NFe autorizadas podem ser canceladas")
        
        try:
            response = self.provider.cancelar_nfe(nota_fiscal.provider_id, motivo)
            
            nota_fiscal.status = 'CANCELADA'
            nota_fiscal.data_cancelamento = datetime.now()
            nota_fiscal.motivo_cancelamento = motivo
            nota_fiscal.save()
            
            logger.info(f"NFe {nota_fiscal.numero} cancelada com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"Erro ao cancelar NFe {nota_fiscal.numero}: {e}")
            raise
    
    def reenviar_email(self, nota_fiscal, email_destino):
        """Reenvia NFe por email"""
        # Esta funcionalidade depende do provedor
        # Por enquanto, implementaremos envio manual via Django
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        
        try:
            # Prepara anexos
            anexos = []
            
            if nota_fiscal.arquivo_pdf:
                anexos.append((f"NFe_{nota_fiscal.numero}.pdf", 
                             nota_fiscal.arquivo_pdf.read(), 
                             'application/pdf'))
            
            if nota_fiscal.arquivo_xml:
                anexos.append((f"NFe_{nota_fiscal.numero}.xml", 
                             nota_fiscal.arquivo_xml.read(), 
                             'application/xml'))
            
            # Monta email
            assunto = f"Nota Fiscal Eletrônica Nº {nota_fiscal.numero}"
            
            contexto = {
                'nota_fiscal': nota_fiscal,
                'empresa_nome': settings.NFE_EMPRESA_NOME
            }
            
            corpo = render_to_string('financeiro/emails/nfe_email.html', contexto)
            
            email = EmailMessage(
                subject=assunto,
                body=corpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destino]
            )
            
            email.content_subtype = 'html'
            
            # Adiciona anexos
            for nome, conteudo, tipo in anexos:
                email.attach(nome, conteudo, tipo)
            
            email.send()
            
            logger.info(f"NFe {nota_fiscal.numero} enviada por email para {email_destino}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar NFe {nota_fiscal.numero} por email: {e}")
            raise NFEServiceException(f"Erro ao enviar email: {e}")