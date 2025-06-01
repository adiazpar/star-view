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
from stars_app.serializers import *

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

# -------------------------------------------------------------- #
# Location Management Views:
class CelestialEventViewSet(viewsets.ModelViewSet):
    queryset = CelestialEvent.objects.all()
    serializer_class = CelestialEventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Set elevation to 0 if not provided
        serializer.save(elevation=serializer.validated_data.get('elevation', 0))


# -------------------------------------------------------------- #
# Viewing Location Views:

class ViewingLocationViewSet(viewsets.ModelViewSet):
    queryset = ViewingLocation.objects.all()
    serializer_class = ViewingLocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

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

        serializer.save(
            added_by=self.request.user,
        )

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

    @action(detail=True, methods=['POST', 'GET'])
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

    @action(detail=True, methods=['POST', 'GET'])
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
            serializer.save(user=request.user, location=location)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['PUT'])
    def update_review(self, request, pk=None):
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

        serializer = LocationReviewSerializer(review, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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

        # Return serialized review data with updated vote information
        serializer = self.get_serializer(review)
        return Response(serializer.data)

class ReviewCommentViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewCommentSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for all comment operations

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
                'light_pollution_value': location.light_pollution_value,
                'cloudCoverPercentage': location.cloudCoverPercentage,
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

    # Add vote information
    if request.user.is_authenticated:
        for review in page_obj:
            # Get the vote for this review
            vote = ReviewVote.objects.filter(
                user=request.user,
                review=review
            ).first()

            # Add vote information as an attribute (not a property)
            setattr(review, 'user_vote', 'up' if vote and vote.is_upvote else 'down' if vote else None)

            # Calculate vote count
            upvotes = review.votes.filter(is_upvote=True).count()
            downvotes = review.votes.filter(is_upvote=False).count()
            setattr(review, 'vote_counts', upvotes - downvotes)  # Using setattr instead of direct assignment

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
            return redirect('location_details', location_id=location_id)

    context = {
        'location': location,
        'page_obj': page_obj,
        'user_has_reviewed': user_has_reviewed,  # Fixed: Don't append 'is not None'
        'is_owner': is_owner,
        'mapbox_token': settings.MAPBOX_TOKEN,
    }
    return render(request, 'stars_app/location_details.html', context)

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
# Update All Forecasts Button on Upload Page
@staff_member_required
def update_forecast(request):
    locations = ViewingLocation.objects.all()

    for loc in locations:
        loc.updateForecast()

    return render(request, 'stars_app/upload_tif.html')


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
    # Get all locations and events:
    locations = ViewingLocation.objects.all()
    events = CelestialEvent.objects.all()

    # Get tile server configuration
    tile_config = get_tile_server_config()

    # Combine all items into one list:
    combined_items = list(locations) + list(events)

    context = {
        'items': combined_items,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'tile_server_config': tile_config['public_url'],
    }
    return render(request, 'stars_app/map.html', context)

def get_tile_server_config():
    """Get the appropriate tile server URL based on environment"""
    import socket
    
    # Check if we're running in Docker by trying to resolve the service name
    try:
        socket.gethostbyname('tile-server')
        # We're in Docker, use internal URL for server calls, public for browser
        return {
            'internal_url': 'http://tile-server:3001',
            'public_url': 'http://localhost:3001'  # This should be accessible from the browser
        }
    except socket.gaierror:
        # Not in Docker, use localhost for everything
        return {
            'internal_url': 'http://localhost:3001',
            'public_url': 'http://localhost:3001'
        }

def event_list(request):
    event_list = CelestialEvent.objects.all()
    return render(request, 'stars_app/list.html', {'events':event_list})

def details(request, event_id):
    event = CelestialEvent.objects.get(pk=event_id)
    viewing_locations = ViewingLocation.objects.all()

    closet_loc = viewing_locations[0]
    for loc in viewing_locations:
        event_point = (event.latitude, event.longitude)
        closest_point = (closet_loc.latitude, closet_loc.longitude)
        current_point = (loc.latitude, loc.longitude)

        closest_distance = geodesic(event_point, closest_point).kilometers
        current_distance = geodesic(event_point, current_point).kilometers
        if current_distance < closest_distance:
            closet_loc = loc

    current_data = {
        'event': event,
        'view_loc': closet_loc
    }
    return render(request, 'stars_app/details.html', current_data)


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
        'notifications': 'stars_app/account_notifications.html',
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