from django.db import models
from django.contrib.auth.models import User
from .base import TimestampedModel
from .viewinglocation import ViewingLocation
import os
from uuid import uuid4


def location_photo_path(instance, filename):
    """Generate unique path for location photos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('location_photos', str(instance.location.id), filename)


class LocationPhoto(TimestampedModel):
    """Photos uploaded for viewing locations"""
    location = models.ForeignKey(
        ViewingLocation,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_photos'
    )
    image = models.ImageField(
        upload_to=location_photo_path,
        help_text="Photo of the viewing location"
    )
    caption = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional caption for the photo"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo shown in location listings"
    )
    is_approved = models.BooleanField(
        default=True,  # Auto-approve for now, can add moderation later
        help_text="Whether the photo has been approved by moderators"
    )
    
    # EXIF data (extracted from uploaded images)
    taken_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the photo was taken (from EXIF)"
    )
    camera_make = models.CharField(max_length=100, blank=True)
    camera_model = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['location', '-created_at']),
            models.Index(fields=['uploaded_by', '-created_at']),
            models.Index(fields=['is_approved', 'is_primary']),
        ]
    
    def __str__(self):
        return f"Photo for {self.location.name} by {self.uploaded_by.username}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary photo per location
        if self.is_primary:
            LocationPhoto.objects.filter(
                location=self.location,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @property
    def image_url(self):
        """Get the full URL for the image"""
        if self.image:
            return self.image.url
        return None