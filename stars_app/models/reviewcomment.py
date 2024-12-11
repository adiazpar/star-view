from django.db import models
from django.contrib.auth.models import User
from .locationreview import LocationReview

class ReviewComment(models.Model):
    review = models.ForeignKey(
        LocationReview,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='review_comments'
    )
    content = models.TextField(
        max_length=500,
        help_text="Comment content"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.review}"