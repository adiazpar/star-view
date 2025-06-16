from django import template
from django.db.models import Avg

register = template.Library()

@register.filter
def get_class(value):
    return value.__class__.__name__

@register.filter
def is_favorite(location, user):
    if user.is_authenticated:
        return location.favorited_by.filter(user=user).exists()
    return False


@register.filter
def average_rating(reviews):
    # Calculate the average rating from a queryset of reviews:
    if not reviews:
        return 0
    # The aggregate function creates a key with _avg suffix
    result = reviews.aggregate(Avg('rating'))
    # Safely get the value with a default of 0
    return result.get('rating__avg', 0) or 0  # Note the double underscore

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary in templates"""
    return dictionary.get(str(key), 0) if dictionary else 0