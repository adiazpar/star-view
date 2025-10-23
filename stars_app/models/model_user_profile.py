# ----------------------------------------------------------------------------------------------------- #
# This model_user_profile.py file defines the UserProfile model:                                        #
#                                                                                                       #
# Purpose:                                                                                              #
# Extends Django's built-in User model with profile pictures and reputation tracking. Automatically     #
# created via post_save signal in signals.py when a User is created.                                    #
#                                                                                                       #
# Key Features:                                                                                         #
# - One-to-One relationship with User model (extends user functionality)                                #
# - Profile picture upload with default fallback                                                        #
# - Reputation system: Tracks scores, verified locations, helpful reviews, and contributor status       #
# - Automatic creation: Signal handler in signals.py creates UserProfile when User is created           #
#                                                                                                       #
# Note: Reputation fields are currently placeholders (always 0/False). Calculate and update manually    #
# as needed for your reputation system implementation.                                                  #
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

    # Reputation fields (currently placeholders - manually update as needed):
    reputation_score = models.IntegerField(default=0, help_text="User's reputation score based on contributions")
    verified_locations_count = models.IntegerField(default=0, help_text="Number of locations verified by this user")
    helpful_reviews_count = models.IntegerField(default=0, help_text="Number of helpful reviews (based on votes)")
    quality_photos_count = models.IntegerField(default=0, help_text="Number of approved photos uploaded")
    is_trusted_contributor = models.BooleanField(default=False, help_text="Whether user is a trusted contributor")


    # Returns profile picture URL or default if none set:
    @property
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE


    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.user.username} Profile'
