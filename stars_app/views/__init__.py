# ----------------------------------------------------------------------------------------------------- #
# This __init__.py file marks the views directory as a Python package and exposes all views:           #
#                                                                                                       #
# Purpose:                                                                                              #
# This file imports all view classes and functions and makes them available at the package level.      #
# This allows cleaner imports throughout the application (e.g., `from stars_app.views import           #
# LocationViewSet` instead of `from stars_app.views.views_location import LocationViewSet`).           #
#                                                                                                       #
# View Organization:                                                                                    #
# Views are separated into individual files by domain for better organization and maintainability:     #
# - views_location.py: Location-related ViewSets and views                                             #
# - views_review.py: Review and comment ViewSets and views                                             #
# - views_user.py: User profile ViewSets and account management views                                  #
# - views_favorite.py: Favorite location ViewSets and views                                            #
# - views_vote.py: Vote ViewSet for upvoting/downvoting                                                #
# - views_navigation.py: Home page, map, and navigation views                                          #
# - views_auth.py: Authentication views (login, register, logout, password reset)                      #
#                                                                                                       #
# Django Integration:                                                                                   #
# Django automatically discovers views imported here and makes them available for URL routing.          #
# All views imported here can be referenced in urls.py configuration.                                  #
# ----------------------------------------------------------------------------------------------------- #

# Location views:
from .views_location import (
    LocationViewSet,
    LocationCreateView,
    location_details,
)

# Review views:
from .views_review import (
    ReviewViewSet,
    ReviewCommentViewSet,
    delete_review,
)

# User profile views:
from .views_user import (
    UserProfileViewSet,
    UserViewSet,
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

# Vote views:
from .views_vote import (
    VoteViewSet,
)

# Navigation views:
from .views_navigation import (
    home,
    map,
    get_tile_server_config,
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
    'LocationCreateView',
    'location_details',

    # Review views
    'ReviewViewSet',
    'ReviewCommentViewSet',
    'delete_review',

    # User profile views
    'UserProfileViewSet',
    'UserViewSet',
    'account',
    'upload_profile_picture',
    'remove_profile_picture',
    'update_name',
    'change_email',
    'change_password',

    # Favorite location views
    'FavoriteLocationViewSet',

    # Vote views
    'VoteViewSet',

    # Navigation views
    'home',
    'map',
    'get_tile_server_config',

    # Authentication views
    'register',
    'custom_login',
    'custom_logout',
    'CustomPasswordResetView',
    'CustomPasswordResetDoneView',
    'CustomPasswordResetConfirmView',
    'CustomPasswordResetCompleteView',
]
