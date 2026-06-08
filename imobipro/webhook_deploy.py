#!/usr/bin/env python3
"""
Webhook para Deploy Automático
Sistema Imobiliário - ImobilPro

Este script recebe webhooks do GitHub/GitLab e executa deploy automático
"""

import os
import sys
import json
import hmac
import hashlib
import subprocess
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configurações
WEBHOOK_SECRET = "sistema_imo_webhook_secret_2024"  # Altere para uma chave segura
DEPLOY_SCRIPT = "/opt/sistema_imobiliario/deploy_automatico.sh"
LOG_FILE = "/var/log/webhook_deploy.log"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

def verify_signature(payload_body, secret_token, signature_header):
    """Verifica a assinatura do webhook para segurança"""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        secret_token.encode('utf-8'),
        payload_body,
        hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)

@app.route('/webhook/deploy', methods=['POST'])
def webhook_deploy():
    """Endpoint para receber webhooks e executar deploy"""
    
    try:
        # Verificar se é uma requisição POST
        if request.method != 'POST':
            return jsonify({'error': 'Método não permitido'}), 405
        
        # Obter dados do webhook
        payload = request.get_data()
        signature = request.headers.get('X-Hub-Signature-256')
        
        # Verificar assinatura (GitHub)
        if not verify_signature(payload, WEBHOOK_SECRET, signature):
            logging.warning("Assinatura inválida no webhook")
            return jsonify({'error': 'Assinatura inválida'}), 401
        
        # Parse do JSON
        data = json.loads(payload.decode('utf-8'))
        
        # Verificar se é um push para a branch main
        if 'ref' in data and data['ref'] == 'refs/heads/main':
            
            logging.info("🚀 Webhook recebido - Iniciando deploy automático")
            logging.info(f"Commit: {data.get('head_commit', {}).get('message', 'N/A')}")
            logging.info(f"Autor: {data.get('head_commit', {}).get('author', {}).get('name', 'N/A')}")
            
            # Executar script de deploy em background
            try:
                process = subprocess.Popen(
                    ['/bin/bash', DEPLOY_SCRIPT],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd='/opt/sistema_imobiliario'
                )
                
                logging.info(f"Deploy iniciado - PID: {process.pid}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Deploy iniciado com sucesso',
                    'timestamp': datetime.now().isoformat(),
                    'commit': data.get('head_commit', {}).get('id', 'N/A')[:7]
                }), 200
                
            except Exception as e:
                logging.error(f"Erro ao executar deploy: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Erro ao executar deploy: {str(e)}'
                }), 500
        
        else:
            logging.info("Webhook recebido mas não é para branch main - ignorando")
            return jsonify({
                'status': 'ignored',
                'message': 'Push não é para branch main'
            }), 200
    
    except json.JSONDecodeError:
        logging.error("Erro ao fazer parse do JSON do webhook")
        return jsonify({'error': 'JSON inválido'}), 400
    
    except Exception as e:
        logging.error(f"Erro inesperado no webhook: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Endpoint para verificar status do webhook"""
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/webhook/logs', methods=['GET'])
def webhook_logs():
    """Endpoint para visualizar logs recentes"""
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            # Retornar últimas 50 linhas
            recent_logs = lines[-50:] if len(lines) > 50 else lines
            
        return jsonify({
            'logs': recent_logs,
            'total_lines': len(lines)
        })
    
    except FileNotFoundError:
        return jsonify({'error': 'Arquivo de log não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Verificar se o script de deploy existe
    if not os.path.exists(DEPLOY_SCRIPT):
        logging.error(f"Script de deploy não encontrado: {DEPLOY_SCRIPT}")
        sys.exit(1)
    
    logging.info("🎯 Webhook de deploy iniciado")
    logging.info(f"Endpoint: http://localhost:5000/webhook/deploy")
    logging.info(f"Status: http://localhost:5000/webhook/status")
    
    # Executar em modo de produção
    app.run(host='0.0.0.0', port=5000, debug=False)