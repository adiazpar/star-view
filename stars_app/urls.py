# ----------------------------------------------------------------------------------------------------- #
# This urls.py file defines all URL routing for the stars_app application:                              #
#                                                                                                       #
# Purpose:                                                                                              #
# Maps incoming HTTP requests to the appropriate view functions or ViewSets. This is the central        #
# configuration that connects URLs to business logic, enabling users to interact with the application   #
# through both traditional template views and REST API endpoints.                                       #
#                                                                                                       #
# Key Features:                                                                                         #
# - REST API routers: Automatic URL generation for CRUD operations on locations, reviews, favorites     #
# - Nested resources: Hierarchical API structure (locations → reviews → comments)                       #
# - Authentication routes: Registration, login, logout, password reset flows                            #
# - Template views: Traditional Django views for navigation and location detail pages                   #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework's DefaultRouter for flat resources (locations, favorites)                #
# - Uses NestedDefaultRouter for hierarchical resources (reviews under locations, comments under        #
#   reviews), creating intuitive API paths like /api/locations/{id}/reviews/{id}/comments/              #
# - Static/media file serving is handled at the project level (django_project/urls.py)                  #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

# Import views:
from .views import (
    # ViewSets
    LocationViewSet,
    FavoriteLocationViewSet,
    ReviewViewSet,
    CommentViewSet,
    UserProfileViewSet,
    # Template views
    home,
    map,
    account,
    location_details,
    # Authentication views
    register,
    custom_login,
    custom_logout,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
    # Health check views
    health_check,
)

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='locations')
router.register(r'favorite-locations', FavoriteLocationViewSet, basename='favorite-locations')
router.register(r'profile', UserProfileViewSet, basename='profile')

# Nested router for reviews
locations_router = routers.NestedDefaultRouter(router, r'locations', lookup='location')
locations_router.register(r'reviews', ReviewViewSet, basename='location-reviews')

# Nested router for comments
reviews_router = routers.NestedDefaultRouter(locations_router, r'reviews', lookup='review')
reviews_router.register(r'comments', CommentViewSet, basename='review-comments')


urlpatterns = [
    # Health check (for load balancer monitoring):
    path('health/', health_check, name='health_check'),

    # User authentication:
    path('register/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),

    # Password Reset Views:
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Navigation:
    path('', home, name='home'),
    path('map/', map, name='map'),
    path('account/', account, name='account'),

    # Location:
    path('location/<int:location_id>/', location_details, name='location_details'),

    # Django Rest Framework:
    path('api/', include(router.urls)),
    path('api/', include(locations_router.urls)),
    path('api/', include(reviews_router.urls)),
]