from django import template

register = template.Library()

@register.filter
def format_number(value):
    """Format number with comma thousand separators"""
    try:
        if value is None:
            return ""
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return value