from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import ValidationError
from .model_location_review import LocationReview
import os
from uuid import uuid4
from PIL import Image
import io
import sys


def review_photo_path(instance, filename):
    """Generate unique path for review photos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('review_photos', str(instance.review.location.id), str(instance.review.id), filename)


def review_thumbnail_path(instance, filename):
    """Generate unique path for review photo thumbnails"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}_thumb.{ext}"
    return os.path.join('review_photos', str(instance.review.location.id), str(instance.review.id), 'thumbnails', filename)


class ReviewPhoto(models.Model):
    """Photos uploaded with location reviews"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    review = models.ForeignKey(
        LocationReview,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    image = models.ImageField(
        upload_to=review_photo_path,
        help_text="Photo for the review"
    )
    thumbnail = models.ImageField(
        upload_to=review_thumbnail_path,
        blank=True,
        null=True,
        help_text="Thumbnail version of the photo"
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for the photo"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of display (lower numbers appear first)"
    )
    
    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['review', 'order']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Photo {self.order + 1} for review by {self.review.user.username}"
    
    def clean(self):
        """Validate that review doesn't have more than 5 photos"""
        if self.review_id:
            existing_count = ReviewPhoto.objects.filter(
                review_id=self.review_id
            ).exclude(pk=self.pk).count()
            
            if existing_count >= 5:
                raise ValidationError("A review can have a maximum of 5 photos.")
    
    def save(self, *args, **kwargs):
        # Run validation
        self.full_clean()
        
        # Process image if it's new or changed
        if self.image and (not self.pk or 'image' in kwargs.get('update_fields', [])):
            self._process_image()
        
        # Auto-set order if not provided
        if self.order == 0 and self.review_id:
            max_order = ReviewPhoto.objects.filter(
                review_id=self.review_id
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        
        super().save(*args, **kwargs)
    
    def _process_image(self):
        """Process the uploaded image: create thumbnail and optimize"""
        try:
            # Open the image
            img = Image.open(self.image.file)
            
            # Convert to RGB if necessary (for PNG/RGBA images)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large (max 1920x1920 while maintaining aspect ratio)
            img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            
            # Save the resized image back
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=90, optimize=True)
            img_io.seek(0)
            
            # Reset the image file
            self.image.file.seek(0)
            self.image.file.truncate()
            self.image.file.write(img_io.getvalue())
            self.image.file.seek(0)
            
            # Create thumbnail
            self._create_thumbnail(img)
            
        except Exception as e:
            print(f"Error processing review image: {e}")
    
    def _create_thumbnail(self, img):
        """Create a thumbnail version of the image"""
        try:
            # Create thumbnail (300x300 max, maintaining aspect ratio)
            img_copy = img.copy()
            img_copy.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            thumb_io = io.BytesIO()
            img_copy.save(thumb_io, format='JPEG', quality=85, optimize=True)
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
            print(f"Error creating review thumbnail: {e}")
    
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