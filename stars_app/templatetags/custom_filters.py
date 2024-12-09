from django import template

register = template.Library()

@register.filter
def get_class(value):
    return value.__class__.__name__

@register.filter
def is_favorite(location, user):
    if user.is_authenticated:
        return location.favorited_by.filter(user=user).exists()
    return False