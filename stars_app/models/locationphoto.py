from django.db import models
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from .base import TimestampedModel
from .viewinglocation import ViewingLocation
import os
from uuid import uuid4
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import io
import sys
from datetime import datetime


def location_photo_path(instance, filename):
    """Generate unique path for location photos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('location_photos', str(instance.location.id), filename)


def location_thumbnail_path(instance, filename):
    """Generate unique path for location photo thumbnails"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}_thumb.{ext}"
    return os.path.join('location_photos', str(instance.location.id), 'thumbnails', filename)


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
    thumbnail = models.ImageField(
        upload_to=location_thumbnail_path,
        blank=True,
        null=True,
        help_text="Thumbnail version of the photo"
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
    camera_settings = models.JSONField(
        null=True,
        blank=True,
        help_text="Camera settings (ISO, aperture, shutter speed, etc.)"
    )
    
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
        
        # Process image if it's new or changed
        if self.image and (not self.pk or 'image' in kwargs.get('update_fields', [])):
            self._process_image()
        
        super().save(*args, **kwargs)
    
    def _process_image(self):
        """Process the uploaded image: extract EXIF data and create thumbnail"""
        try:
            # Open the image
            img = Image.open(self.image.file)
            
            # Extract EXIF data
            self._extract_exif_data(img)
            
            # Create thumbnail
            self._create_thumbnail(img)
            
        except Exception as e:
            print(f"Error processing image: {e}")
    
    def _extract_exif_data(self, img):
        """Extract EXIF data from image"""
        try:
            exif_data = img._getexif()
            if exif_data:
                camera_settings = {}
                
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'Make':
                        self.camera_make = str(value)[:100]
                    elif tag == 'Model':
                        self.camera_model = str(value)[:100]
                    elif tag == 'DateTime':
                        try:
                            self.taken_at = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                        except (ValueError, TypeError):
                            pass
                    elif tag in ['ISO', 'ISOSpeedRatings']:
                        camera_settings['iso'] = value
                    elif tag == 'FNumber':
                        camera_settings['aperture'] = f"f/{float(value):.1f}"
                    elif tag == 'ExposureTime':
                        if isinstance(value, tuple) and len(value) == 2:
                            shutter_speed = value[0] / value[1]
                            if shutter_speed < 1:
                                camera_settings['shutter_speed'] = f"1/{int(1/shutter_speed)}"
                            else:
                                camera_settings['shutter_speed'] = f"{shutter_speed:.1f}s"
                    elif tag == 'FocalLength':
                        if isinstance(value, tuple) and len(value) == 2:
                            focal_length = value[0] / value[1]
                            camera_settings['focal_length'] = f"{focal_length:.0f}mm"
                
                if camera_settings:
                    self.camera_settings = camera_settings
                    
        except Exception as e:
            print(f"Error extracting EXIF data: {e}")
    
    def _create_thumbnail(self, img):
        """Create a thumbnail version of the image"""
        try:
            # Convert to RGB if necessary (for PNG/RGBA images)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Create thumbnail (400x400 max, maintaining aspect ratio)
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Save to BytesIO with higher quality
            thumb_io = io.BytesIO()
            img.save(thumb_io, format='JPEG', quality=95, optimize=True)
            thumb_io.seek(0)
            
            # Generate filename
            original_name = os.path.basename(self.image.name)
            name_without_ext = os.path.splitext(original_name)[0]
            thumb_name = f"{name_without_ext}_thumb.jpg"
            
            # Create Django file
            thumb_file = InMemoryUploadedFile(
                thumb_io,
                None,
                thumb_name,
                'image/jpeg',
                sys.getsizeof(thumb_io),
                None
            )
            
            # Save thumbnail
            self.thumbnail.save(thumb_name, thumb_file, save=False)
            
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
    
    @property
    def image_url(self):
        """Get the full URL for the image"""
        if self.image:
            return self.image.url
        return None
    
    @property
    def thumbnail_url(self):
        """Get the full URL for the thumbnail"""
        if self.thumbnail:
            return self.thumbnail.url
        # Fallback to original image if no thumbnail
        return self.image_url