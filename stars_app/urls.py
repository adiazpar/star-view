from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'locations', views.LocationViewSet, basename='locations')
router.register(r'events', views.EventViewSet, basename='events')

urlpatterns = [
    # User authentication:
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # Navigation:
    path('', views.home, name='home'),
    path('map/', views.map, name='map'),

    # API
    path('api/', include(router.urls)),
]