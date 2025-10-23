# ----------------------------------------------------------------------------------------------------- #
# This serializer_user.py file defines serializers for user-related models:                             #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST Framework serializers for transforming User and UserProfile models between Python       #
# objects and JSON for API responses. Handles user authentication data, profile information, and        #
# reputation metrics.                                                                                   #
#                                                                                                       #
# Key Features:                                                                                         #
# - UserSerializer: Core Django User model with nested profile data                                     #
# - UserProfileSerializer: Profile picture, reputation score, and contribution metrics                  #
# - Read-only reputation: Scores are calculated automatically and cannot be edited via API              #
# - Profile picture URLs: Provides absolute URLs for image display                                      #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from rest_framework import serializers
from django.contrib.auth.models import User
from stars_app.models.model_user_profile import UserProfile



# User Profile Serializer ---------------------------------------- #
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    profile_picture_url = serializers.ReadOnlyField(source='get_profile_picture_url')

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'profile_picture', 'profile_picture_url',
                  'reputation_score', 'verified_locations_count', 'helpful_reviews_count',
                  'quality_photos_count', 'is_trusted_contributor',
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'reputation_score', 'verified_locations_count',
                           'helpful_reviews_count', 'quality_photos_count',
                           'is_trusted_contributor', 'created_at', 'updated_at']


# User Serializer ------------------------------------------------ #
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['date_joined']
