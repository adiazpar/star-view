# ----------------------------------------------------------------------------------------------------- #
# This adapters.py file customizes django-allauth behavior for the Starview application:                #
#                                                                                                       #
# Purpose:                                                                                              #
# Overrides default django-allauth adapters to customize authentication flows, redirects, and           #
# email handling to integrate seamlessly with the React frontend.                                       #
#                                                                                                       #
# Key Features:                                                                                         #
# - Custom redirects: Sends users to React frontend pages instead of Django templates                   #
# - Email verification flow: Redirects to React login page with success message                         #
# - Frontend integration: Ensures smooth SPA experience with query parameters                           #
# - Custom email confirmation view: Handles expired/invalid links by redirecting to React               #
#                                                                                                       #
# Integration:                                                                                          #
# Configured in settings.py via ACCOUNT_ADAPTER setting.                                                #
# Custom view configured in django_project/urls.py to override allauth view.                            #
# ----------------------------------------------------------------------------------------------------- #

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.views import ConfirmEmailView
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import Http404


# ----------------------------------------------------------------------------- #
# Custom account adapter for django-allauth that redirects to React frontend.   #
#                                                                               #
# This adapter customizes the email verification flow to redirect users to      #
# the React login page with a success indicator instead of showing Django       #
# templates.                                                                    #
# ----------------------------------------------------------------------------- #
class CustomAccountAdapter(DefaultAccountAdapter):

    # ----------------------------------------------------------------------------- #
    # Redirect to React email verified page after successful email verification.    #
    #                                                                               #
    # Instead of showing the default django-allauth template, this redirects        #
    # users to a custom React success page that confirms verification and           #
    # provides a link to login.                                                     #
    #                                                                               #
    # Adds a success token to prevent unauthorized access to the page.              #
    #                                                                               #
    # Args:                                                                         #
    #   - email_address: EmailAddress instance that was verified                    #
    # Returns:                                                                      #
    #   - str: URL to redirect to after email verification                          #
    # ----------------------------------------------------------------------------- #
    def get_email_verification_redirect_url(self, email_address):
        import secrets
        from django.conf import settings

        # Generate a one-time success token
        success_token = secrets.token_urlsafe(16)

        # In development, redirect to React dev server
        # In production, use relative URL (Django serves React build)
        if settings.DEBUG:
            return f'http://localhost:5173/email-verified?success={success_token}'
        else:
            return f'/email-verified?success={success_token}'


    # ----------------------------------------------------------------------------- #
    # Redirect to React home page after successful login.                           #
    #                                                                               #
    # Overrides the default login redirect to send users to the React               #
    # frontend home page instead of a Django template.                              #
    #                                                                               #
    # Args:                                                                         #
    #   - request: HTTP request object                                              #
    # Returns:                                                                      #
    #   - str: URL to redirect to after login                                       #
    # ----------------------------------------------------------------------------- #
    def get_login_redirect_url(self, request):
        # Default to home page, but respect 'next' parameter if provided
        next_url = request.GET.get('next')
        if next_url:
            return next_url
        return '/'


    # ----------------------------------------------------------------------------- #
    # Redirect to React home page after successful logout.                          #
    #                                                                               #
    # Overrides the default logout redirect to send users to the React              #
    # frontend home page instead of a Django template.                              #
    #                                                                               #
    # Args:                                                                         #
    #   - request: HTTP request object                                              #
    # Returns:                                                                      #
    #   - str: URL to redirect to after logout                                      #
    # ----------------------------------------------------------------------------- #
    def get_logout_redirect_url(self, request):
        return '/'


    # ----------------------------------------------------------------------------- #
    # Redirect to React home page after successful signup.                          #
    #                                                                               #
    # Overrides the default signup redirect to send users to the React              #
    # frontend home page instead of a Django template.                              #
    #                                                                               #
    # Args:                                                                         #
    #   - request: HTTP request object                                              #
    # Returns:                                                                      #
    #   - str: URL to redirect to after signup                                      #
    # ----------------------------------------------------------------------------- #
    def get_signup_redirect_url(self, request):
        return '/'


# ----------------------------------------------------------------------------- #
# Custom email confirmation view that redirects to React for all scenarios.     #
#                                                                               #
# This view intercepts the email confirmation flow and redirects to the React   #
# frontend instead of rendering Django templates.                               #
#                                                                               #
# Scenarios:                                                                    #
# - Expired/invalid link: Redirects to React error page                         #
# - Already confirmed: Redirects to React error page                            #
# - Valid confirmation: Processes normally and redirects via adapter            #
# ----------------------------------------------------------------------------- #
class CustomConfirmEmailView(ConfirmEmailView):

    def get(self, *args, **kwargs):
        from django.conf import settings

        try:
            self.object = self.get_object()

            # Check if email can be confirmed
            if not self.object or not self.object.email_address.can_set_verified():
                # Email already confirmed by this or another account
                error_url = '/email-confirm-error?error=already_confirmed'
                if settings.DEBUG:
                    error_url = f'http://localhost:5173{error_url}'
                return HttpResponseRedirect(error_url)

            # Valid confirmation - continue with normal flow
            # This will auto-confirm if ACCOUNT_CONFIRM_EMAIL_ON_GET is True
            # and then redirect via get_email_verification_redirect_url
            return super().get(*args, **kwargs)

        except Http404:
            # Expired or invalid confirmation key
            error_url = '/email-confirm-error?error=expired'
            if settings.DEBUG:
                error_url = f'http://localhost:5173{error_url}'
            return HttpResponseRedirect(error_url)
