from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtém um item de um dicionário usando uma chave"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiplica dois valores"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calcula a porcentagem"""
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0