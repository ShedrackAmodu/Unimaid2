from django import template
from urllib.parse import parse_qs, urlencode

register = template.Library()


@register.filter
def remove_param(query_string, param_to_remove):
    """
    Remove a specific parameter from a query string.

    Args:
        query_string: The query string (e.g., 'q=test&genre=1&author=2')
        param_to_remove: The parameter name to remove (e.g., 'q')

    Returns:
        Updated query string with the parameter removed
    """
    if not query_string:
        return ''

    # Parse the query string into a dictionary
    params = parse_qs(query_string, keep_blank_values=True)

    # Remove the specified parameter if it exists
    if param_to_remove in params:
        del params[param_to_remove]

    # Reconstruct the query string
    return urlencode(params, doseq=True)


@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        return value


@register.filter
def multiply(value, arg):
    """Multiply the value by the arg."""
    try:
        return value * arg
    except (ValueError, TypeError):
        return value


@register.filter(name='getattr')
def get_attr(obj, attr):
    """Get an attribute from an object dynamically."""
    return getattr(obj, attr, None)
