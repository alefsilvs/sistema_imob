#!/usr/bin/env python3
"""
Script para debugar especificamente o erro net::ERR_INVALID_URL do QR Code PIX
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
import re

def debug_qrcode_erro():
    print("🔍 DEBUG: ERRO net::ERR_INVALID_URL DO QR CODE PIX")
    print("=" * 60)
    
    try:
        # Simular exatamente o que acontece no comando verificar_vencimentos_bancas
        print("📋 SIMULANDO COMANDO VERIFICAR_VENCIMENTOS_BANCAS...")
        
        # Buscar template
        template = TemplateNotificacao.objects.get(nome="Cobrança Banca de Feira - Email")
        print(f"✅ Template: {template.nome}")
        
        # Buscar contrato
        contrato = Contrato.objects.first()
        print(f"✅ Contrato: {contrato.numero}")
        
        # Buscar configuração PIX (igual ao comando)
        config_pix = ConfiguracaoPagamento.get_configuracao()
        if not config_pix or not config_pix.pix_chave:
            print("❌ Configuração PIX não encontrada")
            return
        
        print(f"✅ Config PIX: {config_pix.pix_chave}")
        
        # Criar dados PIX exatamente como no comando
        dados_pix = {
            'chave': config_pix.pix_chave,
            'valor': 1050.00,
            'nome_recebedor': config_pix.pix_nome_recebedor or 'GESTAO FEIRA MUNICIPAL',
            'cidade': 'SAO PAULO',
            'identificador': 'BANCA1'
        }
        
        print(f"📊 Dados PIX: {dados_pix}")
        
        # Gerar código PIX
        codigo_pix = gerar_codigo_pix_real(dados_pix)
        print(f"✅ Código PIX: {len(codigo_pix)} chars")
        print(f"   Primeiros 50: {codigo_pix[:50]}...")
        
        # Gerar QR Code
        qr_code_base64 = gerar_qr_code_pix(codigo_pix)
        print(f"✅ QR Code Base64: {len(qr_code_base64)} chars")
        
        # VERIFICAÇÕES ESPECÍFICAS PARA O ERRO
        print("\n🔍 VERIFICAÇÕES ESPECÍFICAS:")
        
        # 1. Verificar se há caracteres inválidos
        invalid_chars = []
        for char in qr_code_base64:
            if not (char.isalnum() or char in '+/='):
                invalid_chars.append(char)
        
        if invalid_chars:
            print(f"❌ Caracteres inválidos encontrados: {set(invalid_chars)}")
        else:
            print("✅ Base64 contém apenas caracteres válidos")
        
        # 2. Verificar quebras de linha
        if '\n' in qr_code_base64 or '\r' in qr_code_base64:
            print("❌ Quebras de linha encontradas no base64")
            qr_code_base64_clean = qr_code_base64.replace('\n', '').replace('\r', '')
            print(f"🔧 Base64 limpo: {len(qr_code_base64_clean)} chars")
        else:
            print("✅ Sem quebras de linha no base64")
            qr_code_base64_clean = qr_code_base64
        
        # 3. Verificar padding
        if qr_code_base64_clean.endswith('=') or qr_code_base64_clean.endswith('=='):
            print("✅ Padding correto")
        else:
            print("⚠️  Sem padding - pode estar truncado")
        
        # 4. Testar decodificação
        try:
            decoded = base64.b64decode(qr_code_base64_clean)
            print(f"✅ Decodificação OK: {len(decoded)} bytes")
        except Exception as e:
            print(f"❌ Erro na decodificação: {e}")
            return
        
        # 5. Criar data URL e verificar tamanho
        data_url = f"data:image/png;base64,{qr_code_base64_clean}"
        print(f"✅ Data URL: {len(data_url)} chars")
        
        # 6. Verificar se excede limites do navegador
        if len(data_url) > 2000000:  # 2MB
            print("❌ Data URL muito grande (>2MB)")
        elif len(data_url) > 1000000:  # 1MB
            print("⚠️  Data URL grande (>1MB) - pode causar problemas")
        else:
            print("✅ Tamanho da data URL OK")
        
        # 7. Criar contexto como no comando
        contexto = {
            'contrato': contrato,
            'pix': {
                'codigo_pix': codigo_pix,
                'qr_code_base64': qr_code_base64_clean,
                'disponivel': True
            }
        }
        
        # 8. Renderizar template
        template_django = Template(template.corpo_template)
        context = Context(contexto)
        corpo_renderizado = template_django.render(context)
        
        print(f"✅ Template renderizado: {len(corpo_renderizado)} chars")
        
        # 9. Verificar se a data URL está correta no HTML
        data_url_pattern = r'data:image/png;base64,([A-Za-z0-9+/=]+)'
        matches = re.findall(data_url_pattern, corpo_renderizado)
        
        if matches:
            print(f"✅ {len(matches)} data URL(s) encontrada(s) no HTML")
            for i, match in enumerate(matches):
                print(f"   Data URL {i+1}: {len(match)} chars")
                if match != qr_code_base64_clean:
                    print(f"   ⚠️  Diferença detectada na data URL {i+1}")
        else:
            print("❌ Nenhuma data URL encontrada no HTML renderizado")
        
        # 10. Salvar HTML para teste
        html_debug = f"""<!DOCTYPE html>
<html>
<head>
    <title>Debug QR Code PIX</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .error {{ color: red; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
    </style>
</head>
<body>
    <h1>Debug QR Code PIX - Erro net::ERR_INVALID_URL</h1>
    
    <div class="test-section">
        <h2>Teste 1: Data URL Original</h2>
        <img src="{data_url}" alt="QR Code Original" style="border: 1px solid #ccc;">
        <p>Tamanho: {len(data_url)} caracteres</p>
    </div>
    
    <div class="test-section">
        <h2>Teste 2: Base64 Limpo</h2>
        <img src="data:image/png;base64,{qr_code_base64_clean}" alt="QR Code Limpo" style="border: 1px solid #ccc;">
        <p>Tamanho: {len(qr_code_base64_clean)} caracteres</p>
    </div>
    
    <div class="test-section">
        <h2>Teste 3: Template Renderizado</h2>
        <div style="border: 1px solid #eee; padding: 10px; max-height: 300px; overflow-y: auto;">
            {corpo_renderizado}
        </div>
    </div>
    
    <div class="test-section">
        <h2>Informações de Debug</h2>
        <ul>
            <li>Código PIX: {len(codigo_pix)} chars</li>
            <li>Base64: {len(qr_code_base64)} chars</li>
            <li>Base64 Limpo: {len(qr_code_base64_clean)} chars</li>
            <li>Data URL: {len(data_url)} chars</li>
            <li>HTML Renderizado: {len(corpo_renderizado)} chars</li>
        </ul>
    </div>
    
    <script>
        console.log('=== DEBUG QR CODE PIX ===');
        console.log('Data URL length:', {len(data_url)});
        console.log('Base64 length:', {len(qr_code_base64_clean)});
        
        // Testar carregamento da imagem
        const img = new Image();
        img.onload = function() {{
            console.log('✅ Imagem carregada com sucesso!');
            console.log('Dimensões:', this.width, 'x', this.height);
        }};
        img.onerror = function(e) {{
            console.error('❌ Erro ao carregar imagem:', e);
            console.error('Data URL:', "{data_url}".substring(0, 100) + "...");
        }};
        img.src = "{data_url}";
    </script>
</body>
</html>"""
        
        with open('debug_qrcode_erro.html', 'w', encoding='utf-8') as f:
            f.write(html_debug)
        
        print(f"📄 HTML de debug salvo em 'debug_qrcode_erro.html'")
        print(f"🌐 Abra no navegador e verifique o console para erros")
        
        # 11. Verificar se há problemas conhecidos
        print(f"\n📋 RESUMO DO DEBUG:")
        print(f"   • Código PIX: ✅ {len(codigo_pix)} chars")
        print(f"   • QR Code Base64: ✅ {len(qr_code_base64_clean)} chars")
        print(f"   • Data URL: ✅ {len(data_url)} chars")
        print(f"   • Template: ✅ Renderizado")
        print(f"   • HTML: ✅ {len(corpo_renderizado)} chars")
        
        if len(data_url) > 1000000:
            print(f"   ⚠️  ATENÇÃO: Data URL muito grande pode causar problemas")
        
        print(f"\n✅ DEBUG CONCLUÍDO - Verifique o arquivo HTML gerado")
        
    except Exception as e:
        print(f"❌ Erro durante o debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_qrcode_erro()