# ----------------------------------------------------------------------------------------------------- #
# This serializer_favorite.py file defines serializers for favorite location functionality:             #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST Framework serializer for transforming FavoriteLocation models between Python objects    #
# and JSON. Handles user's collection of favorited stargazing locations with optional nicknames.        #
#                                                                                                       #
# Key Features:                                                                                         #
# - FavoriteLocationSerializer: Junction table between User and Location with nickname support          #
# - Nested location data: Includes full Location details for favorite lists                             #
# - Display name helper: Returns nickname if set, otherwise location name                               #
# - Write optimization: Accepts location_id for creation instead of nested object                       #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from rest_framework import serializers
from ..models import Location
from ..models import FavoriteLocation
from . import LocationSerializer



class FavoriteLocationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True
    )
    display_name = serializers.ReadOnlyField(source='get_display_name')

    class Meta:
        model = FavoriteLocation
        fields = ['id', 'user', 'location', 'location_id', 'nickname', 'display_name', 'created_at']
        read_only_fields = ['user', 'created_at']
