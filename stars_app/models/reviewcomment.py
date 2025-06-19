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
    
    @property
    def upvote_count(self):
        """Get the number of upvotes for this comment"""
        return self.votes.filter(is_upvote=True).count()
    
    @property
    def downvote_count(self):
        """Get the number of downvotes for this comment"""
        return self.votes.filter(is_upvote=False).count()
    
    def get_user_vote(self, user):
        """Get the vote status for a specific user"""
        if not user.is_authenticated:
            return None
        
        try:
            vote = self.votes.get(user=user)
            return 'up' if vote.is_upvote else 'down'
        except:
            return None