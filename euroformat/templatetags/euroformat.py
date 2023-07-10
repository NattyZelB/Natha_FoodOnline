from django import template
from babel.numbers import format_decimal

register = template.Library()

@register.filter
def euroformat(value):
    return format_decimal(value, locale='de_DE')