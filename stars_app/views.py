from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.exceptions import PermissionDenied

# Importing other things from project files:
from stars_app.models.userprofile import UserProfile
from django.contrib.auth.models import User
from stars_app.utils import is_valid_email


# Authentication libraries:
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy

# To display error/success messages:
from django.contrib import messages

# Rest Framework:
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from stars_app.serializers import *
from stars_app.models.locationreport import LocationReport

# Tile libraries:
import os
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views.decorators.cache import cache_control
import subprocess
from django.contrib.admin.views.decorators import staff_member_required
import requests

# Distance
from geopy.distance import geodesic

from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from itertools import chain
from django.core.paginator import Paginator
from .models.reviewvote import ReviewVote
from .models.commentvote import CommentVote

# -------------------------------------------------------------- #
# Pagination Classes:
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# -------------------------------------------------------------- #
# Viewing Location Views:

class ViewingLocationViewSet(viewsets.ModelViewSet):
    queryset = ViewingLocation.objects.all()
    serializer_class = ViewingLocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'formatted_address', 'locality']
    ordering_fields = ['quality_score', 'created_at', 'visitor_count', 'rating_count']
    ordering = ['-quality_score']

    def get_queryset(self):
        queryset = ViewingLocation.objects.all()
        favorites_only = self.request.query_params.get('favorites_only', 'false')
        if favorites_only.lower() == 'true' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        # Get values from serializer:
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        elevation = serializer.validated_data.get('elevation', 0)
        
        # Check for nearby duplicates before creating
        duplicates = self.check_for_duplicates(latitude, longitude)
        if duplicates and not self.request.data.get('force_create', False):
            # Manually create nearby_locations data to ensure IDs are integers
            nearby_locations = []
            for location in duplicates:
                nearby_locations.append({
                    'id': location.id,  # Ensure ID is integer
                    'name': location.name,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'quality_score': location.quality_score,
                })
            
            raise serializers.ValidationError({
                'duplicates_found': True,
                'nearby_locations': nearby_locations,
                'message': 'Similar locations found nearby. Add force_create=true to create anyway.'
            })

        serializer.save(
            added_by=self.request.user,
        )
    
    def check_for_duplicates(self, latitude, longitude, radius_km=0.5):
        """Check for duplicate locations within a radius"""
        from geopy.distance import geodesic
        
        # Query for locations within a rough bounding box first
        lat_range = 0.01  # Roughly 1.1 km
        lng_range = 0.01
        
        nearby_locations = ViewingLocation.objects.filter(
            latitude__range=(latitude - lat_range, latitude + lat_range),
            longitude__range=(longitude - lng_range, longitude + lng_range)
        )
        
        # Calculate precise distances
        duplicates = []
        for location in nearby_locations:
            distance = geodesic(
                (latitude, longitude),
                (location.latitude, location.longitude)
            ).km
            if distance <= radius_km:
                duplicates.append(location)
        
        return duplicates

    @action(detail=True, methods=['POST'])
    def update_elevation(self, request, pk=None):
        """Endpoint to manually trigger elevation update"""
        location = self.get_object()
        success = location.update_elevation_from_mapbox()

        if success:
            location.calculate_quality_score()  # Recalculate quality score with new elevation
            location.save()
            serializer = self.get_serializer(location)
            return Response(serializer.data)

        return Response(
            {'detail': 'Failed to update elevation'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['GET'])
    def check_duplicates(self, request):
        """Check for duplicate locations before creating"""
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius_km', 0.5))
        
        if not latitude or not longitude:
            return Response(
                {'detail': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Invalid latitude or longitude values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        duplicates = self.check_for_duplicates(latitude, longitude, radius_km)
        
        return Response({
            'duplicates_found': len(duplicates) > 0,
            'count': len(duplicates),
            'radius_km': radius_km,
            'locations': ViewingLocationSerializer(duplicates, many=True).data
        })

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        """Submit a report about this location"""
        location = self.get_object()
        
        # Prepare report data
        report_data = {
            'location': location.id,
            'report_type': request.data.get('report_type'),
            'description': request.data.get('description'),
            'duplicate_of': request.data.get('duplicate_of_id')
        }
        
        serializer = LocationReportSerializer(data=report_data)
        if serializer.is_valid():
            try:
                report = serializer.save(reported_by=request.user)
                
                # Increment report counter
                location.times_reported += 1
                location.save()
                
                return Response(
                    LocationReportSerializer(report).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Handle unique constraint violation (duplicate report)
                if 'unique constraint' in str(e).lower():
                    return Response(
                        {'detail': 'You have already submitted this type of report for this location'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                raise
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def reports(self, request, pk=None):
        """Get all reports for this location (admin only)"""
        location = self.get_object()
        
        # Only staff can see all reports
        if not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to view reports'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reports = location.reports.all()
        serializer = LocationReportSerializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST', 'GET'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        location = self.get_object()

        # Handle GET request case:
        if request.method == "GET":
            is_favorited = FavoriteLocation.objects.filter(
                user=request.user,
                location=location
            ).exists()
            return Response({
                'is_favorited': is_favorited,
                'detail': 'Location is favorited' if is_favorited else 'Location is not favorited'
            })


        # Check if already favorited:
        existing_favorite = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).first()

        if existing_favorite:
            return Response(
                {'detail': 'Location already favorited'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a new favorite:
        FavoriteLocation.objects.create(
            user=request.user,
            location=location
        )
        serializer = self.get_serializer(location)
        return Response(serializer.data)

    @action(detail=True, methods=['POST', 'GET'], permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        location = self.get_object()

        # If it's a GET request, just return the current status
        if request.method == 'GET':
            is_favorited = FavoriteLocation.objects.filter(
                user=request.user,
                location=location
            ).exists()
            return Response({
                'is_favorited': is_favorited,
                'detail': 'Location is favorited' if is_favorited else 'Location is not favorited'
            })

        deleted_count, _ = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).delete()

        if deleted_count:
            serializer = self.get_serializer(location)
            return Response(serializer.data)
        return Response(
            {'detail': 'Location was not favorited'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['GET'])
    def favorites(self, request):
        favorites = self.get_queryset().filter(favorited_by__user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='update-nickname', url_name='update-nickname')
    def update_nickname(self, request, pk=None):
        try:
            # Print debug information
            print("Request headers:", request.headers)
            print("Request data:", request.data)

            location = self.get_object()
            favorite = FavoriteLocation.objects.get(
                user=request.user,
                location=location
            )

            if not request.data:
                return Response(
                    {'success': False, 'detail': 'No data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            nickname = request.data.get('nickname', '').strip()
            favorite.nickname = nickname if nickname else None
            favorite.save()

            return Response({
                'success': True,
                'display_name': favorite.get_display_name(),
                'original_name': location.name,
                'defail': 'Nickname updated successfully'
            }, content_type='application/json')

        except Exception as e:
            print("Error:", str(e))  # Debug print
            return Response(
                {'success': False, 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

    @action(detail=True, methods=['POST'])
    def update_address(self, request, pk=None):
        """Endpoint to manually trigger address update"""
        location = self.get_object()
        success = location.update_address_from_coordinates()

        if success:
            location.save()
            serializer = self.get_serializer(location)
            return Response(serializer.data)

        return Response(
            {'detail': 'Failed to update address'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['POST'])
    def add_review(self, request, pk=None):
        location = self.get_object()

        # Check if user already reviewed this location
        existing_review = LocationReview.objects.filter(
            user=request.user,
            location=location
        ).first()

        if existing_review:
            return Response(
                {'detail': 'You have already reviewed this location'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LocationReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(user=request.user, location=location)
            
            # Handle image uploads
            uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.reviewphoto import ReviewPhoto
                
                # Validate number of images
                if len(uploaded_images) > 5:
                    # Delete the review if too many images
                    review.delete()
                    return Response(
                        {'detail': 'You can upload a maximum of 5 photos per review'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5]):
                    try:
                        ReviewPhoto.objects.create(
                            review=review,
                            image=image,
                            order=idx
                        )
                    except Exception as e:
                        # Log the error but continue processing other images
                        print(f"Error uploading review image: {str(e)}")
            
            # Return the review with photos included
            serializer = LocationReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PUT'])
    def update_review(self, request, pk=None):
        location = self.get_object()
        
        review = LocationReview.objects.filter(
            user_id=request.user.id,
            location_id=location.id
        ).first()

        if not review:
            return Response(
                {'detail': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LocationReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Handle image uploads for review updates
            uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.reviewphoto import ReviewPhoto
                
                # Check existing photos count
                existing_photos_count = review.photos.count()
                if existing_photos_count + len(uploaded_images) > 5:
                    return Response(
                        {'detail': f'You can only have up to 5 photos per review. You already have {existing_photos_count} photos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5-existing_photos_count]):
                    try:
                        ReviewPhoto.objects.create(
                            review=review,
                            image=image,
                            order=existing_photos_count + idx
                        )
                    except Exception as e:
                        print(f"Error uploading review image during update: {str(e)}")
            
            # Handle image deletions if specified
            delete_photo_ids = request.data.get('delete_photo_ids', [])
            if delete_photo_ids:
                # Parse JSON string if needed
                import json
                if isinstance(delete_photo_ids, str):
                    try:
                        delete_photo_ids = json.loads(delete_photo_ids)
                    except json.JSONDecodeError:
                        delete_photo_ids = []
                
                if delete_photo_ids:
                    deleted_result = review.photos.filter(id__in=delete_photo_ids).delete()                
            
            return Response(serializer.data)
        
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['DELETE'])
    def delete_review(self, request, pk=None):
        location = self.get_object()
        review = LocationReview.objects.filter(
            user=request.user,
            location=location
        ).first()

        if not review:
            return Response(
                {'detail': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LocationReviewViewSet(viewsets.ModelViewSet):
    serializer_class = LocationReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['rating', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return LocationReview.objects.filter(
            location_id=self.kwargs['location_pk']
        )

    def get_serializer_context(self):
        # This ensures the serializer has access to the request
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        location = ViewingLocation.objects.get(pk=self.kwargs['location_pk'])
        serializer.save(
            user=self.request.user,
            location=location
        )

    @action(detail=True, methods=['POST'])
    def vote(self, request, pk=None, location_pk=None):
        review = self.get_object()
        vote_type = request.data.get('vote_type')

        if vote_type not in ['up', 'down']:
            return Response(
                {'error': 'Invalid vote type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert vote_type to boolean
        is_upvote = vote_type == 'up'

        # Get or create the vote
        vote, created = ReviewVote.objects.get_or_create(
            user=request.user,
            review=review,
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

        # Calculate updated vote information
        upvotes = review.votes.filter(is_upvote=True).count()
        downvotes = review.votes.filter(is_upvote=False).count()
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
        instance = self.get_object()
        if instance.user != request.user:
            return Response({'detail': 'You can only edit your own reviews.'}, 
                           status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
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
                from stars_app.models.reviewphoto import ReviewPhoto
                
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
                    except Exception as e:
                        print(f"Error uploading review image during update: {str(e)}")
            
            # Handle image deletions
            delete_photo_ids = request.data.get('delete_photo_ids')
            if delete_photo_ids:
                try:
                    # Parse JSON string if needed
                    if isinstance(delete_photo_ids, str):
                        import json
                        delete_photo_ids = json.loads(delete_photo_ids)
                    
                    print(f"DEBUG: Parsed delete_photo_ids: {delete_photo_ids}")
                    
                    # Delete the specified photos
                    deleted_count = instance.photos.filter(id__in=delete_photo_ids).delete()
                except Exception as e:
                    print(f"Error deleting review photos: {str(e)}")
            
            # Re-serialize with updated photos
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        return response
    
    @action(detail=True, methods=['POST'])
    def report(self, request, pk=None, location_pk=None):
        """Handle reporting reviews"""
        try:
            review = self.get_object()
            
            # Prevent users from reporting their own reviews
            if review.user == request.user:
                return Response(
                    {'detail': 'You cannot report your own review'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already reported this review
            from stars_app.models.reviewreport import ReviewReport
            existing_report = ReviewReport.objects.filter(
                review=review,
                reported_by=request.user
            ).first()
            
            if existing_report:
                return Response(
                    {'detail': 'You have already reported this review'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the report
            report_data = {
                'review': review.id,
                'report_type': request.data.get('report_type', 'OTHER'),
                'description': request.data.get('description', '')
            }
            
            serializer = ReviewReportSerializer(data=report_data)
            if serializer.is_valid():
                serializer.save(reported_by=request.user)
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

class ReviewCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for all comment operations
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ReviewComment.objects.filter(
            review_id=self.kwargs['review_pk']
        ).select_related('user', 'user__userprofile')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        try:
            review = get_object_or_404(
                LocationReview,
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
            print(f"Error creating comment: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        try:
            # Print request data for debugging
            print(f"Received comment request data: {request.data}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in create method: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        # Only allow users to delete their own comments
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()
    
    @action(detail=True, methods=['POST'])
    def vote(self, request, pk=None, location_pk=None, review_pk=None):
        """Handle voting on comments"""
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
            
            # Check if user already voted
            existing_vote = CommentVote.objects.filter(
                user=request.user,
                comment=comment
            ).first()
            
            user_vote = None
            if existing_vote:
                if existing_vote.is_upvote == is_upvote:
                    # Same vote type - remove the vote (toggle off)
                    existing_vote.delete()
                    user_vote = None
                else:
                    # Different vote type - update the vote
                    existing_vote.is_upvote = is_upvote
                    existing_vote.save()
                    user_vote = 'up' if is_upvote else 'down'
            else:
                # Create new vote
                CommentVote.objects.create(
                    user=request.user,
                    comment=comment,
                    is_upvote=is_upvote
                )
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
        """Handle reporting comments"""
        try:
            comment = self.get_object()
            
            # Prevent users from reporting their own comments
            if comment.user == request.user:
                return Response(
                    {'detail': 'You cannot report your own comment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already reported this comment
            from stars_app.models.commentreport import CommentReport
            existing_report = CommentReport.objects.filter(
                comment=comment,
                reported_by=request.user
            ).first()
            
            if existing_report:
                return Response(
                    {'detail': 'You have already reported this comment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the report
            report_data = {
                'comment': comment.id,
                'report_type': request.data.get('report_type', 'OTHER'),
                'description': request.data.get('description', '')
            }
            
            serializer = CommentReportSerializer(data=report_data)
            if serializer.is_valid():
                serializer.save(reported_by=request.user)
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


# -------------------------------------------------------------- #
# Additional API ViewSets:

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return User.objects.all()


class FavoriteLocationViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteLocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nickname', 'location__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return FavoriteLocation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewVoteViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewVoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ReviewVote.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ViewingLocationCreateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            # Create new viewing location
            location = ViewingLocation.objects.create(
                name=data['name'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                added_by=request.user
            )

            # The save() method will automatically fetch additional data
            # through the APIs as defined in your model

            # Return the location data
            return JsonResponse({
                'id': location.id,
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'elevation': location.elevation,
                'formatted_address': location.formatted_address,
                'quality_score': location.quality_score
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@login_required
def delete_review(request, review_id):
    # Get the review or return 404
    review = get_object_or_404(LocationReview, pk=review_id)

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

def location_details(request, location_id):
    location = get_object_or_404(ViewingLocation, pk=location_id)
    all_reviews = LocationReview.objects.filter(location=location)

    # Initialize these variables early
    user_has_reviewed = False
    is_owner = False

    if request.user.is_authenticated:
        # Check if user owns the location
        is_owner = location.added_by == request.user

        # Check if user has already reviewed
        user_has_reviewed = all_reviews.filter(user=request.user).exists()

        # Get user's review and other reviews
        user_review = all_reviews.filter(user=request.user).first()
        other_reviews = all_reviews.exclude(user=request.user)
    else:
        user_review = None
        other_reviews = all_reviews

    # Order other reviews by created_at
    other_reviews = other_reviews.order_by('-created_at')

    # Combine reviews and handle pagination
    reviews_list = list(chain([user_review], other_reviews)) if user_review else list(other_reviews)
    reviews_list = [r for r in reviews_list if r is not None]

    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Create vote dictionaries to pass to template
    comment_votes = {}
    
    # Add vote information for authenticated users
    for review in page_obj:
        # Add user-specific vote information only for authenticated users
        if request.user.is_authenticated:
            # Get the vote for this review
            vote = ReviewVote.objects.filter(
                user=request.user,
                review=review
            ).first()

            # Add vote information as an attribute (not a property)
            setattr(review, 'user_vote', 'up' if vote and vote.is_upvote else 'down' if vote else None)
        else:
            setattr(review, 'user_vote', None)

        # Prefetch comments with vote information
        comments = review.comments.all()
        for comment in comments:
            if request.user.is_authenticated:
                # Get user's vote on this comment
                comment_vote = CommentVote.objects.filter(
                    user=request.user,
                    comment=comment
                ).first()
                
                if comment_vote:
                    user_vote_value = 1 if comment_vote.is_upvote else -1
                    comment_votes[comment.id] = user_vote_value
                else:
                    comment_votes[comment.id] = 0
            else:
                comment_votes[comment.id] = 0

    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated and not is_owner:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating:
            review, created = LocationReview.objects.get_or_create(
                location=location,
                user=request.user,
                defaults={'rating': rating, 'comment': comment}
            )
            if not created:
                review.rating = rating
                review.comment = comment
                review.save()
            
            # Handle image uploads
            uploaded_images = request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.reviewphoto import ReviewPhoto
                
                # Validate number of images
                existing_photos_count = review.photos.count()
                if existing_photos_count + len(uploaded_images) > 5:
                    messages.error(request, f'You can only upload up to 5 photos per review. You already have {existing_photos_count} photos.')
                    return redirect('location_details', location_id=location_id)
                
                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5-existing_photos_count]):  # Limit to remaining slots
                    try:
                        ReviewPhoto.objects.create(
                            review=review,
                            image=image,
                            order=existing_photos_count + idx
                        )
                    except Exception as e:
                        messages.error(request, f'Error uploading image: {str(e)}')
            
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('location_details', location_id=location_id)

    # Calculate review statistics
    total_reviews = all_reviews.count()
    if total_reviews > 0:
        from django.db.models import Avg
        avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    else:
        avg_rating = 0
    
    context = {
        'location': location,
        'page_obj': page_obj,
        'user_has_reviewed': user_has_reviewed,
        'is_owner': is_owner,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'total_reviews': total_reviews,
        'average_rating': avg_rating,
        'comment_votes': comment_votes,
    }
    return render(request, 'stars_app/location_details/base.html', context)

@login_required
@require_POST
def update_viewing_nickname(request, favorite_id):
    try:
        favorite = FavoriteLocation.objects.get(id=favorite_id, user=request.user)
        nickname = request.POST.get('nickname')

        favorite.nickname = nickname
        favorite.save()

    except FavoriteLocation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Favorite location not found'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


# -------------------------------------------------------------- #
# Navigation Views:
def home(request):
    from datetime import datetime, timedelta

    # Example test event data:
    next_event = {
        'name': 'Lyrid Meteor Shower',
        'date': datetime.now() + timedelta(days=3, hours=14, minutes=22),
    }

    context = {
        'next_event': next_event,
        'upcoming_events_count': 12,  # Replace with actual query
        'nearby_spots_count': 8,  # Replace with actual query
    }

    return render(request, 'stars_app/home.html', context)

def map(request):
    # Get all locations:
    locations = ViewingLocation.objects.all()

    # Get tile server configuration
    tile_config = get_tile_server_config()

    context = {
        'items': locations,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'tile_server_url': tile_config['public_url'],
    }
    return render(request, 'stars_app/map.html', context)

def get_tile_server_config():
    """Get the tile server URL configuration"""
    return {
        'internal_url': 'http://localhost:3001',
        'public_url': 'http://143.198.25.144:3001'
    }


# -------------------------------------------------------------- #
# User Profile Views:
@login_required(login_url='login')
def account(request, pk):
    user = User.objects.get(pk=pk)

    # Ensure the logged-in user can only view their own profile
    if request.user.pk != pk:
        messages.error(request, 'You can only view your own profile')
        return redirect('account', pk=request.user.pk)

    active_tab = request.GET.get('tab', 'account')

    profile, created = UserProfile.objects.get_or_create(user=user)
    favorites = FavoriteLocation.objects.filter(user=pk)

    context = {
        'favorites': favorites,
        'user_profile': profile,
        'active_tab': active_tab,
        'mapbox_token': 'pk.eyJ1IjoiamN1YmVyZHJ1aWQiLCJhIjoiY20yMHNqODY3MGtqcDJvb2MzMXF3dHczNCJ9.yXIqwWQECN6SYhppPQE3PA',
    }

    # Return the appropriate template based on the active tab
    template_mapping = {
        'profile': 'stars_app/account_profile.html',
        'favorites': 'stars_app/account_favorites.html',
        'preferences': 'stars_app/account_preferences.html'
    }

    return render(request, template_mapping.get(active_tab, 'stars_app/account_profile.html'), context)

@login_required
@require_POST
def upload_profile_picture(request):
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)

        profile_picture = request.FILES['profile_picture']
        user_profile = request.user.userprofile

        # Delete old profile picture if it exists and isn't the default
        if user_profile.profile_picture and 'defaults/' not in user_profile.profile_picture.name:
            if os.path.isfile(user_profile.profile_picture.path):
                os.remove(user_profile.profile_picture.path)

        # Save the file using default storage
        user_profile.profile_picture = profile_picture
        user_profile.save()

        # Return the complete URL
        return JsonResponse({
            'success': True,
            'message': 'Profile picture updated successfully',
            'image_url': user_profile.profile_picture.url
        })
    except Exception as e:
        print(f"Error in upload_profile_picture: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def remove_profile_picture(request):
    try:
        user_profile = request.user.userprofile

        # Delete the current profile picture if it exists
        if user_profile.profile_picture and hasattr(user_profile.profile_picture, 'path'):
            if os.path.isfile(user_profile.profile_picture.path):
                os.remove(user_profile.profile_picture.path)

        # Reset to default
        user_profile.profile_picture = None
        user_profile.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile picture removed successfully',
            'default_image_url': '/static/images/default_profile_pic.jpg'
        })
    except Exception as e:
        print(f"Error removing profile picture: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def update_name(request):
    try:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return JsonResponse({
            'success': True,
            'message': 'Name updated successfully.',
            'first_name': first_name,
            'last_name': last_name
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating name: {str(e)}'
        }, status=400)

@login_required
@require_POST
def change_email(request):
    try:
        new_email = request.POST.get('new_email')

        # Validate the new email:
        if not new_email:
            return JsonResponse({
                'success': False,
                'message': 'Email address is required.'
            }, status=400)

        if not is_valid_email(new_email):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)

        # Check if email is already taken
        if User.objects.filter(email=new_email.lower()).exclude(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email address is already registered.'
            }, status=400)

        # Update the email
        request.user.email = new_email.lower()
        request.user.save()

        return JsonResponse({
            'success': True,
            'message': 'Email updated successfully.',
            'new_email': new_email
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating email: {str(e)}'
        }, status=400)

@login_required
@require_POST
def change_password(request):
    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        print(f"cur: {current_password}")  # Debug print
        print(f"new: {new_password}")  # Debug print

        # Validate inputs
        if not current_password or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'Both current and new passwords are required.'
            }, status=400)

        # Verify current password
        if not request.user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'message': 'Current password is incorrect.'
            }, status=400)

        # Set the new password
        request.user.set_password(new_password)
        request.user.save()

        # Update session to prevent logout
        update_session_auth_hash(request, request.user)

        return JsonResponse({
            'success': True,
            'message': 'Password updated successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating password: {str(e)}'
        }, status=400)


# -------------------------------------------------------------- #
# Authentication Views:
def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            pass1 = request.POST.get('password1')
            pass2 = request.POST.get('password2')

            # Check if the username already exists in our database:
            if User.objects.filter(username=username.lower()).exists():
                messages.error(request, 'Username already exists...')
                return redirect('register')

            # Check if the email already exists:
            if User.objects.filter(email=email.lower()).exists():
                messages.error(request, 'Email is already registered.')
                return redirect('register')

            # Validate email format:
            if not is_valid_email(email):
                messages.error(request, 'Please enter a valid email address.')
                return redirect('register')

            # Check if the password confirmation doesn't match:
            if pass1 != pass2:
                messages.error(request, 'Passwords do not match...')
                return redirect('register')

            # We are creating a user after verifying everything is correct:
            user = User.objects.create_user(
                username=username.lower(),
                email=email,
                password=pass1,
                first_name=first_name,
                last_name=last_name
            )

            # Create default profile picture directory if it doesn't exist:
            profile_pics_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
            if not os.path.exists(profile_pics_dir):
                os.makedirs(profile_pics_dir)

            # Notify the user that their account has been created successfully:
            messages.success(request, 'Account created successfully')
            return redirect('login')

        except Exception as e:
            # Display a message to the user that registration was unsuccessful:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register')

    # If we didn't call a post method, direct user to register page:
    return render(request, 'stars_app/register.html')

def custom_login(request):
    if request.method == 'POST':
        try:
            username_or_email = request.POST.get('username').lower()
            password = request.POST.get('password')
            next_url = request.POST.get('next', '')

            # Try to get user by username or email
            user = User.objects.filter(
                Q(username=username_or_email) |
                Q(email=username_or_email)
            ).first()

            # Check for the case that the user doesn't exist in our database:
            if not user:
                messages.error(request, 'No account found with that username or email.')
                return redirect('login')

            # Authenticate with username
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                messages.success(request, f'Logged in successfully as {user.username}')

                login(request, user)

                if next_url and next_url.strip() and not next_url.startswith('/login/'):
                    return redirect(next_url)

                return redirect('home')

            # If user couldn't authenticate above, display wrong password message:
            messages.error(request, 'Invalid password.')
            return redirect('login')

        except Exception as e:
            messages.error(request, 'An error occurred while trying to log in. Please try again.')
            return redirect('login')

    # If we didn't call a post method, direct user to login page:
    next_url = request.GET.get('next', '')
    if next_url.startswith('/login/'):
        next_url = ''

    return render(request, 'stars_app/login.html', {'next': next_url})

@login_required(login_url='login')
def custom_logout(request):
    messages.success(request, f'Logged out successfully...')
    logout(request)
    return redirect('home')


# -------------------------------------------------------------- #
# Password Reset Views:
class CustomPasswordResetView(PasswordResetView):
    template_name = 'stars_app/password_reset.html'
    email_template_name = 'stars_app/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'stars_app/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'stars_app/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'stars_app/password_reset_complete.html'