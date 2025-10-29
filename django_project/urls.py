"""
URL configuration for django_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve as static_serve

from django.conf import settings
from django.conf.urls.static import static

import os

from .views import ReactAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('starview_app.urls')),
]

# Django Debug Toolbar (development only)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Static and media files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve React build assets (always, even in production)
urlpatterns += [
    re_path(
        r'^assets/(?P<path>.*)$',
        static_serve,
        {'document_root': os.path.join(settings.BASE_DIR, 'starview_frontend/dist/assets')},
    ),
    re_path(
        r'^images/(?P<path>.*)$',
        static_serve,
        {'document_root': os.path.join(settings.BASE_DIR, 'starview_frontend/dist/images')},
    ),
]

# Catch-all: serve React app for any non-API/admin routes
# IMPORTANT: This must be the LAST pattern in urlpatterns
# It matches any URL that wasn't caught by previous patterns
urlpatterns += [
    re_path(r'^.*$', ReactAppView.as_view(), name='react_app'),
]
