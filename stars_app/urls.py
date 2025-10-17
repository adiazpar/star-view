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
router.register(r'locations', views.LocationViewSet, basename='locations')
router.register(r'user-profiles', views.UserProfileViewSet, basename='user-profiles')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'favorite-locations', views.FavoriteLocationViewSet, basename='favorite-locations')
router.register(r'votes', views.VoteViewSet, basename='votes')

# Nested router for reviews
locations_router = routers.NestedDefaultRouter(router, r'locations', lookup='location')
locations_router.register(r'reviews', views.ReviewViewSet, basename='location-reviews')

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
    path('account/<int:pk>', views.account, name='account'),

    # Viewing location:
    path('location/<int:location_id>/', views.location_details, name='location_details'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),

    # Django Rest Framework:
    path('api/', include(router.urls)),
    path('api/', include(locations_router.urls)),
    path('api/', include(reviews_router.urls)),

    # Other:
    path('api/locations/', views.LocationCreateView.as_view(), name='location-create'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)