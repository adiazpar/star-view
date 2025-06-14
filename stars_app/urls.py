from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from django.conf import settings
from django.conf.urls.static import static
from . import views

from .views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)

router = DefaultRouter()
router.register(r'viewing-locations', views.ViewingLocationViewSet, basename='viewing-locations')
router.register(r'celestial-events', views.CelestialEventViewSet, basename='celestial-events')
router.register(r'user-profiles', views.UserProfileViewSet, basename='user-profiles')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'favorite-locations', views.FavoriteLocationViewSet, basename='favorite-locations')
router.register(r'review-votes', views.ReviewVoteViewSet, basename='review-votes')
router.register(r'forecasts', views.ForecastViewSet, basename='forecasts')
# defaultforecast is a function, not a model, so no endpoint needed

# Nested router for reviews
locations_router = routers.NestedDefaultRouter(router, r'viewing-locations', lookup='location')
locations_router.register(r'reviews', views.LocationReviewViewSet, basename='location-reviews')

# Nested router for comments
reviews_router = routers.NestedDefaultRouter(locations_router, r'reviews', lookup='review')
reviews_router.register(r'comments', views.ReviewCommentViewSet, basename='review-comments')


urlpatterns = [
    # User authentication:
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('upload-profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('remove-profile-picture/', views.remove_profile_picture, name='remove_profile_picture'),
    path('update-name/', views.update_name, name='update_name'),
    path('change-email/', views.change_email, name='change_email'),
    path('change-password/', views.change_password, name='change_password'),

    # Password Change Views:
    path('password-reset/',
         CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         CustomPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         CustomPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    # Navigation:
    path('', views.home, name='home'),
    path('map/', views.map, name='map'),
    path('list/', views.event_list, name='event_list'),
    path('list/<event_id>', views.details, name='details'),
    path('account/<int:pk>', views.account, name='account'),

    # Viewing location:
    path('location/<int:location_id>/', views.location_details, name='location_details'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),

    # Django Rest Framework:
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(locations_router.urls)),
    path('api/v1/', include(reviews_router.urls)),

    # Other:
    path('api/viewing-locations/', views.ViewingLocationCreateView.as_view(), name='viewing-location-create'),

    # Update Forecasts
    path('update/', views.update_forecast, name='update_forecast'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)