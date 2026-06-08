import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class DataEncryption:
    """
    Classe para criptografia de dados sensíveis.
    Utiliza Fernet (AES 128) para criptografia simétrica.
    """
    
    def __init__(self):
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """
        Inicializa a criptografia com chave derivada da SECRET_KEY do Django.
        """
        try:
            # Usar SECRET_KEY do Django como base para derivar chave de criptografia
            secret_key = getattr(settings, 'SECRET_KEY', None)
            if not secret_key:
                raise ImproperlyConfigured("SECRET_KEY não configurada")
            
            # Derivar chave de criptografia usando PBKDF2
            salt = b'imobiliario_salt_2024'  # Salt fixo para consistência
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
            self._fernet = Fernet(key)
            
        except Exception as e:
            logger.error(f"Erro ao inicializar criptografia: {e}")
            raise
    
    def encrypt(self, data):
        """
        Criptografa dados sensíveis.
        
        Args:
            data (str): Dados a serem criptografados
            
        Returns:
            str: Dados criptografados em base64
        """
        if not data:
            return data
        
        try:
            # Converter para bytes se necessário
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Criptografar
            encrypted_data = self._fernet.encrypt(data_bytes)
            
            # Retornar como string base64
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            raise
    
    def decrypt(self, encrypted_data):
        """
        Descriptografa dados.
        
        Args:
            encrypted_data (str): Dados criptografados em base64
            
        Returns:
            str: Dados descriptografados
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            # Decodificar base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Descriptografar
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Retornar como string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            raise
    
    def encrypt_dict(self, data_dict, fields_to_encrypt):
        """
        Criptografa campos específicos de um dicionário.
        
        Args:
            data_dict (dict): Dicionário com dados
            fields_to_encrypt (list): Lista de campos a serem criptografados
            
        Returns:
            dict: Dicionário com campos criptografados
        """
        encrypted_dict = data_dict.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_dict and encrypted_dict[field]:
                encrypted_dict[field] = self.encrypt(encrypted_dict[field])
        
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict, fields_to_decrypt):
        """
        Descriptografa campos específicos de um dicionário.
        
        Args:
            encrypted_dict (dict): Dicionário com dados criptografados
            fields_to_decrypt (list): Lista de campos a serem descriptografados
            
        Returns:
            dict: Dicionário com campos descriptografados
        """
        decrypted_dict = encrypted_dict.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_dict and decrypted_dict[field]:
                try:
                    decrypted_dict[field] = self.decrypt(decrypted_dict[field])
                except Exception as e:
                    logger.warning(f"Erro ao descriptografar campo {field}: {e}")
                    # Manter valor original se não conseguir descriptografar
        
        return decrypted_dict

# Instância global para uso em todo o sistema
encryption = DataEncryption()

# Campos sensíveis que devem ser criptografados
SENSITIVE_FIELDS = {
    'cpf_cnpj',
    'rg_ie', 
    'conta',
    'agencia',
    'pix',
    'numero_apolice',
    'chave_acesso',
    'protocolo',
    'cliente_documento',
    'two_factor_secret',
    'backup_codes',
    'token',
    'inscricao_municipal',
    'matricula'
}

def encrypt_sensitive_data(data, fields=None):
    """
    Função utilitária para criptografar dados sensíveis.
    
    Args:
        data: Dados a serem criptografados (str ou dict)
        fields: Lista de campos a criptografar (para dict)
        
    Returns:
        Dados criptografados
    """
    if isinstance(data, dict):
        fields_to_encrypt = fields or SENSITIVE_FIELDS
        return encryption.encrypt_dict(data, fields_to_encrypt)
    else:
        return encryption.encrypt(data)

def decrypt_sensitive_data(encrypted_data, fields=None):
    """
    Função utilitária para descriptografar dados sensíveis.
    
    Args:
        encrypted_data: Dados criptografados (str ou dict)
        fields: Lista de campos a descriptografar (para dict)
        
    Returns:
        Dados descriptografados
    """
    if isinstance(encrypted_data, dict):
        fields_to_decrypt = fields or SENSITIVE_FIELDS
        return encryption.decrypt_dict(encrypted_data, fields_to_decrypt)
    else:
        return encryption.decrypt(encrypted_data)

def is_encrypted(data):
    """
    Verifica se os dados estão criptografados.
    
    Args:
        data (str): Dados a verificar
        
    Returns:
        bool: True se estiver criptografado
    """
    if not data or not isinstance(data, str):
        return False
    
    try:
        # Tentar decodificar base64
        base64.urlsafe_b64decode(data.encode('utf-8'))
        # Se conseguiu decodificar e tem tamanho típico de dados criptografados
        return len(data) > 50 and '=' in data[-3:]
    except:
        return False