# ----------------------------------------------------------------------------------------------------- #
# This views_auth.py file handles all authentication-related views:                                     #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides user authentication functionality including registration, login, logout, and password        #
# reset. Handles user creation, session management, and email-based password recovery.                  #
#                                                                                                       #
# Key Features:                                                                                         #
# - User registration: Create new accounts with email validation and duplicate checking                 #
# - Login: Authenticate users with username or email                                                    #
# - Logout: End user sessions with confirmation messages                                                #
# - Password reset: Email-based password recovery workflow with custom templates                        #
# - Input validation: Email format validation, password confirmation, duplicate prevention              #
#                                                                                                       #
# Architecture:                                                                                         #
# - Function-based views for registration, login, and logout                                            #
# - Class-based views for Django's built-in password reset workflow                                     #
# - Integrates with Django's authentication system                                                      #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.db.models import Q



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    REGISTRATION & LOGIN                                               #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# Handle user registration with validation.                                     #
#                                                                               #
# Validates username uniqueness, email format and uniqueness, and password      #
# confirmation. Creates a new user account and redirects to login on success.   #
#                                                                               #
# Args:     Request: HTTP request object                                        #
# Returns:  Rendered registration page or redirect to login on success          #
# ----------------------------------------------------------------------------- #
def register(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            pass1 = request.POST.get('password1')
            pass2 = request.POST.get('password2')

            # Check if the username already exists
            if User.objects.filter(username=username.lower()).exists():
                messages.error(request, 'Username already exists.')
                return redirect('register')

            # Check if the email already exists
            if User.objects.filter(email=email.lower()).exists():
                messages.error(request, 'Email is already registered.')
                return redirect('register')

            # Validate email format using Django's built-in validator
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return redirect('register')

            # Check if the password confirmation doesn't match
            if pass1 != pass2:
                messages.error(request, 'Passwords do not match.')
                return redirect('register')

            # Create user after verifying everything is correct
            User.objects.create_user(
                username=username.lower(),
                email=email.lower(),
                password=pass1,
                first_name=first_name,
                last_name=last_name
            )

            messages.success(request, 'Account created successfully')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register')

    return render(request, 'stars_app/register.html')


# ----------------------------------------------------------------------------- #
# Handle user login with username or email.                                     #
#                                                                               #
# Authenticates users using either their username or email address.             #
# Redirects to the next URL if specified, otherwise to home page.               #
#                                                                               #
# Args:     Request: HTTP request object                                        #
# Returns:  Rendered login page or redirect on success                          #
# ----------------------------------------------------------------------------- #
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

            if not user:
                messages.error(request, 'No account found with that username or email.')
                return redirect('login')

            # Authenticate with username
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Logged in successfully as {user.username}')

                # Redirect to next URL if valid, otherwise home
                if next_url and next_url.strip() and not next_url.startswith('/login/'):
                    return redirect(next_url)

                return redirect('home')

            messages.error(request, 'Invalid password.')
            return redirect('login')

        except Exception as e:
            messages.error(request, 'An error occurred while trying to log in. Please try again.')
            return redirect('login')

    # Handle GET request: render login page
    next_url = request.GET.get('next', '')
    if next_url.startswith('/login/'):
        next_url = ''

    return render(request, 'stars_app/login.html', {'next': next_url})


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
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                    PASSWORD RESET VIEWS                                               #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# Display password reset request form (users enter their email):
class CustomPasswordResetView(PasswordResetView):
    template_name = 'stars_app/password_reset.html'
    email_template_name = 'stars_app/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


# Display confirmation that password reset email was sent:
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'stars_app/password_reset_done.html'


# Display form for entering new password (via link in password reset email):
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'stars_app/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


# Display confirmation that password was successfully reset:
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'stars_app/password_reset_complete.html'
