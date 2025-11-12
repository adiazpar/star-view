# ----------------------------------------------------------------------------------------------------- #
# This model_user_badge.py file defines the UserBadge model:                                            #
#                                                                                                       #
# Purpose:                                                                                              #
# Junction table tracking which badges users have earned. Only stores earned badges (not in-progress    #
# or locked badges). Badge progress is calculated on-demand from source data to avoid sync issues.      #
#                                                                                                       #
# Key Features:                                                                                         #
# - Many-to-Many relationship between Users and Badges (through this model)                             #
# - Prevents duplicate badge awards with unique_together constraint                                     #
# - Automatic timestamp tracking (earned_at)                                                            #
# - Optimized storage (only earned badges, ~60% reduction vs storing all states)                        #
# - Pinned badges tracked in UserProfile.pinned_badge_ids (not here)                                    #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User


class UserBadge(models.Model):
    # user: The user who earned the badge
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='earned_badges',
        db_index=True
    )

    # badge: The badge that was earned
    badge = models.ForeignKey(
        'Badge',
        on_delete=models.CASCADE
    )

    # earned_at: When the user earned this badge
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent users from earning the same badge multiple times:
        unique_together = ['user', 'badge']
        # Order by most recently earned first:
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'earned_at']),
        ]
        verbose_name = 'User Badge'
        verbose_name_plural = 'User Badges'

    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.user.username} earned {self.badge.name}'
