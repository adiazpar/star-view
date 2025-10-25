# ----------------------------------------------------------------------------------------------------- #
# This model_review_comment.py file defines the ReviewComment model:                                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Represents user comments on reviews, creating discussion threads. Users can comment on reviews and    #
# vote on comments, enabling community engagement and discussion about stargazing locations.            #
#                                                                                                       #
# Key Features:                                                                                         #
# - Threaded discussion: Comments belong to reviews                                                     #
# - Vote tracking: GenericRelation to Vote model for upvote/downvote functionality                      #
# - Edit detection: Tracks whether comment has been modified after creation                             #
# - User vote lookup: Method to check how a specific user voted on a comment                            #
# - Character limit: 500 character maximum to encourage concise discussion                              #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation

# Import models:
from . import Review

# Import validators:
from stars_app.utils import sanitize_html



class ReviewComment(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships:
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_comments')

    # Comment data:
    content = models.TextField(max_length=500, help_text="Comment content")

    # Generic relation to Vote model (enables upvote/downvote tracking):
    votes = GenericRelation('Vote', related_query_name='comment')


    class Meta:
        ordering = ['created_at']


    # String representation for admin interface and debugging:
    def __str__(self):
        return f"Comment by {self.user.username} on {self.review}"


    # Returns the total number of upvotes:
    @property
    def upvote_count(self):
        return self.votes.filter(is_upvote=True).count()


    # Returns the total number of downvotes:
    @property
    def downvote_count(self):
        return self.votes.filter(is_upvote=False).count()


    # Returns how a specific user voted ('up', 'down', or None):
    def get_user_vote(self, user):
        if not user.is_authenticated:
            return None

        try:
            vote = self.votes.get(user=user)
            return 'up' if vote.is_upvote else 'down'
        except:
            return None


    # Checks if comment was edited (updated_at > 10 seconds after created_at):
    @property
    def is_edited(self):
        from datetime import timedelta
        return self.updated_at - self.created_at > timedelta(seconds=10)


    # Override save to sanitize HTML content:
    def save(self, *args, **kwargs):
        # Sanitize content to prevent XSS attacks
        if self.content:
            self.content = sanitize_html(self.content)

        super().save(*args, **kwargs)