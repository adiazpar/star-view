from django.db.models import Avg
from rest_framework import serializers

from stars_app.models.celestialevent import CelestialEvent
from stars_app.models.favoritelocation import FavoriteLocation
from stars_app.models.reviewvote import ReviewVote
from stars_app.models.reviewcomment import ReviewComment
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.models.locationreview import LocationReview
from stars_app.models.userprofile import UserProfile
from stars_app.models.forecast import Forecast
from django.contrib.auth.models import User


# Review Comment Serializer --------------------------------------- #
class ReviewCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = ['id', 'review', 'user', 'user_profile_picture', 'content', 'created_at']
        read_only_fields = ['user', 'review']

    def get_user(self, obj):
        # Return full user information needed by frontend
        return {
            'username': obj.user.username,
            'profile_picture_url': obj.user.userprofile.get_profile_picture_url
        }

    def get_user_profile_picture(self, obj):
        # Get the user's profile picture URL
        return obj.user.userprofile.get_profile_picture_url


# Location Review Serializer -------------------------------------- #
class LocationReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_full_name = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = LocationReview
        fields = ['id', 'location', 'user', 'user_full_name',
                 'rating', 'comment', 'created_at', 'updated_at',
                  'vote_count', 'user_vote']

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = ReviewVote.objects.filter(
                user=request.user,
                review=obj
            ).first()

            # Convert boolean to string representation
            if vote is not None:  # Check if vote exists
                return 'up' if vote.is_upvote else 'down'
        return None  # Return None if no vote exists

    def get_vote_count(self, obj):
        # Calculate the total vote score
        upvotes = obj.votes.filter(is_upvote=True).count()
        downvotes = obj.votes.filter(is_upvote=False).count()
        return upvotes - downvotes


# Viewing Location Serializer ------------------------------------- #
class ViewingLocationSerializer(serializers.ModelSerializer):
    added_by = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    reviews = LocationReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    moon_phase_info = serializers.SerializerMethodField()

    class Meta:
        model = ViewingLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'elevation',
                  'formatted_address', 'administrative_area', 'locality', 'country',
                  'light_pollution_value', 'quality_score', 'added_by',
                  'created_at', 'is_favorited', 'cloudCoverPercentage', 'forecast',
                  'reviews', 'average_rating', 'review_count',

                  # Moon Related Fields:
                  'moon_phase', 'moon_altitude', 'moon_impact_score',
                  'next_moonrise', 'next_moonset',
                  'next_astronomical_dawn', 'next_astronomical_dusk',
                  'moon_phase_info'
                  ]

        read_only_fields = ['light_pollution_value', 'quality_score', 'added_by',
                          'created_at', 'formatted_address', 'administrative_area',
                          'locality', 'country',

                            # Moon fields as read-only since they're calculated
                            'moon_phase', 'moon_altitude', 'moon_impact_score',
                            'next_moonrise', 'next_moonset',
                            'next_astronomical_dawn', 'next_astronomical_dusk'
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

    def get_moon_phase_info(self, obj):
        """
        Returns both the numerical phase and descriptive information
        about the current moon phase.
        """
        phase_info = obj.get_moon_phase_name()
        return {
            'percentage': obj.moon_phase,
            'short_name': phase_info['short_name'],
            'description': phase_info['description']
        }


# Celestial Event Serializer -------------------------------------- #
class CelestialEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CelestialEvent
        fields = ['id', 'name', 'event_type', 'description',
                  'latitude', 'longitude', 'elevation',
                  'start_time', 'end_time',
                  'viewing_radius']


# User Profile Serializer ---------------------------------------- #
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    profile_picture_url = serializers.ReadOnlyField(source='get_profile_picture_url')
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'profile_picture', 'profile_picture_url', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


# User Serializer ------------------------------------------------ #
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile']
        read_only_fields = ['date_joined']


# Favorite Location Serializer ----------------------------------- #
class FavoriteLocationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    location = ViewingLocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=ViewingLocation.objects.all(),
        source='location',
        write_only=True
    )
    display_name = serializers.ReadOnlyField(source='get_display_name')
    
    class Meta:
        model = FavoriteLocation
        fields = ['id', 'user', 'location', 'location_id', 'nickname', 'display_name', 'created_at']
        read_only_fields = ['user', 'created_at']


# Review Vote Serializer ----------------------------------------- #
class ReviewVoteSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ReviewVote
        fields = ['id', 'user', 'review', 'is_upvote', 'created_at']
        read_only_fields = ['user', 'created_at']


# Forecast Serializer -------------------------------------------- #
class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forecast
        fields = ['id', 'forecast', 'createTime']
        read_only_fields = ['createTime']


# Note: defaultforecast is a function, not a model, so no serializer needed
