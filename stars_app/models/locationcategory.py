from django.db import models
from django.contrib.auth.models import User
from .base import TimestampedModel


class LocationCategory(models.Model):
    """Pre-defined categories for viewing locations"""
    CATEGORY_CHOICES = [
        ('PARK', 'National/State Park'),
        ('MOUNTAIN', 'Mountain/Peak'),
        ('DESERT', 'Desert'),
        ('BEACH', 'Beach/Coast'),
        ('OBSERVATORY', 'Observatory'),
        ('RURAL', 'Rural Area'),
        ('SUBURBAN', 'Suburban Area'),
        ('CAMPGROUND', 'Campground'),
        ('FIELD', 'Open Field'),
        ('LAKE', 'Lake/Reservoir'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Category name"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly name"
    )
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        unique=True,
        help_text="Type of category"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of this category"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name or class for UI"
    )
    
    class Meta:
        verbose_name_plural = "Location Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LocationTag(TimestampedModel):
    """User-generated tags for viewing locations"""
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag name"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly name"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tags'
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of locations using this tag"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether this tag has been approved by moderators"
    )
    
    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['is_approved', '-usage_count']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def update_usage_count(self):
        """Update the usage count based on actual usage"""
        from .viewinglocation import ViewingLocation
        self.usage_count = ViewingLocation.objects.filter(tags=self).count()
        self.save()