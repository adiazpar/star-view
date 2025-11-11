# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the views directory as a Python package and exposes all views:            #
#                                                                                                       #
# Purpose:                                                                                              #
# This file imports all view classes and functions and makes them available at the package level.       #
# This allows cleaner imports throughout the application (e.g., `from starview_app.views import            #
# LocationViewSet` instead of `from starview_app.views.views_location import LocationViewSet`).            #
#                                                                                                       #
# View Organization:                                                                                    #
# Views are separated into individual files by domain for better organization and maintainability:      #
#                                                                                                       #
# Django Integration:                                                                                   #
# Django automatically discovers views imported here and makes them available for URL routing.          #
# All views imported here can be referenced in urls.py configuration.                                   #
# ----------------------------------------------------------------------------------------------------- #

# Location views:
from .views_location import (
    LocationViewSet,
)

# Review views:
from .views_review import (
    ReviewViewSet,
    CommentViewSet,
)

# User profile views:
from .views_user import (
    UserProfileViewSet,
)

# Favorite location views:
from .views_favorite import (
    FavoriteLocationViewSet,
)

# Follow views:
from .views_follow import (
    toggle_follow,
    check_following,
    get_followers,
    get_following,
)

# Authentication views:
from .views_auth import (
    register,
    custom_login,
    custom_logout,
    auth_status,
    resend_verification_email,
    request_password_reset,
    confirm_password_reset,
)

# Health check views:
from .views_health import (
    health_check,
)

# Expose all views for easier imports:
__all__ = [
    # Location views
    'LocationViewSet',

    # Review views
    'ReviewViewSet',
    'CommentViewSet',

    # User profile views
    'UserProfileViewSet',

    # Favorite location views
    'FavoriteLocationViewSet',

    # Follow views
    'toggle_follow',
    'check_following',
    'get_followers',
    'get_following',

    # Authentication views
    'register',
    'custom_login',
    'custom_logout',
    'auth_status',
    'resend_verification_email',
    'request_password_reset',
    'confirm_password_reset',

    # Health check views
    'health_check',
]
