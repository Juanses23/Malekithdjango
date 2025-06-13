from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if hasattr(dictionary, 'get'):
        return dictionary.get(id=key).descripcion_producto
    return dictionary[key] 

@register.filter(name='times')
def times(number):
    try:
        number = int(number)
        return range(1, number + 1)
    except (ValueError, TypeError):
        return range(0) 