# ----------------------------------------------------------------------------------------------------- #
# This model_location_favorite.py file defines the FavoriteLocation model:                              #
#                                                                                                       #
# Purpose:                                                                                              #
# Represents a user's favorited stargazing location with optional custom nickname. Users can save       #
# locations they like for quick access and personalize them with nicknames.                             #
#                                                                                                       #
# Key Features:                                                                                         #
# - Many-to-Many relationship between Users and Locations (through this model)                          #
# - Optional nickname field for personalization                                                         #
# - Prevents duplicate favorites with unique_together constraint                                        #
# - Automatic timestamp tracking (created_at)                                                           #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User

# Import models:
from . import Location



class FavoriteLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='favorited_by')
    nickname = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent users from favoriting the same location multiple times:
        unique_together = ['user', 'location']


    # Returns the display name (nickname if set, otherwise location name).
    # Truncates to max_length characters if too long:
    def get_display_name(self, max_length=25):
        name = self.nickname if self.nickname else self.location.name
        if len(name) > max_length:
            return f"{name[:max_length]}..."
        return name


    # String representation for admin interface and debugging:
    def __str__(self):
        display_name = self.nickname if self.nickname else self.location.name
        return f'{self.user.username} - {display_name}'
