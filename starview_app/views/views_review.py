# ----------------------------------------------------------------------------------------------------- #
# This views_review.py file handles all review and comment-related views and API endpoints:             #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints and function-based views for managing location reviews and comments.      #
# Reviews include ratings, text comments, photo uploads, and voting functionality.                      #
#                                                                                                       #
# Key Features:                                                                                         #
# - ReviewViewSet: Full CRUD API for reviews with filtering, ordering, and pagination                   #
# - CommentViewSet: API for nested comments on reviews with vote tracking                               #
# - Photo management: Upload, update, and delete review photos (max 5 per review)                       #
# - Vote handling: Users can upvote/downvote reviews and comments using generic Vote model              #
# - Report system: Users can report inappropriate reviews/comments via ContentTypes framework           #
# - Permission checks: Users can only edit/delete their own content                                     #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                               #
# - Integrates with ContentTypes framework for generic Vote and Report models                           #
# - Automatically updates Location aggregate ratings when reviews change                                #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import get_object_or_404

# REST Framework imports:
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response

# Model imports:
from starview_app.models.model_review import Review
from starview_app.models.model_review_comment import ReviewComment
from starview_app.models.model_review_photo import ReviewPhoto
from starview_app.models.model_location import Location

# Serializer imports:
from starview_app.serializers import ReviewSerializer, ReviewCommentSerializer

# Service imports:
from starview_app.services import ReportService, VoteService

# Throttle imports:
from starview_app.utils import ContentCreationThrottle, VoteThrottle, ReportThrottle

# Cache imports:
from starview_app.utils import invalidate_location_detail, invalidate_review_list



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       PERMISSION CLASSES                                              #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Permission class that allows read access to everyone but write access only    #
# to the owner of the object.                                                   #
#                                                                               #
# Safe methods (GET, HEAD, OPTIONS) are allowed for all users.                  #
# Unsafe methods (POST, PUT, PATCH, DELETE) require object ownership.           #
# ----------------------------------------------------------------------------- #
class IsOwnerOrReadOnly(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.user == request.user



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       REVIEW VIEWSET                                                  #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# API ViewSet for managing location reviews.                                    #
#                                                                               #
# Provides endpoints for creating, retrieving, updating, and deleting reviews.  #
# Includes photo upload/deletion, voting, and reporting functionality.          #
# ----------------------------------------------------------------------------- #
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


    # Apply different throttles based on action:
    def get_throttles(self):
        if self.action == 'create':
            # Limit review creation to prevent spam
            return [ContentCreationThrottle()]
        elif self.action == 'vote':
            # Limit votes to prevent vote manipulation
            return [VoteThrottle()]
        elif self.action == 'report':
            # Limit reports to prevent report abuse
            return [ReportThrottle()]
        return super().get_throttles()


    # Filter reviews by location from URL parameters:
    def get_queryset(self):
        from django.contrib.contenttypes.models import ContentType
        from starview_app.models import Vote

        queryset = Review.objects.filter(
            location_id=self.kwargs['location_pk']
        ).select_related(
            'user',
            'location'
        ).prefetch_related(
            'photos',
            'comments__user',
            'votes'  # Prefetch votes to avoid N+1 in get_user_vote()
        )

        return queryset


    # ----------------------------------------------------------------------------- #
    # Create a review for a location and associate it with the current user.       #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_create() to inject   #
    # the current user and location from URL parameters. Without this override,    #
    # DRF would just call serializer.save() which would fail since user and        #
    # location are required fields. We also invalidate caches since the location   #
    # detail now has a new review affecting ratings and review count.              #
    # ----------------------------------------------------------------------------- #
    def perform_create(self, serializer):
        location = get_object_or_404(Location, pk=self.kwargs['location_pk'])
        serializer.save(
            user=self.request.user,
            location=location
        )

        # Invalidate caches since new review was created
        invalidate_location_detail(location.id)  # Location detail includes reviews
        invalidate_review_list(location.id)  # Review list for this location


    # ----------------------------------------------------------------------------- #
    # Update a review and invalidate related caches.                               #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_update() to add      #
    # cache invalidation. Without this override, DRF would just call               #
    # serializer.save() with no cache clearing, causing the location's cached      #
    # review data to become stale (wrong rating, outdated review text, etc).       #
    # ----------------------------------------------------------------------------- #
    def perform_update(self, serializer):
        review = self.get_object()
        location_id = review.location.id
        serializer.save()

        # Invalidate caches since review was updated
        invalidate_location_detail(location_id)
        invalidate_review_list(location_id)


    # ----------------------------------------------------------------------------- #
    # Delete a review and invalidate related caches.                               #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_destroy() to add     #
    # cache invalidation. Without this override, DRF would just call               #
    # instance.delete() with no cache clearing, causing the deleted review to      #
    # still appear in the location's cached review list and affecting cached       #
    # rating calculations.                                                          #
    # ----------------------------------------------------------------------------- #
    def perform_destroy(self, instance):
        location_id = instance.location.id
        instance.delete()

        # Invalidate caches since review was deleted
        invalidate_location_detail(location_id)
        invalidate_review_list(location_id)


    # ----------------------------------------------------------------------------- #
    # Add photos to a review (max 5 total).                                         #
    #                                                                               #
    # Security: Validates each uploaded image for file size (5MB max), MIME type,   #
    # and extension before processing to prevent malicious uploads and DOS attacks. #
    # ----------------------------------------------------------------------------- #
    @action(detail=True, methods=['POST'])
    def add_photos(self, request, pk=None, location_pk=None):
        from django.core.exceptions import ValidationError
        from starview_app.utils import validate_file_size, validate_image_file

        review = self.get_object()

        # Get uploaded images
        uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')

        if not uploaded_images:
            raise exceptions.ValidationError('No images provided')

        # Validate all files before processing any of them
        for image in uploaded_images:
            try:
                validate_file_size(image)
                validate_image_file(image)
            except ValidationError as e:
                raise exceptions.ValidationError(f'Invalid file "{image.name}": {str(e)}')

        # Check existing photos count
        existing_photos_count = review.photos.count()
        remaining_slots = 5 - existing_photos_count

        if remaining_slots <= 0:
            raise exceptions.ValidationError('You already have 5 photos. Delete some before adding more.')

        if len(uploaded_images) > remaining_slots:
            raise exceptions.ValidationError(
                f'You can only add {remaining_slots} more photo(s). You already have {existing_photos_count} photo(s).'
            )

        # Process each uploaded image (all validation passed)
        created_photos = []
        for idx, image in enumerate(uploaded_images):
            photo = ReviewPhoto.objects.create(
                review=review,
                image=image,
                order=existing_photos_count + idx
            )
            created_photos.append({
                'id': photo.id,
                'image_url': photo.image.url,
                'order': photo.order
            })

        return Response(
            {
                'detail': f'{len(created_photos)} photo(s) added successfully',
                'photos': created_photos
            },
            status=status.HTTP_201_CREATED
        )


    # Delete a photo from a review:
    @action(detail=True, methods=['DELETE'], url_path='photos/(?P<photo_id>[^/.]+)')
    def remove_photo(self, request, pk=None, location_pk=None, photo_id=None):
        review = self.get_object()

        try:
            photo = ReviewPhoto.objects.get(id=photo_id, review=review)
            photo.delete()

            return Response(
                {'detail': 'Photo deleted successfully'},
                status=status.HTTP_200_OK
            )
        except ReviewPhoto.DoesNotExist:
            raise exceptions.NotFound('Photo not found')


    # Handle voting on reviews using VoteService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None, location_pk=None):
        review = self.get_object()
        vote_type = request.data.get('vote_type')

        # Use VoteService to handle validation and vote processing
        # VoteService raises ValidationError on failure (caught by exception handler)
        vote_data = VoteService.handle_vote_request(
            user=request.user,
            content_object=review,
            vote_type=vote_type
        )

        return Response({
            'detail': 'Vote processed successfully',
            **vote_data
        }, status=status.HTTP_200_OK)


    # Handle reporting reviews using ReportService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None, location_pk=None):
        review = self.get_object()

        # Use ReportService to handle report submission
        # ReportService raises ValidationError on failure (caught by exception handler)
        report = ReportService.submit_report(
            user=request.user,
            content_object=review,
            report_type=request.data.get('report_type', 'OTHER'),
            description=request.data.get('description', '')
        )

        content_type_name = report.content_type.model.replace('_', ' ').capitalize()
        return Response(
            {'detail': f'{content_type_name} reported successfully'},
            status=status.HTTP_201_CREATED
        )



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       COMMENT VIEWSET                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# API ViewSet for managing comments on reviews.                                 #
#                                                                               #
# Provides endpoints for creating, retrieving, updating, and deleting comments. #
# Includes voting and reporting functionality via ContentTypes framework.       #
# ----------------------------------------------------------------------------- #
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


    # Apply different throttles based on action:
    def get_throttles(self):
        if self.action == 'create':
            # Limit comment creation to prevent spam
            return [ContentCreationThrottle()]
        elif self.action == 'vote':
            # Limit votes to prevent vote manipulation
            return [VoteThrottle()]
        elif self.action == 'report':
            # Limit reports to prevent report abuse
            return [ReportThrottle()]
        return super().get_throttles()


    # Filter comments by review from URL parameters:
    def get_queryset(self):
        return ReviewComment.objects.filter(
            review_id=self.kwargs['review_pk']
        ).select_related(
            'user',
            'user__userprofile',
            'review'
        ).prefetch_related(
            'votes'  # Prefetch votes to avoid N+1 in get_user_vote()
        )


    # Create a comment for a specific review:
    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs['review_pk'],
            location_id=self.kwargs['location_pk']
        )

        serializer.save(
            user=self.request.user,
            review=review
        )


    # Handle voting on comments using VoteService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None, location_pk=None, review_pk=None):
        comment = self.get_object()
        vote_type = request.data.get('vote_type')

        # Use VoteService to handle validation and vote processing
        # VoteService raises ValidationError on failure (caught by exception handler)
        vote_data = VoteService.handle_vote_request(
            user=request.user,
            content_object=comment,
            vote_type=vote_type
        )

        return Response({
            'detail': 'Vote processed successfully',
            **vote_data
        }, status=status.HTTP_200_OK)


    # Handle reporting comments using ReportService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None, location_pk=None, review_pk=None):
        comment = self.get_object()

        # Use ReportService to handle report submission
        # ReportService raises ValidationError on failure (caught by exception handler)
        report = ReportService.submit_report(
            user=request.user,
            content_object=comment,
            report_type=request.data.get('report_type', 'OTHER'),
            description=request.data.get('description', '')
        )

        content_type_name = report.content_type.model.replace('_', ' ').capitalize()
        return Response(
            {'detail': f'{content_type_name} reported successfully'},
            status=status.HTTP_201_CREATED
        )
