# ----------------------------------------------------------------------------------------------------- #
# This views_auth.py file handles all authentication-related views:                                     #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides user authentication functionality including registration, login, logout, and password        #
# reset. Uses DRF exceptions for consistent error handling via the global exception handler.            #
#                                                                                                       #
# Key Features:                                                                                         #
# - User registration: AJAX endpoint with validation, duplicate checking, and password strength rules   #
# - Login: AJAX endpoint supporting username or email authentication                                    #
# - Logout: End user sessions and redirect to home                                                      #
# - Password reset: Email-based password recovery workflow with Django's built-in views                 #
# - Unified error handling: All errors raise DRF exceptions caught by the exception handler             #
#                                                                                                       #
# Architecture:                                                                                         #
# - AJAX-enabled function-based views for registration and login (with fallback rendering)              #
# - Function-based logout view with login requirement                                                   #
# - Class-based views for Django's password reset workflow                                              #
# - Integrates with PasswordService for centralized password validation                                 #
# - Integrates with global exception handler for standardized JSON error responses                      #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.db.models import Q
from django.db import transaction

# DRF imports:
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, exceptions
from rest_framework.response import Response

# django-axes imports for account lockout:
from axes.exceptions import AxesBackendPermissionDenied
from axes.handlers.proxy import AxesProxyHandler

# Service imports:
from starview_app.services import PasswordService
from starview_app.utils import LoginRateThrottle, log_auth_event



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    REGISTRATION & LOGIN                                               #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Handle user registration with validation.                                     #
#                                                                               #
# DRF API endpoint that validates username uniqueness, email format and         #
# uniqueness, password confirmation and strength. Creates a new user account    #
# and returns JSON response with success status and redirect URL.               #
#                                                                               #
# Throttling: Limited to 5 requests per minute to prevent abuse                 #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  Rendered registration page (GET) or DRF Response (POST)             #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def register(request):
        # Get form data
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        pass1 = request.data.get('password1', '')
        pass2 = request.data.get('password2', '')

        # Validate required fields
        if not all([username, email, first_name, last_name, pass1, pass2]):
            raise exceptions.ValidationError('All fields are required.')

        # Validate username uniqueness
        if User.objects.filter(username=username.lower()).exists():
            raise exceptions.ValidationError('This username is already taken.')

        # Validate email format using Django's built-in validator
        try:
            validate_email(email)
        except ValidationError:
            raise exceptions.ValidationError('Please enter a valid email address.')

        # Validate email uniqueness
        if User.objects.filter(email=email.lower()).exists():
            raise exceptions.ValidationError('This email address is already registered.')

        # Validate that passwords match
        passwords_match, match_error = PasswordService.validate_passwords_match(pass1, pass2)
        if not passwords_match:
            raise exceptions.ValidationError(match_error)

        # Prepare user data (DRY - used for both validation and creation)
        user_data = {
            'username': username.lower(),
            'email': email.lower(),
            'first_name': first_name,
            'last_name': last_name
        }

        # Create temporary user instance for context-aware password validation
        temp_user = User(**user_data)

        # Validate password strength (context-aware using temp_user)
        password_valid, validation_error = PasswordService.validate_password_strength(pass1, user=temp_user)
        if not password_valid:
            raise exceptions.ValidationError(validation_error)

        # Wrap user creation and email sending in a transaction
        # If email sending fails, user creation will be rolled back
        from allauth.account.models import EmailAddress, EmailConfirmation

        with transaction.atomic():
            # Create user after all validation passes
            user = User.objects.create_user(
                **user_data,
                password=pass1
            )

            # Create EmailAddress entry for django-allauth (always unverified)
            email_address = EmailAddress.objects.create(
                user=user,
                email=email.lower(),
                verified=False,  # Always require email verification
                primary=True
            )

            # Always send verification email (mandatory verification)
            confirmation = EmailConfirmation.create(email_address)
            confirmation.send(request, signup=True)

            # Audit log: Successful registration
            log_auth_event(
                request=request,
                event_type='registration_success',
                user=user,
                success=True,
                message=f'New user registered (email verification required): {user.username}',
                metadata={'email': user.email, 'verified': False}
            )

            return Response({
                'detail': 'Account created! Please check your email to verify your account before logging in.',
                'email_sent': True,
                'requires_verification': True
            }, status=status.HTTP_201_CREATED)


# ----------------------------------------------------------------------------- #
# Handle user login with username or email.                                     #
#                                                                               #
# DRF API endpoint that authenticates users using either their username or      #
# email. Returns JSON response with success status and redirect URL.            #
#                                                                               #
# Throttling: Limited to 5 requests per minute to prevent brute force attacks   #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  Rendered login page (GET) or DRF Response (POST)                    #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def custom_login(request):
        # Get form data
        username_or_email = request.data.get('username', '').strip().lower()
        password = request.data.get('password', '')
        next_url = request.data.get('next', '').strip()

        # Validate required fields
        if not username_or_email or not password:
            raise exceptions.ValidationError('Username and password are required.')

        # Check if request is already locked out.
        # This prevents further authentication attempts when account is locked
        if AxesProxyHandler.is_locked(request):
            # Audit log: Login attempt while locked
            log_auth_event(
                request=request,
                event_type='login_locked',
                username=username_or_email,
                success=False,
                message=f'Login attempt blocked - account locked: {username_or_email}',
                metadata={'reason': 'account_locked'}
            )
            raise exceptions.PermissionDenied(
                'Account locked due to too many login attempts. Please try again later.'
            )

        # Try to get user by username or email
        user_obj = User.objects.filter(
            Q(username=username_or_email) |
            Q(email=username_or_email)
        ).first()

        # Use generic error message to prevent user enumeration
        # Don't reveal whether the username/email exists or password is wrong
        generic_error = 'Invalid username or password.'

        # If user doesn't exist, return generic error (prevents user enumeration)
        if not user_obj:
            # Audit log: Failed login - user not found
            log_auth_event(
                request=request,
                event_type='login_failed',
                username=username_or_email,
                success=False,
                message=f'Login failed - user not found: {username_or_email}',
                metadata={'reason': 'user_not_found'}
            )
            # Use 400 instead of 401 to prevent browser's HTTP auth dialog
            raise exceptions.ValidationError(generic_error)

        # Authenticate with username (django-axes intercepts this call)
        # Phase 4: Account Lockout - AxesBackendPermissionDenied raised if account is locked
        try:
            authenticated_user = authenticate(request, username=user_obj.username, password=password)
        except AxesBackendPermissionDenied:
            # Account is locked out due to too many failed attempts
            # Audit log: Login attempt while locked (triggered by axes)
            log_auth_event(
                request=request,
                event_type='login_locked',
                username=user_obj.username,
                success=False,
                message=f'Login attempt blocked - account locked: {user_obj.username}',
                metadata={'reason': 'account_locked_by_axes'}
            )
            raise exceptions.PermissionDenied(
                'Account locked due to too many login attempts. Please try again later.'
            )

        if authenticated_user is not None:
            # Check email verification requirement (always enforced)
            from allauth.account.models import EmailAddress
            try:
                email_address = EmailAddress.objects.get(user=authenticated_user, primary=True)
                if not email_address.verified:
                    # Audit log: Login blocked - email not verified
                    log_auth_event(
                        request=request,
                        event_type='login_failed',
                        user=authenticated_user,
                        success=False,
                        message=f'Login blocked - email not verified: {authenticated_user.username}',
                        metadata={'reason': 'email_not_verified'}
                    )
                    # Return error with email so frontend can display it
                    return Response({
                        'detail': 'Please verify your email address before logging in. Check your inbox for the verification link.',
                        'email': authenticated_user.email,
                        'requires_verification': True
                    }, status=status.HTTP_403_FORBIDDEN)
            except EmailAddress.DoesNotExist:
                # No EmailAddress entry - treat as unverified
                log_auth_event(
                    request=request,
                    event_type='login_failed',
                    user=authenticated_user,
                    success=False,
                    message=f'Login blocked - no email address: {authenticated_user.username}',
                    metadata={'reason': 'no_email_address'}
                )
                raise exceptions.PermissionDenied(
                    'Please verify your email address before logging in.'
                )

            login(request, authenticated_user)

            # Handle "Remember Me" functionality
            remember_me = request.data.get('remember_me', False)
            if remember_me:
                # Keep session for 30 days (2,592,000 seconds)
                request.session.set_expiry(2592000)
            else:
                # Session expires when browser closes (default behavior)
                request.session.set_expiry(0)

            # Audit log: Successful login
            log_auth_event(
                request=request,
                event_type='login_success',
                user=authenticated_user,
                success=True,
                message=f'User logged in successfully: {authenticated_user.username}',
                metadata={'auth_method': 'password', 'remember_me': remember_me}
            )

            # Determine redirect URL
            redirect_url = '/'
            if next_url and not next_url.startswith('/login'):
                redirect_url = next_url

            return Response({
                'detail': 'Login successful! Redirecting...',
                'redirect_url': redirect_url
            }, status=status.HTTP_200_OK)

        # Authentication failed - check if this failure triggered a lockout
        # The lockout occurs AFTER the failed attempt is recorded:
        if AxesProxyHandler.is_locked(request):
            # Audit log: Account just got locked
            log_auth_event(
                request=request,
                event_type='login_locked',
                username=user_obj.username,
                success=False,
                message=f'Account locked after failed login attempt: {user_obj.username}',
                metadata={'reason': 'exceeded_failure_limit'}
            )
            raise exceptions.PermissionDenied(
                'Account locked due to too many login attempts. Please try again later.'
            )

        # Audit log: Failed login - invalid password
        log_auth_event(
            request=request,
            event_type='login_failed',
            username=user_obj.username,
            success=False,
            message=f'Login failed - invalid password: {user_obj.username}',
            metadata={'reason': 'invalid_password'}
        )

        # Invalid password - use same generic error (prevents user enumeration)
        # Use 400 instead of 401 to prevent browser's HTTP auth dialog
        raise exceptions.ValidationError(generic_error)


# ----------------------------------------------------------------------------- #
# Handle user logout via API endpoint.                                          #
#                                                                               #
# Ends the user's session and returns JSON response.                            #
#                                                                               #
# Args:     Request: HTTP request object                                        #
# Returns:  DRF Response with success message                                   #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def custom_logout(request):
    # Get user before logout (session cleared after logout())
    user = request.user

    # Audit log: User logout
    log_auth_event(
        request=request,
        event_type='logout',
        user=user,
        success=True,
        message=f'User logged out: {user.username}',
        metadata={}
    )

    logout(request)
    return Response({
        'detail': 'Logout successful.',
        'redirect_url': '/'
    }, status=status.HTTP_200_OK)



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    PASSWORD RESET FORMS                                               #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Ensures all password operations (registration, password change, and password  #
# reset) use the same validation logic from PasswordService, maintaining a      #
# single source of truth for password validation across the application.        #
#                                                                               #
# Integration:                                                                  #
# Used by CustomPasswordResetConfirmView in the password reset flow when users  #
# set a new password via email link. Overrides Django's default SetPasswordForm #
# to delegate validation and password setting to PasswordService.               #
# ----------------------------------------------------------------------------- #
class PasswordServiceSetPasswordForm(SetPasswordForm):

    # ----------------------------------------------------------------------------- #
    # This method is called during form validation (Django's clean process) and     #
    # uses PasswordService to ensure consistent validation with registration and    #
    # password change operations.                                                   #
    # ----------------------------------------------------------------------------- #
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        # Validate that passwords match using PasswordService
        match_valid, match_error = PasswordService.validate_passwords_match(
            password1, password2
        )
        if not match_valid:
            raise ValidationError(match_error)

        # Validate password strength using PasswordService (context-aware)
        strength_valid, strength_error = PasswordService.validate_password_strength(
            password1, user=self.user
        )
        if not strength_valid:
            raise ValidationError(strength_error)

        return password2


    # ----------------------------------------------------------------------------- #
    # This ensures password hashing and storage is handled consistently via         #
    # PasswordService rather than directly calling Django's set_password method.    #
    # ----------------------------------------------------------------------------- #
    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]

        # Use PasswordService to set the password
        # Note: This already saves the user internally, no need to save again
        success, error = PasswordService.set_password(self.user, password)

        if not success:
            raise ValidationError(error)

        # User was already saved by PasswordService.set_password()
        return self.user



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    PASSWORD RESET VIEWS                                               #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Display password reset request form (users enter their email).                #
#                                                                               #
# Throttled to prevent email bombing attacks (3 requests per hour).             #
# ----------------------------------------------------------------------------- #
class CustomPasswordResetView(PasswordResetView):
    template_name = 'stars_app/auth/password_reset/auth_password_reset.html'
    email_template_name = 'stars_app/auth/password_reset/auth_password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    throttle_classes = [LoginRateThrottle]

    def form_valid(self, form):
        # Get email from form
        email = form.cleaned_data['email']

        # Audit log: Password reset requested
        log_auth_event(
            request=self.request,
            event_type='password_reset_requested',
            username='',  # Don't know username yet
            success=True,
            message=f'Password reset requested for email: {email}',
            metadata={'email': email}
        )

        return super().form_valid(form)


# Display confirmation that password reset email was sent:
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'stars_app/auth/password_reset/auth_password_reset_done.html'


# Display form for entering new password (via link in password reset email):
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'stars_app/auth/password_reset/auth_password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    form_class = PasswordServiceSetPasswordForm

    def form_valid(self, form):
        # Get user whose password is being changed
        user = form.user

        # Audit log: Password changed via reset link
        log_auth_event(
            request=self.request,
            event_type='password_changed',
            user=user,
            success=True,
            message=f'Password changed via reset link: {user.username}',
            metadata={'method': 'password_reset_link'}
        )

        return super().form_valid(form)


# Display confirmation that password was successfully reset:
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'stars_app/auth/password_reset/auth_password_reset_complete.html'



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    EMAIL VERIFICATION                                                 #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Resend email verification link to user.                                       #
#                                                                               #
# DRF API endpoint that sends a new verification email to unverified users.     #
# Rate-limited to prevent email spam (max 1 per minute per email).              #
#                                                                               #
# Args:     request: HTTP request object with email in request body             #
# Returns:  DRF Response with success/error message                             #
# ----------------------------------------------------------------------------- #
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def resend_verification_email(request):
    email = request.data.get('email', '').strip().lower()

    # Validate email provided
    if not email:
        raise exceptions.ValidationError('Email address is required.')

    # Validate email format
    try:
        validate_email(email)
    except ValidationError:
        raise exceptions.ValidationError('Please enter a valid email address.')

    # Check if user with this email exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists or not (prevent user enumeration)
        # Return success message regardless
        return Response({
            'detail': 'If an account with that email exists and is unverified, a verification email has been sent.'
        }, status=status.HTTP_200_OK)

    # Check if email is already verified
    from allauth.account.models import EmailAddress, EmailConfirmation
    try:
        email_address = EmailAddress.objects.get(user=user, email=email)
        if email_address.verified:
            # Email already verified
            raise exceptions.ValidationError('This email address is already verified. You can log in now.')
    except EmailAddress.DoesNotExist:
        # No EmailAddress entry - shouldn't happen, but handle gracefully
        raise exceptions.ValidationError('No account found with this email address.')

    # Send new verification email
    try:
        # Delete all existing confirmations for this email address
        # This ensures only the latest verification link works
        old_confirmations = EmailConfirmation.objects.filter(email_address=email_address)
        deleted_count = old_confirmations.count()
        old_confirmations.delete()

        # Create new confirmation and send email
        confirmation = EmailConfirmation.create(email_address)
        confirmation.send(request)

        # Audit log: Verification email resent
        log_auth_event(
            request=request,
            event_type='verification_email_resent',
            user=user,
            success=True,
            message=f'Verification email resent to: {email}',
            metadata={'email': email, 'old_confirmations_deleted': deleted_count}
        )

        return Response({
            'detail': 'Verification email sent! Please check your inbox.',
            'email_sent': True
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Audit log: Failed to send verification email
        log_auth_event(
            request=request,
            event_type='verification_email_failed',
            user=user,
            success=False,
            message=f'Failed to send verification email to: {email}',
            metadata={'email': email, 'error': str(e)}
        )
        raise exceptions.APIException('Failed to send verification email. Please try again later.')


# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    AUTHENTICATION STATUS                                              #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Check if user is authenticated and return user information.                   #
#                                                                               #
# DRF API endpoint that returns authentication status and basic user info.      #
# Useful for frontend components (like navbar) to conditionally render UI       #
# based on authentication state without making unnecessary authenticated        #
# requests to other endpoints.                                                  #
#                                                                               #
# Args:     request: HTTP request object                                        #
# Returns:  DRF Response with authentication status and user data               #
# ----------------------------------------------------------------------------- #
@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status(request):
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'profile_picture_url': request.user.userprofile.get_profile_picture_url
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'authenticated': False,
            'user': None
        }, status=status.HTTP_200_OK)
