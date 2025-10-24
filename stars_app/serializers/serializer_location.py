# ----------------------------------------------------------------------------------------------------- #
# This serializer_location.py file defines serializers for location-related models:                     #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST Framework serializers for transforming Location models between Python objects and       #
# JSON. Includes optimized serializers for different use cases (full details, map markers, info panel). #
#                                                                                                       #
# Key Features:                                                                                         #
# - LocationSerializer: Full location data with reviews, ratings, and user-specific context             #
# - MapLocationSerializer: Lightweight (97% reduction) for map marker display only                      #
# - LocationInfoPanelSerializer: Optimized (95% reduction) for map info panel clicks                    #
# - Performance optimization: Different serializers for different UI needs                              #
# - User context: Includes authenticated user's favorite status                                         #
#                                                                                                       #
# Performance Impact:                                                                                   #
# - Full LocationSerializer: ~7KB per location (with nested reviews/photos/votes)                       #
# - MapLocationSerializer: ~30 bytes per location (id, name, lat, lng, quality)                         #
# - LocationInfoPanelSerializer: ~300 bytes per location (basic info + stats only)                      #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db.models import Avg
from rest_framework import serializers
from ..models import Location
from ..models import FavoriteLocation
from . import ReviewSerializer



class LocationSerializer(serializers.ModelSerializer):
    added_by = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    verified_by = serializers.SerializerMethodField()

    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()


    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'elevation',
                  'formatted_address', 'administrative_area', 'locality', 'country',
                  'added_by',
                  'created_at', 'is_favorited',
                  'reviews', 'average_rating', 'review_count',

                  # Verification fields:
                  'is_verified', 'verification_date', 'verified_by', 'verification_notes',
                  'times_reported', 'last_visited', 'visitor_count'
                  ]

        read_only_fields = ['id', 'added_by',
                          'created_at', 'formatted_address', 'administrative_area',
                          'locality', 'country',

                            # Verification fields are read-only (managed by system)
                            'is_verified', 'verification_date', 'verified_by', 'verification_notes',
                            'times_reported', 'last_visited', 'visitor_count'
                            ]


    def get_added_by(self, obj):
        return {
            'id': obj.added_by.id,
            'username': obj.added_by.username
        } if obj.added_by else None


    def get_average_rating(self, obj):
        return obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']


    def get_review_count(self, obj):
        return obj.reviews.count()


    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteLocation.objects.filter(
                user=request.user,
                location=obj
            ).exists()

        # Otherwise return false since no favorites:
        return False


    def get_verified_by(self, obj):
        if obj.verified_by:
            return {
                'id': obj.verified_by.id,
                'username': obj.verified_by.username
            }
        return None



# ----------------------------------------------------------------------------- #
# Lightweight serializer optimized for map marker display.                      #
#                                                                               #
# This serializer returns only the minimal data needed to render location       #
# markers on the 3D globe interface. By excluding unnecessary fields like       #
# reviews, nested user data, and metadata, it reduces payload size by ~97%      #
# compared to the full LocationSerializer.                                      #
#                                                                               #
# Note: Includes is_favorited field for authenticated users to display favorite #
# status indicators on map markers and sidebar.                                 #
# ----------------------------------------------------------------------------- #
class MapLocationSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'is_favorited']
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteLocation.objects.filter(
                user=request.user,
                location=obj
            ).exists()
        return False



# ----------------------------------------------------------------------------- #
# Optimized serializer for map info panel display.                              #
#                                                                               #
# This serializer provides just enough data to populate the info panel that     #
# appears when a user clicks a marker on the map. It includes basic location    #
# info and review statistics, but excludes heavy nested data like full review   #
# content, photos, comments, and vote data.                                     #
# ----------------------------------------------------------------------------- #
class LocationInfoPanelSerializer(serializers.ModelSerializer):

    added_by_id = serializers.IntegerField(source='added_by.id', read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()


    class Meta:
        model = Location
        fields = [
            'id', 'name', 'latitude', 'longitude', 'elevation',
            'formatted_address',
            'added_by_id', 'average_rating', 'review_count'
        ]
        read_only_fields = fields


    # Calculate average rating without fetching full review objects:
    def get_average_rating(self, obj):
        return obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']


    # Get review count without fetching full review objects:
    def get_review_count(self, obj):
        return obj.reviews.count()
