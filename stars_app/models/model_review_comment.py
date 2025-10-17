from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from .model_location_review import LocationReview

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
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relation to Vote model
    votes = GenericRelation('Vote', related_query_name='comment')

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
    
    @property
    def is_edited(self):
        """Check if the comment has been edited"""
        # Consider it edited if updated_at is more than 10 seconds after created_at
        from datetime import timedelta
        return self.updated_at - self.created_at > timedelta(seconds=10)