from django.urls import path, include
from rest_framework.routers import DefaultRouter

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

    # Map Tiles:
    path('upload/', views.upload_and_process_tif, name='upload_and_process_tif'),
    path('tiles/<int:z>/<int:x>/<int:y>.png', views.serve_tile, name='serve_tile'),

    # Django Rest Framework:
    path('api/', include(router.urls)),

    # Update Forecasts
    path('update/', views.update_forecast, name='update_forecast'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)