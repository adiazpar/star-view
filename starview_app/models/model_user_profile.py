# ----------------------------------------------------------------------------------------------------- #
# This model_user_profile.py file defines the UserProfile model:                                        #
#                                                                                                       #
# Purpose:                                                                                              #
# Extends Django's built-in User model with profile pictures, bio, and location. Automatically created  #
# via post_save signal in signals.py when a User is created.                                            #
#                                                                                                       #
# Key Features:                                                                                         #
# - One-to-One relationship with User model (extends user functionality)                                #
# - Profile picture upload with default fallback                                                        #
# - Public profile fields: bio and location for user profiles                                           #
# - Automatic creation: Signal handler in signals.py creates UserProfile when User is created           #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings



class UserProfile(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User relationship:
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Profile data:
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(
        max_length=500,
        blank=True,
        default='',
        help_text="Short bio visible on public profile (max 500 characters)"
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="User's location (e.g., 'Seattle, WA')"
    )


    # Returns profile picture URL or default if none set:
    @property
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE


    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.user.username} Profile'
