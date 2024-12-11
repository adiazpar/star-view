from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from .viewinglocation import ViewingLocation

class LocationReview(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure one review per user per location
        unique_together = ('user', 'location')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review of {self.location.name}"

    @property
    def vote_count(self):
        """Returns the total vote score (upvotes - downvotes)"""
        upvotes = self.votes.filter(is_upvote=True).count()
        downvotes = self.votes.filter(is_upvote=False).count()
        return upvotes - downvotes