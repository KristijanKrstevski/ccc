from django import template
import random

register = template.Library()

@register.simple_tag
def random_number(min_val, max_val):
    """Generate a random number between min_val and max_val (inclusive)"""
    try:
        return random.randint(int(min_val), int(max_val))
    except (ValueError, TypeError):
        return 1