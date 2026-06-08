from django.db import models
from django.core.exceptions import ValidationError
from .encryption import encryption, is_encrypted
import logging

logger = logging.getLogger(__name__)

class EncryptedCharField(models.CharField):
    """
    Campo CharField que criptografa automaticamente os dados.
    """
    
    description = "Campo de texto criptografado"
    
    def __init__(self, *args, **kwargs):
        # Aumentar max_length para acomodar dados criptografados
        if 'max_length' in kwargs:
            kwargs['max_length'] = max(kwargs['max_length'] * 2, 255)
        else:
            kwargs['max_length'] = 255
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """
        Descriptografa o valor ao carregar do banco de dados.
        """
        if value is None:
            return value
        
        try:
            # Verificar se está criptografado
            if is_encrypted(value):
                return encryption.decrypt(value)
            else:
                # Dados não criptografados (migração ou dados antigos)
                return value
        except Exception as e:
            logger.warning(f"Erro ao descriptografar campo: {e}")
            return value
    
    def to_python(self, value):
        """
        Converte o valor para Python.
        """
        if value is None:
            return value
        
        # Se já está descriptografado, retornar como está
        if isinstance(value, str) and not is_encrypted(value):
            return value
        
        # Tentar descriptografar
        try:
            if is_encrypted(value):
                return encryption.decrypt(value)
            return value
        except Exception as e:
            logger.warning(f"Erro ao converter valor: {e}")
            return value
    
    def get_prep_value(self, value):
        """
        Criptografa o valor antes de salvar no banco.
        """
        if value is None or value == '':
            return value
        
        try:
            # Se já está criptografado, não criptografar novamente
            if is_encrypted(str(value)):
                return value
            
            # Criptografar o valor
            return encryption.encrypt(str(value))
        except Exception as e:
            logger.error(f"Erro ao criptografar valor: {e}")
            return value

class EncryptedTextField(models.TextField):
    """
    Campo TextField que criptografa automaticamente os dados.
    """
    
    description = "Campo de texto longo criptografado"
    
    def from_db_value(self, value, expression, connection):
        """
        Descriptografa o valor ao carregar do banco de dados.
        """
        if value is None:
            return value
        
        try:
            if is_encrypted(value):
                return encryption.decrypt(value)
            else:
                return value
        except Exception as e:
            logger.warning(f"Erro ao descriptografar campo de texto: {e}")
            return value
    
    def to_python(self, value):
        """
        Converte o valor para Python.
        """
        if value is None:
            return value
        
        if isinstance(value, str) and not is_encrypted(value):
            return value
        
        try:
            if is_encrypted(value):
                return encryption.decrypt(value)
            return value
        except Exception as e:
            logger.warning(f"Erro ao converter valor de texto: {e}")
            return value
    
    def get_prep_value(self, value):
        """
        Criptografa o valor antes de salvar no banco.
        """
        if value is None or value == '':
            return value
        
        try:
            if is_encrypted(str(value)):
                return value
            
            return encryption.encrypt(str(value))
        except Exception as e:
            logger.error(f"Erro ao criptografar valor de texto: {e}")
            return value

class EncryptedJSONField(models.JSONField):
    """
    Campo JSONField que criptografa automaticamente os dados.
    """
    
    description = "Campo JSON criptografado"
    
    def from_db_value(self, value, expression, connection):
        """
        Descriptografa o valor JSON ao carregar do banco de dados.
        """
        if value is None:
            return value
        
        try:
            # Se é string, pode estar criptografado
            if isinstance(value, str) and is_encrypted(value):
                decrypted = encryption.decrypt(value)
                import json
                return json.loads(decrypted)
            
            # Se já é dict/list, retornar como está
            return value
        except Exception as e:
            logger.warning(f"Erro ao descriptografar campo JSON: {e}")
            return value
    
    def to_python(self, value):
        """
        Converte o valor para Python.
        """
        if value is None:
            return value
        
        # Se já é dict/list, retornar como está
        if isinstance(value, (dict, list)):
            return value
        
        try:
            if isinstance(value, str) and is_encrypted(value):
                decrypted = encryption.decrypt(value)
                import json
                return json.loads(decrypted)
            
            # Tentar fazer parse JSON normal
            import json
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Erro ao converter valor JSON: {e}")
            return value
    
    def get_prep_value(self, value):
        """
        Criptografa o valor JSON antes de salvar no banco.
        """
        if value is None:
            return value
        
        try:
            import json
            
            # Se já é string criptografada, retornar como está
            if isinstance(value, str) and is_encrypted(value):
                return value
            
            # Converter para JSON e criptografar
            json_str = json.dumps(value, ensure_ascii=False)
            return encryption.encrypt(json_str)
        except Exception as e:
            logger.error(f"Erro ao criptografar valor JSON: {e}")
            return value

class CPFCNPJField(EncryptedCharField):
    """
    Campo específico para CPF/CNPJ com validação e criptografia.
    """
    
    description = "Campo CPF/CNPJ criptografado"
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255  # Espaço para criptografia
        super().__init__(*args, **kwargs)
    
    def validate(self, value, model_instance):
        """
        Valida CPF/CNPJ antes de salvar.
        """
        super().validate(value, model_instance)
        
        if value:
            # Remover formatação
            clean_value = ''.join(filter(str.isdigit, str(value)))
            
            # Validar tamanho
            if len(clean_value) not in [11, 14]:
                raise ValidationError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
            
            # Validar CPF
            if len(clean_value) == 11:
                if not self._validate_cpf(clean_value):
                    raise ValidationError('CPF inválido.')
            
            # Validar CNPJ
            elif len(clean_value) == 14:
                if not self._validate_cnpj(clean_value):
                    raise ValidationError('CNPJ inválido.')
    
    def _validate_cpf(self, cpf):
        """
        Valida CPF usando algoritmo oficial.
        """
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Calcular primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcular segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        return cpf[-2:] == f"{digit1}{digit2}"
    
    def _validate_cnpj(self, cnpj):
        """
        Valida CNPJ usando algoritmo oficial.
        """
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Calcular primeiro dígito verificador
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcular segundo dígito verificador
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        return cnpj[-2:] == f"{digit1}{digit2}"