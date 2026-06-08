import requests
import sys

try:
    print("Testando conexão com o servidor...")
    r = requests.get('http://127.0.0.1:8000/dashboard/', timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type", "N/A")}')
    print(f'Content length: {len(r.text)}')
    
    # Verificar se há erros no HTML
    if 'error' in r.text.lower() or 'exception' in r.text.lower():
        print("ERRO ENCONTRADO NO HTML:")
        lines = r.text.split('\n')
        for i, line in enumerate(lines):
            if 'error' in line.lower() or 'exception' in line.lower():
                print(f"Linha {i+1}: {line.strip()}")
    
    # Verificar estrutura HTML básica
    if '<html' not in r.text:
        print("PROBLEMA: Tag HTML não encontrada")
    if '<head' not in r.text:
        print("PROBLEMA: Tag HEAD não encontrada")
    if '<body' not in r.text:
        print("PROBLEMA: Tag BODY não encontrada")
        
    print("\nPrimeiros 500 caracteres do HTML:")
    print(r.text[:500])
    
except requests.exceptions.ConnectionError:
    print("ERRO: Não foi possível conectar ao servidor Django")
    print("Verifique se o servidor está rodando em http://127.0.0.1:8000")
except Exception as e:
    print(f"ERRO: {str(e)}")