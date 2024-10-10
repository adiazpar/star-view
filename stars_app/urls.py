from django.urls import path, include
from django.contrib import admin

from . import views

urlpatterns = [
    # User authentication:
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # Navigation:
    path('', views.home, name='home'),
    path('map/', views.map, name='map')
]