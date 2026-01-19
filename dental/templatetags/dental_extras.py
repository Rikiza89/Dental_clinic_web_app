# dental/templatetags/dental_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    try:
        # Convert key to int if it's a string number
        if isinstance(key, str) and key.isdigit():
            key = int(key)
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter"""
    return value.split(delimiter)