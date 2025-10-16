from django.db import models
from django.contrib.auth.models import User
from .model_review_comment import ReviewComment


class CommentVote(models.Model):
    """Model to track upvotes/downvotes on comments"""
    comment = models.ForeignKey(
        ReviewComment, 
        on_delete=models.CASCADE, 
        related_name='votes'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_votes'
    )
    is_upvote = models.BooleanField(
        help_text="True for upvote, False for downvote"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'comment')
        ordering = ['-created_at']
    
    def __str__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"{self.user.username} {vote_type} on comment {self.comment.id}"