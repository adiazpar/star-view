# ----------------------------------------------------------------------------------------------------- #
# This views.py file contains project-level views for serving the React frontend:                       #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides infrastructure-level views that enable the React + Django architecture. These views are not  #
# specific to the stars_app business logic, but rather handle the integration layer between the React   #
# frontend and Django backend. This file lives at the project level because it serves the entire        #
# application, not just one app.                                                                        #
#                                                                                                       #
# Why This Exists:                                                                                      #
# React Router handles client-side routing, but when users refresh the page or directly navigate to a   #
# React route (e.g., /map or /location/123), the browser sends that request to Django. Without this     #
# catch-all view, Django would return a 404. This view serves the React index.html for all non-API      #
# routes, allowing React Router to take over and render the correct component.                          #
#                                                                                                       #
# Architecture:                                                                                         #
# - Development: Vite dev server runs on :5173 with hot reload, this view rarely used                   #
# - Production: Django serves React build from starview_frontend/dist/, this view handles all routes  #
# - URLs: Configured as catch-all pattern in django_project/urls.py (must be last in urlpatterns)       #
# - Templates: Looks for index.html in starview_frontend/dist/ (configured in settings.TEMPLATES)       #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.views.generic import TemplateView
from django.conf import settings
import os


# ----------------------------------------------------------------------------- #
# Catch-all view that serves React's index.html for client-side routing.        #
#                                                                               #
# This enables React Router to handle navigation by serving the same HTML       #
# file for all non-API routes. React then renders the appropriate component     #
# based on the URL path.                                                        #
#                                                                               #
# Development workflow:                                                         #
# - Run `npm run dev` in starview_frontend/ directory                           #
# - Access React at http://localhost:5173 (hot reload enabled)                  #
# - API calls proxy to Django at :8000 via Vite config                          #
#                                                                               #
# Production workflow:                                                          #
# - Run `npm run build` to create optimized bundle in starview_frontend/dist/   #
# - Django serves everything from :8000                                         #
# - This view returns index.html for all non-API routes                         #
# ----------------------------------------------------------------------------- #
class ReactAppView(TemplateView):

    def get_template_names(self):
        # Production: always serve the built React app
        if not settings.DEBUG:
            return ['index.html']

        # Development: check if build exists (e.g., testing production mode locally)
        build_path = os.path.join(settings.BASE_DIR, 'starview_frontend', 'dist', 'index.html')
        if os.path.exists(build_path):
            return ['index.html']

        # Development fallback: React build doesn't exist
        # User should run `npm run dev` instead of accessing via Django
        return ['dev_placeholder.html']
