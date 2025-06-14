from django.db import models
from django.contrib.auth.models import User


class TimestampedModel(models.Model):
    """Abstract base model with created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedModel(TimestampedModel):
    """Abstract base model for user-owned content"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )

    class Meta:
        abstract = True


class LocationModel(models.Model):
    """Abstract base model for location-based content"""
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(
        help_text="Elevation in meters",
        default=0
    )

    class Meta:
        abstract = True


class RatableModel(models.Model):
    """Abstract base model for content that can be rated/reviewed"""
    rating_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text="Average rating (0.00-5.00)"
    )

    class Meta:
        abstract = True

    def update_rating_stats(self):
        """Update rating statistics from related reviews"""
        # This will be implemented by subclasses
        pass


class ViewingLocationBase(TimestampedModel, LocationModel, RatableModel):
    """Combined base class for ViewingLocation to avoid MRO issues"""
    
    class Meta:
        abstract = True


class CelestialEventBase(TimestampedModel, LocationModel):
    """Combined base class for CelestialEvent to avoid MRO issues"""
    
    class Meta:
        abstract = True