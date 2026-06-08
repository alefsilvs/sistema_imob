# -*- coding: utf-8 -*-
"""
Sistema de Proteção - ImobilPro
Copyright (c) 2024 - Todos os direitos reservados

Este módulo contém proteções contra uso não autorizado.
"""

import hashlib
import os
import sys
from datetime import datetime
import logging

# Configuração de logging para auditoria
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PROTECTION - %(message)s',
    handlers=[
        logging.FileHandler('protection.log'),
        logging.StreamHandler()
    ]
)

class SystemProtection:
    """
    Classe de proteção do sistema contra uso não autorizado.
    """
    
    COPYRIGHT_NOTICE = """
    ================================================================================
    SISTEMA IMOBILIÁRIO - IMOBILPRO
    Copyright (c) 2024 - Todos os direitos reservados
    
    AVISO LEGAL:
    Este software é propriedade exclusiva do autor.
    O uso não autorizado é crime previsto em lei.
    Violações serão processadas nos termos da legislação brasileira.
    ================================================================================
    """
    
    def __init__(self):
        self.system_hash = self._generate_system_hash()
        self.start_time = datetime.now()
        self._log_system_start()
    
    def _generate_system_hash(self):
        """Gera hash único do sistema para identificação."""
        try:
            # Combina informações do sistema para criar hash único
            system_info = f"{os.getcwd()}{sys.version}{datetime.now().strftime('%Y-%m')}"
            return hashlib.sha256(system_info.encode()).hexdigest()[:16]
        except Exception:
            return "UNKNOWN_SYSTEM"
    
    def _log_system_start(self):
        """Registra início do sistema para auditoria."""
        try:
            logging.info(f"Sistema iniciado - Hash: {self.system_hash}")
            logging.info(f"Diretório: {os.getcwd()}")
            logging.info(f"Python: {sys.version}")
            logging.info(f"Timestamp: {self.start_time}")
        except Exception:
            pass
    
    def display_copyright(self):
        """Exibe aviso de copyright."""
        print(self.COPYRIGHT_NOTICE)
    
    def verify_integrity(self):
        """Verifica integridade básica do sistema."""
        try:
            # Verifica se arquivos essenciais existem
            essential_files = [
                'LICENSE',
                'README.md',
                'manage.py',
                'sistema_imobiliario/settings.py'
            ]
            
            missing_files = []
            for file_path in essential_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                logging.warning(f"Arquivos essenciais ausentes: {missing_files}")
                return False
            
            return True
        except Exception as e:
            logging.error(f"Erro na verificação de integridade: {e}")
            return False
    
    def log_access(self, module_name, user_info=None):
        """Registra acesso a módulos do sistema."""
        try:
            access_info = f"Módulo acessado: {module_name}"
            if user_info:
                access_info += f" | Usuário: {user_info}"
            logging.info(access_info)
        except Exception:
            pass
    
    def get_license_info(self):
        """Retorna informações da licença."""
        return {
            'software': 'Sistema Imobiliário - ImobilPro',
            'copyright': '© 2024 - Todos os direitos reservados',
            'license_type': 'Proprietária',
            'commercial_use': 'Apenas com autorização expressa',
            'distribution': 'Proibida',
            'modification': 'Proibida',
            'reverse_engineering': 'Proibida',
            'legal_notice': 'Uso não autorizado é crime previsto em lei'
        }

# Instância global de proteção
_protection_instance = None

def get_protection_instance():
    """Retorna instância singleton de proteção."""
    global _protection_instance
    if _protection_instance is None:
        _protection_instance = SystemProtection()
    return _protection_instance

def init_protection():
    """Inicializa sistema de proteção."""
    protection = get_protection_instance()
    protection.display_copyright()
    
    if not protection.verify_integrity():
        print("\n⚠️  AVISO: Possível violação de integridade detectada!")
        print("📞 Entre em contato com o proprietário do software.")
    
    return protection

def log_module_access(module_name, user_info=None):
    """Função auxiliar para registrar acesso a módulos."""
    protection = get_protection_instance()
    protection.log_access(module_name, user_info)

# Proteção automática ao importar
if __name__ != '__main__':
    # Registra importação do módulo
    try:
        protection = get_protection_instance()
        protection.log_access('protection_module')
    except Exception:
        pass