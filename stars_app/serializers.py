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
from stars_app.models.locationphoto import LocationPhoto
from stars_app.models.locationcategory import LocationCategory, LocationTag
from stars_app.models.locationreport import LocationReport
from stars_app.models.reviewphoto import ReviewPhoto
from django.contrib.auth.models import User


# Review Comment Serializer --------------------------------------- #
class ReviewCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()
    formatted_content = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    is_edited = serializers.ReadOnlyField()

    class Meta:
        model = ReviewComment
        fields = ['id', 'review', 'user', 'user_profile_picture', 'content', 'formatted_content', 
                  'created_at', 'upvote_count', 'downvote_count', 'user_vote', 'is_edited']
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

    def get_formatted_content(self, obj):
        # Convert markdown to HTML for display
        return self._markdown_format(obj.content)
    
    def get_upvote_count(self, obj):
        return obj.upvote_count
    
    def get_downvote_count(self, obj):
        return obj.downvote_count
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_vote(request.user)
        return None
    
    def _markdown_format(self, text):
        """Convert basic markdown to HTML"""
        if not text:
            return ""
        
        import re
        
        # Handle bold (**text**)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Handle underline (__text__)  
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
        
        # Handle italic (*text*) - but avoid touching content inside ** 
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        
        return text


# Review Photo Serializer ----------------------------------------- #
class ReviewPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ReviewPhoto
        fields = ['id', 'image', 'thumbnail', 'caption', 'order', 
                  'image_url', 'thumbnail_url', 'created_at']
        read_only_fields = ['thumbnail', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image_url if obj.image else None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return obj.thumbnail_url if obj.thumbnail else None


# Location Review Serializer -------------------------------------- #
class LocationReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_full_name = serializers.SerializerMethodField()
    vote_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    is_edited = serializers.ReadOnlyField()

    class Meta:
        model = LocationReview
        fields = ['id', 'location', 'user', 'user_full_name',
                 'rating', 'comment', 'created_at', 'updated_at',
                  'vote_count', 'upvote_count', 'downvote_count', 'user_vote', 'photos', 'is_edited']

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

    def get_upvote_count(self, obj):
        # Get the number of upvotes
        return obj.votes.filter(is_upvote=True).count()

    def get_downvote_count(self, obj):
        # Get the number of downvotes
        return obj.votes.filter(is_upvote=False).count()


# Location Category Serializer ---------------------------------- #
class LocationCategorySerializer(serializers.ModelSerializer):
    location_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LocationCategory
        fields = ['id', 'name', 'slug', 'category_type', 'description', 'icon', 'location_count']
        read_only_fields = ['slug']
    
    def get_location_count(self, obj):
        return obj.locations.count()


# Location Tag Serializer ---------------------------------------- #
class LocationTagSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = LocationTag
        fields = ['id', 'name', 'slug', 'created_by', 'usage_count', 'is_approved', 'created_at']
        read_only_fields = ['slug', 'created_by', 'usage_count', 'created_at']


# Location Photo Serializer -------------------------------------- #
class LocationPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')
    uploaded_at = serializers.ReadOnlyField(source='created_at')
    image_url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()
    
    class Meta:
        model = LocationPhoto
        fields = ['id', 'location', 'uploaded_by', 'uploaded_by_username', 'uploaded_at', 
                  'image', 'image_url', 'thumbnail_url', 'caption', 'is_primary', 'is_approved', 
                  'taken_at', 'camera_make', 'camera_model', 'camera_settings', 'created_at']
        read_only_fields = ['uploaded_by', 'uploaded_by_username', 'uploaded_at', 'is_approved', 
                           'created_at', 'image_url', 'thumbnail_url', 'taken_at', 'camera_make', 
                           'camera_model', 'camera_settings']
        extra_kwargs = {
            'image': {'write_only': True}
        }


# Viewing Location Serializer ------------------------------------- #
class ViewingLocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # Explicitly define ID as integer
    added_by = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    verified_by = serializers.SerializerMethodField()

    reviews = LocationReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    photos = LocationPhotoSerializer(many=True, read_only=True)
    primary_photo = serializers.SerializerMethodField()
    
    categories = LocationCategorySerializer(many=True, read_only=True)
    tags = LocationTagSerializer(many=True, read_only=True)

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
                  'moon_phase_info',
                  
                  # Verification fields:
                  'is_verified', 'verification_date', 'verified_by', 'verification_notes',
                  'times_reported', 'last_visited', 'visitor_count',
                  
                  # Photo fields:
                  'photos', 'primary_photo',
                  
                  # Categories and tags:
                  'categories', 'tags'
                  ]

        read_only_fields = ['light_pollution_value', 'quality_score', 'added_by',
                          'created_at', 'formatted_address', 'administrative_area',
                          'locality', 'country',

                            # Moon fields as read-only since they're calculated
                            'moon_phase', 'moon_altitude', 'moon_impact_score',
                            'next_moonrise', 'next_moonset',
                            'next_astronomical_dawn', 'next_astronomical_dusk',
                            
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
    
    def get_verified_by(self, obj):
        if obj.verified_by:
            return {
                'id': obj.verified_by.id,
                'username': obj.verified_by.username
            }
        return None
    
    def get_primary_photo(self, obj):
        primary = obj.photos.filter(is_primary=True, is_approved=True).first()
        if primary:
            return LocationPhotoSerializer(primary).data
        # If no primary, get the first approved photo
        first_photo = obj.photos.filter(is_approved=True).first()
        if first_photo:
            return LocationPhotoSerializer(first_photo).data
        return None


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


# Location Report Serializer ------------------------------------- #
class LocationReportSerializer(serializers.ModelSerializer):
    reported_by = serializers.ReadOnlyField(source='reported_by.username')
    reviewed_by = serializers.ReadOnlyField(source='reviewed_by.username')
    location_name = serializers.ReadOnlyField(source='location.name')
    duplicate_of_name = serializers.ReadOnlyField(source='duplicate_of.name')
    
    class Meta:
        model = LocationReport
        fields = ['id', 'location', 'location_name', 'reported_by', 'report_type', 
                  'description', 'status', 'duplicate_of', 'duplicate_of_name',
                  'reviewed_by', 'review_notes', 'reviewed_at', 'created_at']
        read_only_fields = ['reported_by', 'reviewed_by', 'reviewed_at', 'created_at', 'status']
