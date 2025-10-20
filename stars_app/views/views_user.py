# ----------------------------------------------------------------------------------------------------- #
# This views_user.py file handles all user profile-related views and API endpoints:                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints and function-based views for managing user profiles and account          #
# settings. Handles profile pictures, personal information updates, and account preferences.           #
#                                                                                                       #
# Key Features:                                                                                         #
# - UserViewSet: Read-only API for user information                                                    #
# - UserProfileViewSet: Full CRUD API for user profile data                                            #
# - Profile picture management: Upload and remove profile pictures with automatic cleanup              #
# - Account settings: Update name, email, and password with validation                                 #
# - Tab-based interface: Separate views for profile, favorites, and preferences                        #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                              #
# - Function-based views for form submissions and AJAX updates                                         #
# - Integrates with Django's authentication system for password management                             #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# REST Framework imports:
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

# Model imports:
from django.contrib.auth.models import User
from ..models import UserProfile
from ..models import FavoriteLocation

# Serializer imports:
from stars_app.serializers import UserSerializer, UserProfileSerializer

# Other imports:
import os



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                         API VIEWSETS                                                  #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing user profiles.

    Provides endpoints for viewing and updating user profile information.
    Users can only access their own profile data.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter to only show the current user's profile."""
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create a profile for the current user."""
        serializer.save(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API ViewSet for user information.

    Provides endpoints for viewing user data but not modifying it.
    Used for displaying user information in reviews, comments, etc.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Return all users."""
        return User.objects.all()


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                  FUNCTION-BASED VIEWS                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

@login_required(login_url='login')
def account(request, pk):
    """
    Display user account page with tabs for profile, favorites, and preferences.

    Args:
        request: HTTP request object
        pk: User primary key

    Returns:
        Rendered account page template based on active tab
    """
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
    """
    Upload a new profile picture for the current user.

    Deletes the old profile picture (if not default) and saves the new one.

    Returns:
        JsonResponse with success status and new image URL
    """
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({'error': 'No image file provided'}, status=400)

        profile_picture = request.FILES['profile_picture']
        user_profile = request.user.userprofile

        # Delete old profile picture if it exists and isn't the default
        if user_profile.profile_picture and 'defaults/' not in user_profile.profile_picture.name:
            if os.path.isfile(user_profile.profile_picture.path):
                os.remove(user_profile.profile_picture.path)

        # Save the new profile picture
        user_profile.profile_picture = profile_picture
        user_profile.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile picture updated successfully',
            'image_url': user_profile.profile_picture.url
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def remove_profile_picture(request):
    """
    Remove the current user's profile picture and reset to default.

    Returns:
        JsonResponse with success status and default image URL
    """
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
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def update_name(request):
    """
    Update the current user's first and last name.

    Returns:
        JsonResponse with success status and updated name
    """
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
    """
    Update the current user's email address with validation.

    Validates email format and checks for duplicates before updating.

    Returns:
        JsonResponse with success status and new email
    """
    try:
        new_email = request.POST.get('new_email')

        # Validate the new email
        if not new_email:
            return JsonResponse({
                'success': False,
                'message': 'Email address is required.'
            }, status=400)

        # Validate email format using Django's built-in validator
        try:
            validate_email(new_email)
        except ValidationError:
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
    """
    Update the current user's password with validation.

    Verifies the current password before setting the new one and maintains
    the user's session after password change.

    Returns:
        JsonResponse with success status
    """
    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

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
