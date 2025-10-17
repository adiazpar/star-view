from django.db.models import Avg
from rest_framework import serializers

from stars_app.models.model_favorite_location import FavoriteLocation
from stars_app.models.model_review_comment import ReviewComment
from stars_app.models.model_viewing_location import ViewingLocation
from stars_app.models.model_location_review import LocationReview
from stars_app.models.model_user_profile import UserProfile
from stars_app.models.model_review_photo import ReviewPhoto
from django.contrib.auth.models import User

# Unified report model (replaces LocationReport, ReviewReport, CommentReport)
from stars_app.models.model_report import Report

# Unified vote model (replaces ReviewVote, CommentVote)
from stars_app.models.model_vote import Vote


# Review Comment Serializer --------------------------------------- #
class ReviewCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    is_edited = serializers.ReadOnlyField()

    class Meta:
        model = ReviewComment
        fields = ['id', 'review', 'user', 'user_profile_picture', 'content',
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

    def get_upvote_count(self, obj):
        return obj.upvote_count

    def get_downvote_count(self, obj):
        return obj.downvote_count

    def get_user_vote(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_vote(request.user)
        return None


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
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(obj)

            vote = Vote.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id
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


# Viewing Location Serializer ------------------------------------- #
class ViewingLocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)  # Explicitly define ID as integer
    added_by = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    verified_by = serializers.SerializerMethodField()

    reviews = LocationReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = ViewingLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'elevation',
                  'formatted_address', 'administrative_area', 'locality', 'country',
                  'quality_score', 'added_by',
                  'created_at', 'is_favorited',
                  'reviews', 'average_rating', 'review_count',

                  # Verification fields:
                  'is_verified', 'verification_date', 'verified_by', 'verification_notes',
                  'times_reported', 'last_visited', 'visitor_count'
                  ]

        read_only_fields = ['quality_score', 'added_by',
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


# ========================================================================== #
# GENERIC VOTE SERIALIZER
# ========================================================================== #
# This serializer handles votes for ANY type of content using Django's
# ContentTypes framework. It works with the generic Vote model.
# ========================================================================== #

class VoteSerializer(serializers.ModelSerializer):
    """
    Generic serializer for the Vote model.

    This serializer uses Django's ContentTypes framework to handle votes
    for ANY model in your project. The voted object is specified via:
    - content_type: The model being voted on (auto-detected from object)
    - object_id: The ID of the specific object being voted on

    This is completely generic and requires no changes to support new
    votable content types.
    """

    # ===== USER INFORMATION =====
    user = serializers.ReadOnlyField(
        source='user.username',
        help_text="Username of the person who cast this vote"
    )

    # ===== CONTENT TYPE INFORMATION =====
    voted_object_type = serializers.ReadOnlyField(
        help_text="Type of object being voted on (e.g., 'locationreview', 'reviewcomment')"
    )

    voted_object_str = serializers.SerializerMethodField(
        help_text="String representation of the voted object"
    )


    class Meta:
        model = Vote

        fields = [
            # Basic vote info
            'id',
            'created_at',

            # Generic relationship fields
            'content_type',
            'object_id',
            'voted_object_type',  # Helper field showing model name
            'voted_object_str',   # Human-readable string of the object

            # Vote data
            'user',
            'is_upvote',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'user',
            'content_type',  # Auto-set from the object being voted on
        ]


    def get_voted_object_str(self, obj):
        """
        Returns a human-readable string representation of the voted object.

        This calls the __str__ method on the voted object to get a
        meaningful description.
        """
        if obj.voted_object:
            return str(obj.voted_object)
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id}"


# ========================================================================== #
# GENERIC REPORT SERIALIZER
# ========================================================================== #
# This serializer handles reports for ANY type of content using Django's
# ContentTypes framework. It works with the generic Report model.
# ========================================================================== #

class ReportSerializer(serializers.ModelSerializer):
    """
    Generic serializer for the Report model.

    This serializer uses Django's ContentTypes framework to handle reports
    for ANY model in your project. The reported object is specified via:
    - content_type: The model being reported (auto-detected from object)
    - object_id: The ID of the specific object being reported

    This is completely generic and requires no changes to support new
    reportable content types.
    """

    # ===== USER INFORMATION =====
    reported_by = serializers.ReadOnlyField(
        source='reported_by.username',
        help_text="Username of the person who submitted this report"
    )

    reviewed_by = serializers.ReadOnlyField(
        source='reviewed_by.username',
        help_text="Username of the moderator who reviewed this report (if reviewed)"
    )

    # ===== CONTENT TYPE INFORMATION =====
    reported_object_type = serializers.ReadOnlyField(
        help_text="Type of object being reported (e.g., 'viewinglocation', 'locationreview')"
    )

    reported_object_str = serializers.SerializerMethodField(
        help_text="String representation of the reported object"
    )


    class Meta:
        model = Report

        fields = [
            # Basic report info
            'id',
            'created_at',
            'updated_at',

            # Generic relationship fields
            'content_type',
            'object_id',
            'reported_object_type',  # Helper field showing model name
            'reported_object_str',   # Human-readable string of the object

            # Report details
            'reported_by',
            'report_type',
            'description',
            'status',

            # Additional data (JSON field for any extra context)
            'additional_data',

            # Moderation fields
            'reviewed_by',
            'review_notes',
            'reviewed_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'reported_by',
            'reviewed_by',
            'reviewed_at',
            'status',
            'content_type',  # Auto-set from the object being reported
        ]


    def get_reported_object_str(self, obj):
        """
        Returns a human-readable string representation of the reported object.

        This calls the __str__ method on the reported object to get a
        meaningful description.
        """
        if obj.reported_object:
            return str(obj.reported_object)
        return f"{obj.content_type.model if obj.content_type else 'Unknown'} #{obj.object_id}"
