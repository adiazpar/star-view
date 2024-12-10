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
    return reviews.aggregate(Avg('rating'))['rating_avg'] or 0