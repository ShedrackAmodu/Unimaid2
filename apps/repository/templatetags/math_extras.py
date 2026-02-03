from django import template

register = template.Library()


@register.filter(name='sub')
def sub(value, arg):
    """Subtract `arg` from `value` in templates.

    Attempts integer subtraction first, falls back to float. Returns
    empty string on error to avoid raising TemplateSyntaxError.
    """
    try:
        # Try integer subtraction when inputs look like ints
        if isinstance(value, str) and value.isdigit() and isinstance(arg, str) and arg.isdigit():
            return int(value) - int(arg)

        if isinstance(value, (int,)) and isinstance(arg, (int,)):
            return value - arg

        # Fallback to floats
        v = float(value)
        a = float(arg)
        result = v - a
        # Return int when result is whole number
        if result.is_integer():
            return int(result)
        return result
    except Exception:
        return ''
