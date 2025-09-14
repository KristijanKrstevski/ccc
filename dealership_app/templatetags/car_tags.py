from django import template
from django.utils import translation

register = template.Library()

@register.filter
def get_fuel_display_lang(car, language=None):
    """Get fuel type display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_fuel_type_display_lang(language)
    except AttributeError:
        # Fallback to default display
        return car.get_fuel_type_display()

@register.filter
def get_transmission_display_lang(car, language=None):
    """Get transmission display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_transmission_display_lang(language)
    except AttributeError:
        return car.get_transmission_display()

@register.filter
def get_body_type_display_lang(car, language=None):
    """Get body type display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_body_type_display_lang(language)
    except AttributeError:
        return car.get_body_type_display()

@register.filter
def get_color_display_lang(car, language=None):
    """Get color display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_color_display_lang(language)
    except AttributeError:
        return car.get_color_display()

@register.filter
def get_seats_display_lang(car, language=None):
    """Get seats display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_seats_display_lang(language)
    except AttributeError:
        return car.get_seats_display()

@register.filter
def get_registration_display_lang(car, language=None):
    """Get registration display in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_registration_type_display_lang(language)
    except AttributeError:
        return car.get_registration_type_display()

@register.filter
def get_registered_badge_text(car, language=None):
    """Get registered badge text in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_registered_badge_text(language)
    except AttributeError:
        return "Регистрирано"

@register.filter
def get_serviced_badge_text(car, language=None):
    """Get serviced badge text in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_serviced_badge_text(language)
    except AttributeError:
        return "Сервисирано"

@register.filter
def get_promo_badge_text(car, language=None):
    """Get promo badge text in specified language"""
    if not language:
        language = translation.get_language()
    try:
        return car.get_promo_badge_text(language)
    except AttributeError:
        return "Промо цена"