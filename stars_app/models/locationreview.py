from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from .viewinglocation import ViewingLocation
from .base import TimestampedModel

class LocationReview(TimestampedModel):
    location = models.ForeignKey(
        ViewingLocation,
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