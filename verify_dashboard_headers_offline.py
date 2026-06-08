#!/usr/bin/env python3
"""
Verifica offline a presença e visibilidade dos headers no dashboard
usando o HTML salvo (dashboard_authenticated.html) e os CSS locais.
"""

import os
import re
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, 'dashboard_authenticated.html')
CSS_CUSTOM_PATH = os.path.join(BASE_DIR, 'static', 'css', 'custom.css')
CSS_RESPONSIVE_PATH = os.path.join(BASE_DIR, 'static', 'css', 'responsive.css')


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Não foi possível ler '{path}': {e}")
        return ""


def contains_hidden_style(style_text: str) -> bool:
    if not style_text:
        return False
    s = style_text.replace(' ', '').lower()
    return any(token in s for token in ['display:none', 'visibility:hidden', 'opacity:0'])


def check_css_rules(css_text: str, selector: str) -> dict:
    result = {
        'found': False,
        'has_hidden': False,
        'samples': []
    }
    if not css_text:
        return result

    # Captura regras do seletor
    pattern = re.compile(rf"{re.escape(selector)}\s*\{{[^\}}]*\}}", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(css_text)
    if matches:
        result['found'] = True
        result['samples'] = matches[:3]
        for rule in matches:
            if contains_hidden_style(rule):
                result['has_hidden'] = True
                break
    return result


def main():
    print("== Verificação Offline de Headers do Dashboard ==")

    html = read_file(HTML_PATH)
    if not html:
        print("❌ HTML do dashboard não encontrado. Gere 'dashboard_authenticated.html' antes.")
        return

    soup = BeautifulSoup(html, 'html.parser')

    # Elementos principais
    sidebar_header = soup.find('header', class_='sidebar-header')
    navbar_header = soup.find('header', class_='navbar-header')
    sidebar = soup.find('aside', class_='sidebar')

    print(f"sidebar-header presente: {'✅' if sidebar_header else '❌'}")
    print(f"navbar-header presente: {'✅' if navbar_header else '❌'}")
    print(f"sidebar presente: {'✅' if sidebar else '❌'}")

    # Checar estilos inline
    if sidebar_header:
        inline = sidebar_header.get('style', '')
        print(f"sidebar-header inline style: {inline or '—'}")
        print("sidebar-header oculto por inline? ", "❌ NÃO" if not contains_hidden_style(inline) else "⚠️ SIM")

    if navbar_header:
        inline = navbar_header.get('style', '')
        print(f"navbar-header inline style: {inline or '—'}")
        print("navbar-header oculto por inline? ", "❌ NÃO" if not contains_hidden_style(inline) else "⚠️ SIM")

    if sidebar:
        inline = sidebar.get('style', '')
        print(f"sidebar inline style: {inline or '—'}")
        print("sidebar oculto por inline? ", "❌ NÃO" if not contains_hidden_style(inline) else "⚠️ SIM")

    # Ler CSS
    css_custom = read_file(CSS_CUSTOM_PATH)
    css_resp = read_file(CSS_RESPONSIVE_PATH)

    # Checar regras CSS
    for selector in ['.navbar-header', '.sidebar-header']:
        rules_custom = check_css_rules(css_custom, selector)
        rules_resp = check_css_rules(css_resp, selector)
        print(f"\nCSS para {selector}:")
        print(f"  custom.css encontrado: {'✅' if rules_custom['found'] else '❌'} | ocultação: {'⚠️ SIM' if rules_custom['has_hidden'] else '❌ NÃO'}")
        print(f"  responsive.css encontrado: {'✅' if rules_resp['found'] else '❌'} | ocultação: {'⚠️ SIM' if rules_resp['has_hidden'] else '❌ NÃO'}")
        if rules_custom['samples']:
            print("  Exemplo custom.css:")
            print(rules_custom['samples'][0][:200] + '...')
        if rules_resp['samples']:
            print("  Exemplo responsive.css:")
            print(rules_resp['samples'][0][:200] + '...')

    # Conclusão
    ok_headers = bool(sidebar_header) and bool(navbar_header)
    no_inline_hide = True
    for el in [sidebar_header, navbar_header, sidebar]:
        if el and contains_hidden_style(el.get('style', '')):
            no_inline_hide = False
            break

    css_ok = True
    for selector in ['.navbar-header', '.sidebar-header']:
        r1 = check_css_rules(css_custom, selector)
        r2 = check_css_rules(css_resp, selector)
        if r1['has_hidden'] or r2['has_hidden']:
            css_ok = False
            break

    print("\n== Resultado ==")
    if ok_headers and no_inline_hide and css_ok:
        print("✅ Headers presentes e sem ocultação por CSS/inline.")
    else:
        print("⚠️ Possível problema: ")
        print(f"  - Headers presentes? {'SIM' if ok_headers else 'NÃO'}")
        print(f"  - Ocultação inline? {'SIM' if not no_inline_hide else 'NÃO'}")
        print(f"  - Ocultação via CSS? {'SIM' if not css_ok else 'NÃO'}")


if __name__ == '__main__':
    main()