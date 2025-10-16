from django.db import models
from django.contrib.auth.models import User
from .model_location_review import LocationReview


class ReviewVote(models.Model):
    review = models.ForeignKey(
        LocationReview,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    is_upvote = models.BooleanField(
        help_text="True for upvote, False for downvote"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure one vote per user per review
        unique_together = ('user', 'review')

    def __str__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"{self.user.username}'s {vote_type} on {self.review}"
