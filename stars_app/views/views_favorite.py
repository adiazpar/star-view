# ----------------------------------------------------------------------------------------------------- #
# This views_favorite.py file handles user's favorite locations API endpoints.                          #
#                                                                                                       #
# Purpose:                                                                                              #
# Manages user's collection of favorite stargazing locations with optional per-user nicknames.          #
# Each user can favorite locations and assign personal nicknames without affecting other users.         #
#                                                                                                       #
# Key Features:                                                                                         #
# - CRUD operations for favorites (list, create, retrieve, update, delete)                              #
# - Automatic per-user filtering (users only see their own favorites)                                   #
# - Optional nicknames for personal organization (stored in FavoriteLocation junction table)            #
# - Sorted by creation date (newest first)                                                              #
# - Nickname updates via standard PATCH/PUT operations on this ViewSet                                  #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Import models:
from ..models import FavoriteLocation

# Import serializers:
from ..serializers import FavoriteLocationSerializer



# ----------------------------------------------------------------------------- #
# API ViewSet for managing user's favorite locations.                           #
#                                                                               #
# Provides standard CRUD endpoints with automatic user isolation. Favorites     #
# are returned sorted by creation date (newest first). Requires authentication. #
# ----------------------------------------------------------------------------- #
class FavoriteLocationViewSet(viewsets.ModelViewSet):
    # Translator between database objects and JSON (handles validation, field inclusion, nested data):
    serializer_class = FavoriteLocationSerializer
    permission_classes = [IsAuthenticated]


    # Filter to only show current user's favorites (sorted by newest first):
    def get_queryset(self):
        return FavoriteLocation.objects.filter(user=self.request.user).order_by('-created_at')


    # Automatically set user field when creating favorites:
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
