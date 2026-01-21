from django import template

register = template.Library()


@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        return value


@register.filter
def replace(value, arg):
    """Replace occurrences of old substring with new substring."""
    try:
        old, new = arg.split(',', 1)
        return value.replace(old.strip(), new.strip())
    except (ValueError, TypeError):
        return value
