# ----------------------------------------------------------------------------------------------------- #
# This views_review.py file handles all review and comment-related views and API endpoints:            #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints and function-based views for managing location reviews and comments.     #
# Reviews include ratings, text comments, photo uploads, and voting functionality.                     #
#                                                                                                       #
# Key Features:                                                                                         #
# - ReviewViewSet: Full CRUD API for reviews with filtering, ordering, and pagination                  #
# - ReviewCommentViewSet: API for nested comments on reviews with vote tracking                        #
# - Photo management: Upload, update, and delete review photos (max 5 per review)                      #
# - Vote handling: Users can upvote/downvote reviews and comments using generic Vote model             #
# - Report system: Users can report inappropriate reviews/comments via ContentTypes framework          #
# - Permission checks: Users can only edit/delete their own content                                    #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                              #
# - Integrates with ContentTypes framework for generic Vote and Report models                          #
# - Automatically updates Location aggregate ratings when reviews change                               #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# REST Framework imports:
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

# Model imports:
from stars_app.models.model_review import Review
from stars_app.models.model_review_comment import ReviewComment
from stars_app.models.model_review_photo import ReviewPhoto
from stars_app.models.model_location import Location
from stars_app.models.model_report import Report
from stars_app.models.model_vote import Vote
from django.contrib.contenttypes.models import ContentType

# Serializer imports:
from stars_app.serializers import ReviewSerializer, ReviewCommentSerializer, ReportSerializer

# Other imports:
import json



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       REVIEW VIEWSET                                                  #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

class ReviewViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing location reviews.

    Provides endpoints for creating, retrieving, updating, and deleting reviews.
    Includes photo upload/deletion and voting functionality.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['rating', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter reviews by location from URL parameters."""
        return Review.objects.filter(
            location_id=self.kwargs['location_pk']
        )

    def get_serializer_context(self):
        """Ensure the serializer has access to the request."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """Create a review for a specific location."""
        location = Location.objects.get(pk=self.kwargs['location_pk'])
        serializer.save(
            user=self.request.user,
            location=location
        )

    @action(detail=True, methods=['POST'])
    def vote(self, request, pk=None, location_pk=None):
        """Handle voting on reviews using the generic Vote model."""
        review = self.get_object()
        vote_type = request.data.get('vote_type')

        if vote_type not in ['up', 'down']:
            return Response(
                {'error': 'Invalid vote type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert vote_type to boolean
        is_upvote = vote_type == 'up'

        # Get the ContentType for Review model
        content_type = ContentType.objects.get_for_model(review)

        # Get or create the vote using generic Vote model
        vote, created = Vote.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=review.id,
            defaults={'is_upvote': is_upvote}
        )

        if not created:
            if vote.is_upvote == is_upvote:
                # If voting the same way, remove the vote
                vote.delete()
                vote = None
            else:
                # If voting differently, update the vote
                vote.is_upvote = is_upvote
                vote.save()

        # Calculate updated vote information using generic Vote queryset
        upvotes = Vote.objects.filter(
            content_type=content_type,
            object_id=review.id,
            is_upvote=True
        ).count()
        downvotes = Vote.objects.filter(
            content_type=content_type,
            object_id=review.id,
            is_upvote=False
        ).count()
        vote_count = upvotes - downvotes

        # Get current user's vote status
        user_vote = None
        if vote:
            user_vote = 'up' if vote.is_upvote else 'down'

        return Response({
            'vote_count': vote_count,
            'user_vote': user_vote,
            'upvotes': upvotes,
            'downvotes': downvotes
        })

    def update(self, request, *args, **kwargs):
        """Update a review (permission check: user must own the review)."""
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'detail': 'You can only edit your own reviews.'},
                          status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partially update a review with photo upload/deletion support."""
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'detail': 'You can only edit your own reviews.'},
                          status=status.HTTP_403_FORBIDDEN)

        # Handle photo uploads and deletions
        response = super().partial_update(request, *args, **kwargs)

        if response.status_code == 200:
            # Handle image uploads
            uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')
            if uploaded_images:
                # Check existing photos count
                existing_photos_count = instance.photos.count()
                if existing_photos_count + len(uploaded_images) > 5:
                    return Response(
                        {'detail': f'You can only have up to 5 photos per review. You already have {existing_photos_count} photos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5-existing_photos_count]):
                    try:
                        ReviewPhoto.objects.create(
                            review=instance,
                            image=image,
                            order=existing_photos_count + idx
                        )
                    except Exception:
                        # Continue processing other images on error
                        pass

            # Handle image deletions
            delete_photo_ids = request.data.get('delete_photo_ids')
            if delete_photo_ids:
                try:
                    # Parse JSON string if needed
                    if isinstance(delete_photo_ids, str):
                        delete_photo_ids = json.loads(delete_photo_ids)

                    # Delete the specified photos
                    instance.photos.filter(id__in=delete_photo_ids).delete()
                except Exception:
                    # Continue on error
                    pass

            # Re-serialize with updated photos
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        return response

    @action(detail=True, methods=['POST'])
    def report(self, request, pk=None, location_pk=None):
        """Handle reporting reviews using the generic Report model."""
        try:
            review = self.get_object()

            # Prevent users from reporting their own reviews
            if review.user == request.user:
                return Response(
                    {'detail': 'You cannot report your own review'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the ContentType for Review model
            content_type = ContentType.objects.get_for_model(review)

            # Check if user already reported this review
            existing_report = Report.objects.filter(
                content_type=content_type,
                object_id=review.id,
                reported_by=request.user
            ).first()

            if existing_report:
                return Response(
                    {'detail': 'You have already reported this review'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare report data for the generic Report model
            report_data = {
                'object_id': review.id,
                'report_type': request.data.get('report_type', 'OTHER'),
                'description': request.data.get('description', '')
            }

            serializer = ReportSerializer(data=report_data)
            if serializer.is_valid():
                serializer.save(
                    content_type=content_type,
                    reported_by=request.user
                )
                return Response(
                    {'detail': 'Review reported successfully'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                   REVIEW COMMENT VIEWSET                                              #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

class ReviewCommentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing comments on reviews.

    Provides endpoints for creating, retrieving, updating, and deleting comments.
    Includes voting and reporting functionality via ContentTypes framework.
    """
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter comments by review from URL parameters."""
        return ReviewComment.objects.filter(
            review_id=self.kwargs['review_pk']
        ).select_related('user', 'user__userprofile')

    def get_serializer_context(self):
        """Ensure the serializer has access to the request."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """Create a comment for a specific review."""
        try:
            review = get_object_or_404(
                Review,
                id=self.kwargs['review_pk'],
                location_id=self.kwargs['location_pk']
            )

            # Create the comment
            comment = serializer.save(
                user=self.request.user,
                review=review
            )

            # Re-serialize the created comment with full user information
            return_serializer = self.get_serializer(comment)
            return return_serializer.data

        except Exception as e:
            raise

    def create(self, request, *args, **kwargs):
        """Create a comment with error handling."""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        """Delete a comment (permission check: user must own the comment)."""
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()

    @action(detail=True, methods=['POST'])
    def vote(self, request, pk=None, location_pk=None, review_pk=None):
        """Handle voting on comments using the generic Vote model."""
        try:
            comment = self.get_object()
            vote_type = request.data.get('vote_type')

            if vote_type not in ['up', 'down']:
                return Response(
                    {'detail': 'Vote type must be "up" or "down"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prevent users from voting on their own comments
            if comment.user == request.user:
                return Response(
                    {'detail': 'You cannot vote on your own comment'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            is_upvote = vote_type == 'up'

            # Get the ContentType for ReviewComment model
            content_type = ContentType.objects.get_for_model(comment)

            # Get or create the vote using generic Vote model
            vote, created = Vote.objects.get_or_create(
                user=request.user,
                content_type=content_type,
                object_id=comment.id,
                defaults={'is_upvote': is_upvote}
            )

            user_vote = None
            if not created:
                if vote.is_upvote == is_upvote:
                    # Same vote type - remove the vote (toggle off)
                    vote.delete()
                    user_vote = None
                else:
                    # Different vote type - update the vote
                    vote.is_upvote = is_upvote
                    vote.save()
                    user_vote = 'up' if is_upvote else 'down'
            else:
                user_vote = 'up' if is_upvote else 'down'

            # Return updated vote counts and user's vote status
            return Response({
                'upvotes': comment.upvote_count,
                'downvotes': comment.downvote_count,
                'user_vote': user_vote
            })

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['POST'])
    def report(self, request, pk=None, location_pk=None, review_pk=None):
        """Handle reporting comments using the generic Report model."""
        try:
            comment = self.get_object()

            # Prevent users from reporting their own comments
            if comment.user == request.user:
                return Response(
                    {'detail': 'You cannot report your own comment'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the ContentType for ReviewComment model
            content_type = ContentType.objects.get_for_model(comment)

            # Check if user already reported this comment
            existing_report = Report.objects.filter(
                content_type=content_type,
                object_id=comment.id,
                reported_by=request.user
            ).first()

            if existing_report:
                return Response(
                    {'detail': 'You have already reported this comment'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare report data for the generic Report model
            report_data = {
                'object_id': comment.id,
                'report_type': request.data.get('report_type', 'OTHER'),
                'description': request.data.get('description', '')
            }

            serializer = ReportSerializer(data=report_data)
            if serializer.is_valid():
                serializer.save(
                    content_type=content_type,
                    reported_by=request.user
                )
                return Response(
                    {'detail': 'Comment reported successfully'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                  FUNCTION-BASED VIEWS                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

@login_required
def delete_review(request, review_id):
    """
    Delete a review (function-based view for legacy support).

    Args:
        request: HTTP request object
        review_id: ID of the review to delete

    Returns:
        JsonResponse with success status and message
    """
    review = get_object_or_404(Review, pk=review_id)

    # Check if the logged-in user owns this review
    if request.user != review.user:
        return JsonResponse({
            'success': False,
            'message': 'You can only delete your own reviews'
        }, status=403)

    try:
        # Delete the review
        review.delete()
        return JsonResponse({
            'success': True,
            'message': 'Review deleted successfully',
            'should_show_form': True
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to delete review'
        }, status=500)
