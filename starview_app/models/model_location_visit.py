# ----------------------------------------------------------------------------------------------------- #
# This model_location_visit.py file defines the LocationVisit model:                                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Tracks user check-ins to stargazing locations for badge progress and engagement tracking. Separate    #
# from FavoriteLocation (favorites = bookmarks, visits = been there). Enables the badge system to       #
# reward users for exploring new locations.                                                             #
#                                                                                                       #
# Key Features:                                                                                         #
# - Many-to-Many relationship between Users and Locations (through this model)                          #
# - Prevents duplicate visits with unique_together constraint (one visit per location)                  #
# - Automatic timestamp tracking (visited_at)                                                           #
# - Indexed fields for efficient badge checking and anomaly detection                                   #
# - Honor system - users self-report visits via "Mark as Visited" button                                #
# - Auto-created when user submits review (review implies visit)                                        #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User


class LocationVisit(models.Model):
    # user: The user who visited the location
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='location_visits',
        db_index=True
    )

    # location: The location that was visited
    location = models.ForeignKey(
        'Location',
        on_delete=models.CASCADE,
        related_name='visits'
    )

    # visited_at: When the user marked this location as visited
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        # Prevent users from visiting the same location multiple times:
        unique_together = ['user', 'location']
        # Order by most recent visits first:
        ordering = ['-visited_at']
        # Index for anomaly detection (rapid check-ins):
        indexes = [
            models.Index(fields=['user', 'visited_at']),
        ]
        verbose_name = 'Location Visit'
        verbose_name_plural = 'Location Visits'

    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.user.username} visited {self.location.name}'
