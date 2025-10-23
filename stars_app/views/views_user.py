# ----------------------------------------------------------------------------------------------------- #
# This views_user.py file handles user profile and account management views:                            #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides user-facing functionality for managing account settings, profiles, and authentication.       #
# Separates user management views from authentication (login/register) and content views (locations).   #
#                                                                                                       #
# Key Features:                                                                                         #
# - Account Management: Tabbed interface for profile and favorites                                      #
# - Profile Updates: AJAX endpoints for profile pictures, names, email, and passwords                   #
# - Password Security: Integrates with PasswordService for consistent validation across the app         #
# - Response Handling: Uses ResponseService for standardized JSON responses                             #
#                                                                                                       #
# Architecture:                                                                                         #
# - Function-based views for account page and AJAX update endpoints                                     #
# - Uses PasswordService for all password operations (single source of truth)                           #
# - Uses ResponseService for consistent error and success responses                                     #
# - Uses safe_delete_file from signals for secure file deletion with MEDIA_ROOT validation              #
# - Optimized database queries with select_related to prevent N+1 query problems                        #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings

# DRF imports:
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# Model imports:
from django.contrib.auth.models import User
from ..models import UserProfile
from ..models import FavoriteLocation

# Service imports:
from stars_app.services import PasswordService, ResponseService

# Signal utility imports:
from stars_app.signals import safe_delete_file



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                           USER METHODS                                                #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Display user account page with tabbed interface for profile and favorites.    #
# Active tab determined by 'tab' query parameter.                               #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  Rendered account page template based on active tab                  #
# ----------------------------------------------------------------------------- #
@login_required(login_url='login')
def account(request):
    user = request.user
    active_tab = request.GET.get('tab', 'profile')

    # Optimize: Use select_related to fetch Location data with favorites (prevents N+1)
    favorites = FavoriteLocation.objects.filter(user=user).select_related('location')

    context = {
        'favorites': favorites,
        'user_profile': user.userprofile,
        'active_tab': active_tab,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'default_profile_picture': settings.DEFAULT_PROFILE_PICTURE,
    }

    # Return the appropriate template based on the active tab
    template_mapping = {
        'profile': 'stars_app/account_profile.html',
        'favorites': 'stars_app/account_favorites.html',
    }

    return render(request, template_mapping.get(active_tab, 'stars_app/account_profile.html'), context)


# ----------------------------------------------------------------------------- #
# Upload new profile picture via DRF API. Automatically deletes old custom      #
# images (preserves default images) before saving the new one.                  #
#                                                                               #
# Args:     request: POST request with 'profile_picture' file                   #
# Returns:  DRF Response with success status and new image URL                  #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_picture(request):
    try:
        if 'profile_picture' not in request.FILES:
            return ResponseService.error('No image file provided', status_code=status.HTTP_400_BAD_REQUEST)

        profile_picture = request.FILES['profile_picture']
        user_profile = request.user.userprofile

        # Delete old profile picture if it exists (None means using default, so nothing to delete)
        if user_profile.profile_picture and hasattr(user_profile.profile_picture, 'path'):
            safe_delete_file(user_profile.profile_picture.path)

        # Save the new profile picture
        user_profile.profile_picture = profile_picture
        user_profile.save()

        return ResponseService.success(
            'Profile picture updated successfully',
            data={'image_url': user_profile.profile_picture.url}
        )
    except Exception as e:
        return ResponseService.error(str(e), status_code=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------------------------------------------- #
# Remove profile picture via DRF API. Deletes the file and resets to default.  #
#                                                                               #
# Args:     request: POST request from API call                                 #
# Returns:  DRF Response with success status and default image URL              #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_profile_picture(request):
    try:
        user_profile = request.user.userprofile

        # Delete the current profile picture if it exists (None means using default)
        if user_profile.profile_picture and hasattr(user_profile.profile_picture, 'path'):
            safe_delete_file(user_profile.profile_picture.path)

        # Reset to default (model returns default URL when profile_picture is None)
        user_profile.profile_picture = None
        user_profile.save()

        return ResponseService.success(
            'Profile picture removed successfully',
            data={'default_image_url': user_profile.get_profile_picture_url}
        )
    except Exception as e:
        return ResponseService.error(str(e), status_code=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------------------------------------------- #
# Update user's first and last name via DRF API.                                #
#                                                                               #
# Args:     request: POST request with first_name and last_name                 #
# Returns:  DRF Response with success status and updated names                  #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_name(request):
    try:
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()

        # Validate required fields
        if not first_name or not last_name:
            return ResponseService.error('Both first and last name are required.', status_code=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return ResponseService.success(
            'Name updated successfully.',
            data={
                'first_name': first_name,
                'last_name': last_name
            }
        )
    except Exception as e:
        return ResponseService.error(f'Error updating name: {str(e)}', status_code=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------------------------------------------- #
# Update user's email via DRF API. Validates format and checks for duplicates   #
# before updating (case-insensitive).                                           #
#                                                                               #
# Args:     request: POST request with new_email                                #
# Returns:  DRF Response with success status and new email                      #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_email(request):
    try:
        new_email = request.data.get('new_email', '').strip()

        # Validate the new email
        if not new_email:
            return ResponseService.error('Email address is required.', status_code=status.HTTP_400_BAD_REQUEST)

        # Validate email format using Django's built-in validator
        try:
            validate_email(new_email)
        except ValidationError:
            return ResponseService.error('Please enter a valid email address.', status_code=status.HTTP_400_BAD_REQUEST)

        # Check if email is already taken
        if User.objects.filter(email=new_email.lower()).exclude(id=request.user.id).exists():
            return ResponseService.error('This email address is already registered.', status_code=status.HTTP_400_BAD_REQUEST)

        # Update the email
        request.user.email = new_email.lower()
        request.user.save()

        return ResponseService.success(
            'Email updated successfully.',
            data={'new_email': new_email}
        )

    except Exception as e:
        return ResponseService.error(f'Error updating email: {str(e)}', status_code=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------------------------------------------- #
# Update user's password via DRF API. Verifies current password, validates new  #
# password strength with PasswordService, and maintains session.                #
#                                                                               #
# Args:     request: POST request with current_password and new_password        #
# Returns:  DRF Response with success status or validation error                #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        # Validate inputs
        if not current_password or not new_password:
            return ResponseService.error('Both current and new passwords are required.', status_code=status.HTTP_400_BAD_REQUEST)

        # Use PasswordService to validate and change password
        success, error_message = PasswordService.change_password(
            user=request.user,
            current_password=current_password,
            new_password=new_password
        )

        if not success:
            return ResponseService.error(error_message, status_code=status.HTTP_400_BAD_REQUEST)

        # Update session to prevent logout after password change
        update_session_auth_hash(request, request.user)

        return ResponseService.success('Password updated successfully.')

    except Exception as e:
        return ResponseService.error(f'Error updating password: {str(e)}', status_code=status.HTTP_400_BAD_REQUEST)
