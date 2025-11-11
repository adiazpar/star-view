# ----------------------------------------------------------------------------------------------------- #
# This model_follow.py file defines the Follow model:                                                   #
#                                                                                                       #
# Purpose:                                                                                              #
# Represents a user following another user in the social network. Enables users to follow other         #
# stargazers and see their activity, reviews, and location discoveries.                                 #
#                                                                                                       #
# Key Features:                                                                                         #
# - Many-to-Many relationship between Users (through this model)                                        #
# - Prevents duplicate follows with unique_together constraint                                          #
# - Prevents self-follows with clean() validation                                                       #
# - Automatic timestamp tracking (created_at)                                                           #
# - Indexed fields for efficient queries (follower, following)                                          #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Follow(models.Model):
    # follower: The user who is following someone
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        db_index=True
    )

    # following: The user who is being followed
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent users from following the same user multiple times:
        unique_together = ['follower', 'following']
        # Order by most recent follows first:
        ordering = ['-created_at']


    # Validation to prevent users from following themselves:
    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves.")


    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'
