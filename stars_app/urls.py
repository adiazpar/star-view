from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter

from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import ChangePasswordView

router = DefaultRouter()
router.register(r'viewing-locations', views.ViewingLocationViewSet, basename='viewing-locations')
router.register(r'celestial-events', views.CelestialEventViewSet, basename='celestial-events')

urlpatterns = [
    # User authentication:
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

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

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)