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
        # Pass the FileField object directly (works with both local and R2/S3 storage)
        if user_profile.profile_picture:
            safe_delete_file(user_profile.profile_picture)

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
        # Pass the FileField object directly (works with both local and R2/S3 storage)
        if user_profile.profile_picture:
            safe_delete_file(user_profile.profile_picture)

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
    # Update user's username.                                                       #
    #                                                                               #
    # Validates username format and uniqueness before updating.                     #
    # Username requirements:                                                        #
    # - 3-30 characters                                                             #
    # - Alphanumeric, underscores, and hyphens only                                 #
    # - Must be unique across all users                                             #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-username/                                       #
    # Body: JSON with new_username                                                  #
    # Returns: DRF Response with success status and updated username                #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-username')
    def update_username(self, request):
        import re
        new_username = request.data.get('new_username', '').strip().lower()

        # Validate required field
        if not new_username:
            raise exceptions.ValidationError('Username is required.')

        # Validate length
        if len(new_username) < 3:
            raise exceptions.ValidationError('Username must be at least 3 characters.')
        if len(new_username) > 30:
            raise exceptions.ValidationError('Username must be 30 characters or less.')

        # Validate format (alphanumeric, underscore, hyphen only)
        if not re.match(r'^[a-z0-9_-]+$', new_username):
            raise exceptions.ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')

        # Check if username is already taken
        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            raise exceptions.ValidationError('This username is already taken.')

        # Update username
        user = request.user
        user.username = new_username
        user.save()

        return Response({
            'detail': 'Username updated successfully.',
            'username': new_username
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Update user's email address with verification flow.                           #
    #                                                                               #
    # Security: Requires verification of new email before change takes effect.      #
    # Process:                                                                      #
    # 1. Validate new email format and uniqueness                                   #
    # 2. Send notification to current email address                                 #
    # 3. Create unverified EmailAddress record for new email                        #
    # 4. Send verification link to new email address                                #
    # 5. User clicks link to confirm and complete email change                      #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-email/                                          #
    # Body: JSON with new_email                                                     #
    # Returns: DRF Response with verification instructions                          #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-email')
    def update_email(self, request):
        from allauth.account.models import EmailAddress
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string

        new_email = request.data.get('new_email', '').strip()

        # Validate the new email
        if not new_email:
            raise exceptions.ValidationError('Email address is required.')

        # Validate email format using Django's built-in validator
        try:
            validate_email(new_email)
        except ValidationError:
            raise exceptions.ValidationError('Please enter a valid email address.')

        # Check if this is the same as current email
        if request.user.email.lower() == new_email.lower():
            raise exceptions.ValidationError('This is already your current email address.')

        # Check if email is already taken by another user
        if User.objects.filter(email=new_email.lower()).exclude(id=request.user.id).exists():
            raise exceptions.ValidationError('This email address is already registered.')

        # Check if email is already in use by a social account (from ANY user including self)
        from allauth.socialaccount.models import SocialAccount
        for social_account in SocialAccount.objects.all():
            social_email = social_account.extra_data.get('email', '').lower()
            if social_email == new_email.lower():
                # Block the change - this email is used by a social account
                raise exceptions.ValidationError('This email address is already registered.')

        # Check if email has a pending verification (unverified EmailAddress record)
        # This prevents race conditions where multiple users try to claim the same email
        pending_email = EmailAddress.objects.filter(
            email=new_email.lower(),
            verified=False
        ).exclude(user=request.user).first()

        if pending_email:
            raise exceptions.ValidationError('This email address is already registered.')

        # Send notification to old email address
        old_email = request.user.email
        if old_email:
            subject = 'Email Address Change Request - Starview'
            context = {
                'user': request.user,
                'old_email': old_email,
                'new_email': new_email,
                'site_name': 'Starview',
            }

            html_content = render_to_string('starview_app/auth/email/email_change_notification.html', context)
            text_content = render_to_string('starview_app/auth/email/email_change_notification.txt', context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[old_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)

        # Get or create EmailAddress record for new email (unverified)
        email_address, created = EmailAddress.objects.get_or_create(
            user=request.user,
            email=new_email.lower(),
            defaults={'verified': False, 'primary': False}
        )

        # If email already exists and is verified, make it primary immediately
        if not created and email_address.verified:
            email_address.set_as_primary()
            # Update User model email
            request.user.email = new_email.lower()
            request.user.save()
            return Response({
                'detail': 'Email updated successfully.',
                'new_email': new_email,
                'verification_required': False
            }, status=status.HTTP_200_OK)

        # Email is unverified, send verification email
        email_address.send_confirmation(request)

        return Response({
            'detail': f'Verification email sent to {new_email}. Please check your inbox and click the verification link to complete the email change.',
            'verification_required': True,
            'new_email': new_email
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Update user's password. Verifies current password and validates new password. #
    #                                                                               #
    # Handles two scenarios:                                                        #
    # 1. User has existing password → Requires current_password for verification   #
    # 2. User has no password (OAuth signup) → Sets first password without current #
    #                                                                               #
    # HTTP Method: PATCH                                                            #
    # Endpoint: /api/profile/update-password/                                       #
    # Body: JSON with new_password and optional current_password                    #
    # Returns: DRF Response with success status or validation error                 #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['patch'], url_path='update-password')
    def update_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        # Validate new password is provided
        if not new_password:
            raise exceptions.ValidationError('New password is required.')

        # Check if user has a usable password (not OAuth-only account)
        if request.user.has_usable_password():
            # User has existing password - require current password for verification
            if not current_password:
                raise exceptions.ValidationError('Current password is required.')

            # Use PasswordService to validate and change password
            success, error_message = PasswordService.change_password(
                user=request.user,
                current_password=current_password,
                new_password=new_password
            )
        else:
            # User has no password (OAuth signup) - set first password
            success, error_message = PasswordService.set_password(
                user=request.user,
                new_password=new_password
            )

        if not success:
            raise exceptions.ValidationError(error_message)

        # Update session to prevent logout after password change
        update_session_auth_hash(request, request.user)

        return Response({
            'detail': 'Password updated successfully.'
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Get user's connected social accounts (Google OAuth, etc.)                     #
    #                                                                               #
    # Returns list of social accounts linked to the user with provider info,        #
    # email from the provider, and connection date.                                 #
    #                                                                               #
    # HTTP Method: GET                                                              #
    # Endpoint: /api/profile/social-accounts/                                       #
    # Returns: DRF Response with array of social account data                       #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['get'], url_path='social-accounts')
    def social_accounts(self, request):
        from allauth.socialaccount.models import SocialAccount

        accounts = SocialAccount.objects.filter(user=request.user)

        account_data = []
        for account in accounts:
            # Get email from provider's extra data
            provider_email = account.extra_data.get('email', 'N/A')

            # Get provider display name
            provider_name = account.provider.title()

            account_data.append({
                'id': account.id,
                'provider': account.provider,
                'provider_name': provider_name,
                'email': provider_email,
                'connected_at': account.date_joined,
                'uid': account.uid,
            })

        return Response({
            'social_accounts': account_data,
            'count': len(account_data)
        }, status=status.HTTP_200_OK)


    # ----------------------------------------------------------------------------- #
    # Disconnect a social account from user's profile                               #
    #                                                                               #
    # Removes the link between user and a specific OAuth provider. User must have   #
    # alternative login method (password) before disconnecting social account.      #
    #                                                                               #
    # HTTP Method: DELETE                                                           #
    # Endpoint: /api/profile/disconnect-social/{account_id}/                        #
    # Returns: DRF Response with success status                                     #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['delete'], url_path='disconnect-social/(?P<account_id>[^/.]+)')
    def disconnect_social(self, request, account_id=None):
        from allauth.socialaccount.models import SocialAccount

        try:
            account = SocialAccount.objects.get(id=account_id, user=request.user)
        except SocialAccount.DoesNotExist:
            raise exceptions.NotFound('Social account not found.')

        # Check if user has a password (can't disconnect if no alternative login method)
        if not request.user.has_usable_password():
            raise exceptions.ValidationError(
                'Cannot disconnect social account. Please set a password first to ensure you can still login.'
            )

        # Store provider name for response
        provider_name = account.provider.title()

        # Delete the social account
        account.delete()

        return Response({
            'detail': f'{provider_name} account disconnected successfully.',
            'provider': account.provider
        }, status=status.HTTP_200_OK)
