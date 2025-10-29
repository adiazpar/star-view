# ----------------------------------------------------------------------------------------------------- #
# This model_vote.py file defines the Vote model:                                                       #
#                                                                                                       #
# Purpose:                                                                                              #
# Generic voting system using Django's ContentTypes framework. Allows users to upvote or downvote any   #
# type of content with a single unified model and prevents duplicate votes.                             #
#                                                                                                       #
# Key Features:                                                                                         #
# - GenericForeignKey: Can point to any model (Review, ReviewComment, etc.)                             #
# - Vote types: Boolean field (True = upvote, False = downvote)                                         #
# - Unique constraint: Prevents users from voting multiple times on the same content                    #
# - Audit trail: Tracks who voted and when                                                              #
#                                                                                                       #
# ContentTypes Framework:                                                                               #
# Uses three fields to create generic relationships:                                                    #
# 1. content_type → Which model (e.g., "Review", "ReviewComment")                                       #
# 2. object_id → Specific instance ID                                                                   #
# 3. voted_object → Virtual field combining the above (GenericForeignKey)                               #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType



class Vote(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic relationship (ContentTypes framework):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, help_text="The type of object being voted on (e.g., Review, ReviewComment, etc.)")
    object_id = models.PositiveIntegerField(help_text="The ID of the specific object being voted on")
    voted_object = GenericForeignKey('content_type', 'object_id')  # Virtual field combining above

    # Vote data:
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes', help_text="The user who cast this vote")
    is_upvote = models.BooleanField(help_text="True for upvote, False for downvote")


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', '-created_at']),
        ]
        unique_together = ('user', 'content_type', 'object_id')  # One vote per user per object


    # Returns the model name of the voted object (e.g., 'review', 'reviewcomment'):
    @property
    def voted_object_type(self):
        if self.content_type:
            return self.content_type.model
        return None


    # String representation for admin interface and debugging:
    def __str__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        target = str(self.voted_object) if self.voted_object else f"{self.content_type.model if self.content_type else 'unknown'} #{self.object_id}"
        return f"{self.user.username}'s {vote_type} on {target}"
