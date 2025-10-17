from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Vote(models.Model):
    """
    Generic vote model that can handle upvotes/downvotes for ANY type of content.

    This model uses Django's ContentTypes framework with a GenericForeignKey
    to create a truly generic relationship. A Vote can point to any model:
    - LocationReview
    - ReviewComment
    - Or any future models you want to make votable (ViewingLocation, ReviewPhoto, etc.)

    The GenericForeignKey works by storing:
    1. content_type: Which model is being voted on (e.g., "LocationReview")
    2. object_id: The ID of that specific object
    3. voted_object: A virtual field that combines the above two
    """

    # ==================== TIMESTAMP FIELDS ====================
    created_at = models.DateTimeField(auto_now_add=True)


    # ==================== GENERIC RELATIONSHIP ====================
    # These three fields work together to create a generic relationship
    # that can point to ANY model in your Django project

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object being voted on (e.g., LocationReview, ReviewComment, etc.)"
    )

    object_id = models.PositiveIntegerField(
        help_text="The ID of the specific object being voted on"
    )

    voted_object = GenericForeignKey('content_type', 'object_id')
    # This is a virtual field that combines content_type + object_id
    # Usage: vote.voted_object will return the actual object (review/comment)


    # ==================== VOTE DATA FIELDS ====================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The user who cast this vote"
    )

    is_upvote = models.BooleanField(
        help_text="True for upvote, False for downvote"
    )


    # ==================== MODEL CONFIGURATION ====================

    class Meta:
        ordering = ['-created_at']

        # Database indexes for common queries
        indexes = [
            # Speed up queries filtering by voted object and user
            models.Index(fields=['content_type', 'object_id']),

            # Speed up queries for user's votes
            models.Index(fields=['user', '-created_at']),
        ]

        # Ensure one vote per user per object
        # This prevents a user from voting multiple times on the same thing
        unique_together = ('user', 'content_type', 'object_id')


    # ==================== HELPER PROPERTIES ====================

    @property
    def voted_object_type(self):
        """
        Returns a string indicating what type of object is being voted on.

        Returns:
            The model name as a string (e.g., 'locationreview', 'reviewcomment')

        Usage:
            if vote.voted_object_type == 'locationreview':
                # Handle review-specific logic
        """
        if self.content_type:
            return self.content_type.model
        return None


    # ==================== STRING REPRESENTATION ====================

    def __str__(self):
        """
        Human-readable string representation for admin interface and debugging.
        """
        vote_type = "upvote" if self.is_upvote else "downvote"

        if self.voted_object:
            target = str(self.voted_object)
        else:
            target = f"{self.content_type.model if self.content_type else 'unknown'} #{self.object_id}"

        return f"{self.user.username}'s {vote_type} on {target}"
