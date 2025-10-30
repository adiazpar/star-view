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
# - Error Handling: Uses DRF exceptions caught by the global exception handler                          #
#                                                                                                       #
# Architecture:                                                                                         #
# - Function-based views for account page and AJAX update endpoints                                     #
# - Uses PasswordService for all password operations (single source of truth)                           #
# - Uses DRF exceptions for consistent error responses via exception handler                            #
# - Uses safe_delete_file from signals for secure file deletion with MEDIA_ROOT validation              #
# - Optimized database queries with select_related to prevent N+1 query problems                        #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings

# DRF imports:
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response

# Model imports:
from django.contrib.auth.models import User
from ..models import UserProfile
from ..models import FavoriteLocation

# Service imports:
from starview_app.services import PasswordService

# Signal utility imports:
from starview_app.utils.signals import safe_delete_file



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                      USER PROFILE VIEWSET                                             #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# REST API ViewSet for user profile management operations.                      #
#                                                                               #
# This ViewSet provides a RESTful API for managing user profile data including  #
# profile pictures, names, email, and passwords. All endpoints require          #
# authentication and operate on the authenticated user's profile.               #
#                                                                               #
# Architecture:                                                                 #
# - All actions raise DRF exceptions for consistent error handling              #
# - Password operations use PasswordService for validation                      #
# - File deletion uses safe_delete_file from signals module                     #
# - Uses DRF's @action decorator for custom endpoints                           #
# ----------------------------------------------------------------------------- #
class UserProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # ----------------------------------------------------------------------------- #
    # Upload new profile picture. Automatically deletes old custom images           #
    # (preserves default images) before saving the new one.                         #
    #                                                                               #
    # Security: Validates file size (5MB max), MIME type, and extension before      #
    # processing to prevent malicious file uploads and DOS attacks.                 #
    #                                                                               #
    # HTTP Method: POST                                                             #
    # Endpoint: /api/profile/upload-picture/                                        #
    # Body: multipart/form-data with 'profile_picture' file                         #
    # Returns: DRF Response with success status and new image URL                   #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['post'], url_path='upload-picture')
    def upload_picture(self, request):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from starview_app.utils import validate_file_size, validate_image_file

        if 'profile_picture' not in request.FILES:
            raise exceptions.ValidationError('No image file provided')

        profile_picture = request.FILES['profile_picture']

        # Validate file before processing
        try:
            validate_file_size(profile_picture)
            validate_image_file(profile_picture)
        except DjangoValidationError as e:
            raise exceptions.ValidationError(str(e))

        user_profile = request.user.userprofile

        # Delete old profile picture if it exists (None means using default, so nothing to delete)
        if user_profile.profile_picture and hasattr(user_profile.profile_picture, 'path'):
            safe_delete_file(user_profile.profile_picture.path)

        # Save the new profile picture
        user_profile.profile_picture = profile_picture
        user_profile.save()

        return Response({
            'detail': 'Profile picture updated successfully',
            'image_url': user_profile.profile_picture.url
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Remove profile picture and reset to default.                                  #
    #                                                                               #
    # HTTP Method: DELETE                                                           #
    # Endpoint: /api/profile/remove-picture/                                        #
    # Returns: DRF Response with success status and default image URL               #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['delete'], url_path='remove-picture')
    def remove_picture(self, request):
        user_profile = request.user.userprofile

        # Delete the current profile picture if it exists (None means using default)
        if user_profile.profile_picture and hasattr(user_profile.profile_picture, 'path'):
            safe_delete_file(user_profile.profile_picture.path)

        # Reset to default (model returns default URL when profile_picture is None)
        user_profile.profile_picture = None
        user_profile.save()

        return Response({
            'detail': 'Profile picture removed successfully',
            'default_image_url': user_profile.get_profile_picture_url
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Update user's first and last name.                                            #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-name/                                           #
    # Body: JSON with first_name and last_name                                      #
    # Returns: DRF Response with success status and updated names                   #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-name')
    def update_name(self, request):
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()

        # Validate required fields
        if not first_name or not last_name:
            raise exceptions.ValidationError('Both first and last name are required.')

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return Response({
            'detail': 'Name updated successfully.',
            'first_name': first_name,
            'last_name': last_name
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Update user's email address. Validates format and checks for duplicates.      #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-email/                                          #
    # Body: JSON with new_email                                                     #
    # Returns: DRF Response with success status and new email                       #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-email')
    def update_email(self, request):
        new_email = request.data.get('new_email', '').strip()

        # Validate the new email
        if not new_email:
            raise exceptions.ValidationError('Email address is required.')

        # Validate email format using Django's built-in validator
        try:
            validate_email(new_email)
        except ValidationError:
            raise exceptions.ValidationError('Please enter a valid email address.')

        # Check if email is already taken
        if User.objects.filter(email=new_email.lower()).exclude(id=request.user.id).exists():
            raise exceptions.ValidationError('This email address is already registered.')

        # Update the email
        request.user.email = new_email.lower()
        request.user.save()

        return Response({
            'detail': 'Email updated successfully.',
            'new_email': new_email
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Update user's password. Verifies current password and validates new password. #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-password/                                       #
    # Body: JSON with current_password and new_password                             #
    # Returns: DRF Response with success status or validation error                 #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-password')
    def update_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        # Validate inputs
        if not current_password or not new_password:
            raise exceptions.ValidationError('Both current and new passwords are required.')

        # Use PasswordService to validate and change password
        success, error_message = PasswordService.change_password(
            user=request.user,
            current_password=current_password,
            new_password=new_password
        )

        if not success:
            raise exceptions.ValidationError(error_message)

        # Update session to prevent logout after password change
        update_session_auth_hash(request, request.user)

        return Response({
            'detail': 'Password updated successfully.'
        }, status=status.HTTP_200_OK)
