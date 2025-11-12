# ----------------------------------------------------------------------------------------------------- #
# This model_review.py file defines the Review model:                                                   #
#                                                                                                       #
# Purpose:                                                                                              #
# Represents a user's review of a stargazing location with ratings, comments, and vote tracking.        #
# Automatically maintains aggregate rating statistics on the parent Location model.                     #
#                                                                                                       #
# Key Features:                                                                                         #
# - Rating validation: 1-5 star ratings enforced via validators                                         #
# - Unique constraint: One review per user per location                                                 #
# - Vote tracking: GenericRelation to Vote model for upvote/downvote functionality                      #
# - Automatic aggregation: Updates Location.rating_count and Location.average_rating on save/delete     #
# - Edit detection: Tracks whether review has been modified after creation                              #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.db.models import Avg
from django.contrib.contenttypes.fields import GenericRelation

# Import models:
from . import Location

# Import validators:
from starview_app.utils import sanitize_html



class Review(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships:
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_reviews')

    # Review data:
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Rating from 1 to 5 stars")
    comment = models.TextField(max_length=1000, blank=True, null=True, help_text="Optional review comment")

    # Generic relation to Vote model (enables upvote/downvote tracking):
    votes = GenericRelation('Vote', related_query_name='review')


    class Meta:
        unique_together = ('user', 'location')  # One review per user per location
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rating'], name='review_rating_idx'),
            models.Index(fields=['created_at'], name='review_created_idx'),
            models.Index(fields=['location'], name='review_location_idx'),
            models.Index(fields=['user'], name='review_user_idx'),
        ]
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'


    # String representation for admin interface and debugging:
    def __str__(self):
        return f"{self.user.username}'s review of {self.location.name}"


    # Returns the net vote score (upvotes minus downvotes):
    @property
    def vote_count(self):
        # Use prefetched votes if available to avoid database queries
        if hasattr(self, '_prefetched_objects_cache') and 'votes' in self._prefetched_objects_cache:
            votes_list = list(self.votes.all())
            upvotes = sum(1 for v in votes_list if v.is_upvote)
            downvotes = sum(1 for v in votes_list if not v.is_upvote)
            return upvotes - downvotes
        else:
            upvotes = self.votes.filter(is_upvote=True).count()
            downvotes = self.votes.filter(is_upvote=False).count()
            return upvotes - downvotes


    # Returns the total number of upvotes:
    @property
    def upvote_count(self):
        # Use prefetched votes if available to avoid database queries
        if hasattr(self, '_prefetched_objects_cache') and 'votes' in self._prefetched_objects_cache:
            votes_list = list(self.votes.all())
            return sum(1 for v in votes_list if v.is_upvote)
        else:
            return self.votes.filter(is_upvote=True).count()


    # Returns the total number of downvotes:
    @property
    def downvote_count(self):
        # Use prefetched votes if available to avoid database queries
        if hasattr(self, '_prefetched_objects_cache') and 'votes' in self._prefetched_objects_cache:
            votes_list = list(self.votes.all())
            return sum(1 for v in votes_list if not v.is_upvote)
        else:
            return self.votes.filter(is_upvote=False).count()


    # Checks if review was edited (updated_at > 10 seconds after created_at):
    @property
    def is_edited(self):
        from datetime import timedelta
        return self.updated_at - self.created_at > timedelta(seconds=10)


    # Validate review data before saving:
    def clean(self):
        from django.core.exceptions import ValidationError

        # Prevent users from reviewing their own locations
        if self.location.added_by == self.user:
            raise ValidationError(
                "You cannot review your own location. "
                "Reviews must be written by other users to maintain objectivity."
            )


    # Override save to sanitize HTML and update location rating statistics:
    def save(self, *args, **kwargs):
        # Run validation before saving
        self.full_clean()
        # Sanitize comment to prevent XSS attacks
        if self.comment:
            self.comment = sanitize_html(self.comment)

        is_new = self.pk is None
        old_rating = None

        if not is_new:
            old_review = Review.objects.get(pk=self.pk)
            old_rating = old_review.rating

        super().save(*args, **kwargs)
        self.update_location_ratings()


    # Override delete to automatically update location rating statistics:
    def delete(self, *args, **kwargs):
        location = self.location
        super().delete(*args, **kwargs)
        self.update_location_ratings(location=location)


    # Updates the parent location's rating_count and average_rating fields:
    def update_location_ratings(self, location=None):
        if location is None:
            location = self.location

        reviews = location.reviews.all()
        location.rating_count = reviews.count()

        if location.rating_count > 0:
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            location.average_rating = round(avg_rating, 2) if avg_rating else 0
        else:
            location.average_rating = 0

        location.save(update_fields=['rating_count', 'average_rating'])
