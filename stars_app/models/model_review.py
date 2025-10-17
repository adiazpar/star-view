from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.db.models import Avg
from django.contrib.contenttypes.fields import GenericRelation
from .model_location import Location


class Review(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='location_reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Optional review comment"
    )

    # Generic relation to Vote model
    votes = GenericRelation('Vote', related_query_name='review')

    class Meta:
        # Ensure one review per user per location
        unique_together = ('user', 'location')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rating'], name='review_rating_idx'),
            models.Index(fields=['created_at'], name='review_created_idx'),
            models.Index(fields=['location'], name='review_location_idx'),
            models.Index(fields=['user'], name='review_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}'s review of {self.location.name}"

    @property
    def vote_count(self):
        """Returns the total vote score (upvotes - downvotes)"""
        upvotes = self.votes.filter(is_upvote=True).count()
        downvotes = self.votes.filter(is_upvote=False).count()
        return upvotes - downvotes

    @property
    def upvote_count(self):
        """Returns the number of upvotes"""
        return self.votes.filter(is_upvote=True).count()

    @property
    def downvote_count(self):
        """Returns the number of downvotes"""
        return self.votes.filter(is_upvote=False).count()
    
    @property
    def is_edited(self):
        """Check if the review has been edited"""
        # Consider it edited if updated_at is more than 10 seconds after created_at
        from datetime import timedelta
        return self.updated_at - self.created_at > timedelta(seconds=10)
    
    def save(self, *args, **kwargs):
        """Override save to update location rating statistics"""
        is_new = self.pk is None
        old_rating = None
        
        # If updating existing review, get the old rating
        if not is_new:
            old_review = Review.objects.get(pk=self.pk)
            old_rating = old_review.rating
        
        # Save the review
        super().save(*args, **kwargs)
        
        # Update location statistics
        self.update_location_ratings()
    
    def delete(self, *args, **kwargs):
        """Override delete to update location rating statistics"""
        location = self.location
        super().delete(*args, **kwargs)
        
        # Update location statistics after deletion
        self.update_location_ratings(location=location)
    
    def update_location_ratings(self, location=None):
        """Update the location's rating count and average"""
        if location is None:
            location = self.location
        
        # Get all reviews for this location
        reviews = location.reviews.all()
        
        # Update rating count
        location.rating_count = reviews.count()
        
        # Calculate and update average rating
        if location.rating_count > 0:
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            location.average_rating = round(avg_rating, 2) if avg_rating else 0
        else:
            location.average_rating = 0
        
        location.save(update_fields=['rating_count', 'average_rating'])
