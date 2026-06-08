#!/usr/bin/env python3
"""
Script para testar problemas com data URLs no navegador
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from notificacoes.models import TemplateNotificacao
from contratos.models import Contrato
from pagamentos.models import ConfiguracaoPagamento
from pagamentos.utils import gerar_codigo_pix_real, gerar_qr_code_pix
from django.template import Template, Context
import base64

def testar_data_url():
    print("🔍 TESTANDO DATA URL DO QR CODE PIX")
    print("=" * 60)
    
    try:
        # Buscar template
        template = TemplateNotificacao.objects.get(nome="Cobrança Banca de Feira - Email")
        print(f"✅ Template encontrado: {template.nome}")
        
        # Buscar contrato
        contrato = Contrato.objects.first()
        if not contrato:
            print("❌ Nenhum contrato de banca encontrado")
            return
        print(f"✅ Contrato encontrado: {contrato.numero}")
        
        # Buscar configuração PIX
        config_pix = ConfiguracaoPagamento.get_configuracao()
        if not config_pix or not config_pix.pix_habilitado:
            print("❌ PIX não está habilitado ou configurado")
            return
        print(f"✅ Configuração PIX encontrada: {config_pix.pix_chave}")
        
        # Gerar código PIX
        dados_pix = {
            'valor': 1050.00,
            'chave': config_pix.pix_chave,
            'nome_recebedor': config_pix.pix_nome_recebedor or "SISTEMA IMOBILIARIO",
            'cidade': "SAO PAULO",
            'identificador': "BANCA1"
        }
        codigo_pix = gerar_codigo_pix_real(dados_pix)
        print(f"✅ Código PIX gerado: {len(codigo_pix)} caracteres")
        
        # Gerar QR Code
        qr_code_base64 = gerar_qr_code_pix(codigo_pix)
        print(f"✅ QR Code gerado: {len(qr_code_base64)} caracteres")
        
        # Verificar se o base64 é válido
        try:
            decoded = base64.b64decode(qr_code_base64)
            print(f"✅ Base64 válido: {len(decoded)} bytes")
        except Exception as e:
            print(f"❌ Base64 inválido: {e}")
            return
        
        # Criar data URL completa
        data_url = f"data:image/png;base64,{qr_code_base64}"
        print(f"✅ Data URL criada: {len(data_url)} caracteres")
        
        # Verificar se há caracteres problemáticos
        problemas = []
        if '\n' in qr_code_base64:
            problemas.append("Quebras de linha encontradas")
        if '\r' in qr_code_base64:
            problemas.append("Retornos de carro encontrados")
        if ' ' in qr_code_base64:
            problemas.append("Espaços encontrados")
        if not qr_code_base64.replace('+', '').replace('/', '').replace('=', '').isalnum():
            problemas.append("Caracteres não-base64 encontrados")
        
        if problemas:
            print("⚠️  PROBLEMAS ENCONTRADOS:")
            for problema in problemas:
                print(f"   - {problema}")
        else:
            print("✅ Base64 limpo - sem caracteres problemáticos")
        
        # Criar HTML de teste
        html_teste = f"""<!DOCTYPE html>
<html>
<head>
    <title>Teste QR Code PIX</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Teste QR Code PIX</h1>
    
    <h2>Método 1: Data URL direta</h2>
    <img src="{data_url}" alt="QR Code PIX" style="border: 1px solid #ccc;">
    
    <h2>Método 2: Data URL via template Django</h2>
    <img src="data:image/png;base64,{qr_code_base64}" alt="QR Code PIX" style="border: 1px solid #ccc;">
    
    <h2>Informações de Debug</h2>
    <p><strong>Tamanho do base64:</strong> {len(qr_code_base64)} caracteres</p>
    <p><strong>Tamanho da data URL:</strong> {len(data_url)} caracteres</p>
    <p><strong>Primeiros 100 chars:</strong> {qr_code_base64[:100]}...</p>
    <p><strong>Últimos 100 chars:</strong> ...{qr_code_base64[-100:]}</p>
    
    <h2>Teste de JavaScript</h2>
    <script>
        console.log('Testando data URL...');
        const img = new Image();
        img.onload = function() {{
            console.log('✅ Imagem carregada com sucesso!');
            console.log('Dimensões:', this.width, 'x', this.height);
        }};
        img.onerror = function() {{
            console.error('❌ Erro ao carregar imagem!');
        }};
        img.src = "{data_url}";
    </script>
</body>
</html>"""
        
        # Salvar HTML de teste
        with open('teste_qrcode_browser.html', 'w', encoding='utf-8') as f:
            f.write(html_teste)
        
        print(f"📄 HTML de teste salvo em 'teste_qrcode_browser.html'")
        print(f"🌐 Abra o arquivo no navegador para testar")
        
        # Verificar se há problemas conhecidos
        print("\n🔍 VERIFICAÇÕES ADICIONAIS:")
        
        # Verificar tamanho da URL
        if len(data_url) > 2000000:  # 2MB
            print("⚠️  Data URL muito grande (>2MB) - pode causar problemas")
        else:
            print(f"✅ Tamanho da data URL OK: {len(data_url)/1024:.1f}KB")
        
        # Verificar se termina corretamente
        if qr_code_base64.endswith('=') or qr_code_base64.endswith('=='):
            print("✅ Base64 termina corretamente com padding")
        else:
            print("⚠️  Base64 pode estar truncado (sem padding)")
        
        print("\n✅ TESTE CONCLUÍDO")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_data_url()