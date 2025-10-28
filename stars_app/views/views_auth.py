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
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
from django.urls import reverse_lazy, reverse
from django.db.models import Q

# DRF imports:
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework import status, exceptions
from rest_framework.response import Response

# django-axes imports for account lockout:
from axes.exceptions import AxesBackendPermissionDenied
from axes.handlers.proxy import AxesProxyHandler

# Service imports:
from stars_app.services import PasswordService
from stars_app.utils import LoginRateThrottle, log_auth_event



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
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def register(request):
    if request.method == 'POST':
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

        # Create user after all validation passes
        user = User.objects.create_user(
            **user_data,
            password=pass1
        )

        # Auto-login the newly registered user
        # Set backend attribute (required when multiple auth backends are configured)
        from django.contrib.auth import get_backends
        backend = get_backends()[0]  # Use first backend (ModelBackend)
        user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
        login(request, user)

        # Audit log: Successful registration
        log_auth_event(
            request=request,
            event_type='registration_success',
            user=user,
            success=True,
            message=f'New user registered: {user.username}',
            metadata={'email': user.email}
        )

        # Registration successful
        return Response({
            'detail': 'Account created successfully! Redirecting...',
            'redirect_url': reverse('home')
        }, status=status.HTTP_201_CREATED)

    # GET request: render registration form
    return render(request, 'stars_app/auth/auth_register.html')


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
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def custom_login(request):
    if request.method == 'POST':
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
                'Account temporarily locked due to too many failed login attempts. Please try again in 1 hour.'
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
            raise exceptions.AuthenticationFailed(generic_error)

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
                'Account temporarily locked due to too many failed login attempts. Please try again in 1 hour.'
            )

        if authenticated_user is not None:
            login(request, authenticated_user)

            # Audit log: Successful login
            log_auth_event(
                request=request,
                event_type='login_success',
                user=authenticated_user,
                success=True,
                message=f'User logged in successfully: {authenticated_user.username}',
                metadata={'auth_method': 'password'}
            )

            # Determine redirect URL
            redirect_url = reverse('home')
            if next_url and not next_url.startswith('/login/'):
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
                'Account temporarily locked due to too many failed login attempts. Please try again in 1 hour.'
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
        raise exceptions.AuthenticationFailed(generic_error)

    # GET request: render login page
    next_url = request.GET.get('next', '')
    if next_url.startswith('/login/'):
        next_url = ''

    return render(request, 'stars_app/auth/auth_login.html', {'next': next_url})


# ----------------------------------------------------------------------------- #
# Handle user logout.                                                           #
#                                                                               #
# Ends the user's session and redirects to home page with confirmation message. #
#                                                                               #
# Args:     Request: HTTP request object                                        #
# Returns:  Redirect to home page                                               #
# ----------------------------------------------------------------------------- #
@login_required(login_url='login')
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
    return redirect('home')



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
