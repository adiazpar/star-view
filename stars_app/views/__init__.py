# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the views directory as a Python package and exposes all views:            #
#                                                                                                       #
# Purpose:                                                                                              #
# This file imports all view classes and functions and makes them available at the package level.       #
# This allows cleaner imports throughout the application (e.g., `from stars_app.views import            #
# LocationViewSet` instead of `from stars_app.views.views_location import LocationViewSet`).            #
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
    location_details,
)

# Review views:
from .views_review import (
    ReviewViewSet,
    CommentViewSet,
)

# User profile views:
from .views_user import (
    account,
    upload_profile_picture,
    remove_profile_picture,
    update_name,
    change_email,
    change_password,
)

# Favorite location views:
from .views_favorite import (
    FavoriteLocationViewSet,
)

# Navigation views:
from .views_navigation import (
    home,
    map,
)

# Authentication views:
from .views_auth import (
    register,
    custom_login,
    custom_logout,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)

# Expose all views for easier imports:
__all__ = [
    # Location views
    'LocationViewSet',
    'location_details',

    # Review views
    'ReviewViewSet',
    'CommentViewSet',

    # User profile views
    'account',
    'upload_profile_picture',
    'remove_profile_picture',
    'update_name',
    'change_email',
    'change_password',

    # Favorite location views
    'FavoriteLocationViewSet',

    # Navigation views
    'home',
    'map',

    # Authentication views
    'register',
    'custom_login',
    'custom_logout',
    'CustomPasswordResetView',
    'CustomPasswordResetDoneView',
    'CustomPasswordResetConfirmView',
    'CustomPasswordResetCompleteView',
]
