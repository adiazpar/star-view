from django.db.models import Avg
from rest_framework import serializers

from stars_app.models.favoritelocation import FavoriteLocation
from stars_app.models.reviewvote import ReviewVote
from stars_app.models.reviewcomment import ReviewComment
from stars_app.models.viewinglocation import ViewingLocation
from stars_app.models.locationreview import LocationReview
from stars_app.models.userprofile import UserProfile
from stars_app.models.locationreport import LocationReport
from stars_app.models.reviewphoto import ReviewPhoto
from stars_app.models.reviewreport import ReviewReport
from stars_app.models.commentreport import CommentReport
from django.contrib.auth.models import User


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


# Review Vote Serializer ----------------------------------------- #
class ReviewVoteSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = ReviewVote
        fields = ['id', 'user', 'review', 'is_upvote', 'created_at']
        read_only_fields = ['user', 'created_at']


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


class ReviewReportSerializer(serializers.ModelSerializer):
    reported_by = serializers.ReadOnlyField(source='reported_by.username')
    reviewed_by = serializers.ReadOnlyField(source='reviewed_by.username')
    review_user = serializers.ReadOnlyField(source='review.user.username')
    review_location = serializers.ReadOnlyField(source='review.location.name')
    
    class Meta:
        model = ReviewReport
        fields = ['id', 'review', 'review_user', 'review_location', 'reported_by', 
                  'report_type', 'description', 'status', 'reviewed_by', 'review_notes', 
                  'reviewed_at', 'created_at']
        read_only_fields = ['reported_by', 'reviewed_by', 'reviewed_at', 'created_at', 'status']


class CommentReportSerializer(serializers.ModelSerializer):
    reported_by = serializers.ReadOnlyField(source='reported_by.username')
    reviewed_by = serializers.ReadOnlyField(source='reviewed_by.username')
    comment_user = serializers.ReadOnlyField(source='comment.user.username')
    comment_review_user = serializers.ReadOnlyField(source='comment.review.user.username')
    comment_location = serializers.ReadOnlyField(source='comment.review.location.name')
    
    class Meta:
        model = CommentReport
        fields = ['id', 'comment', 'comment_user', 'comment_review_user', 'comment_location', 
                  'reported_by', 'report_type', 'description', 'status', 'reviewed_by', 
                  'review_notes', 'reviewed_at', 'created_at']
        read_only_fields = ['reported_by', 'reviewed_by', 'reviewed_at', 'created_at', 'status']
