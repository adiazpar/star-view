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
from django.db.models import Avg, Count

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


    # Filter to only show current user's favorites with optimized queries:
    def get_queryset(self):
        from django.db.models import Exists, OuterRef

        queryset = FavoriteLocation.objects.filter(
            user=self.request.user
        ).select_related(
            'location__added_by',
            'location__verified_by',
            'user'
        ).prefetch_related(
            'location__reviews__user',
            'location__reviews__photos',
            'location__reviews__votes',  # Prefetch votes for reviews
            'location__reviews__comments__user',
            'location__reviews__comments__votes'  # Prefetch votes for comments
        )

        # Add annotations to the nested location objects
        # This is done through a subquery to annotate the location
        queryset = queryset.annotate(
            location_review_count=Count('location__reviews'),
            location_average_rating=Avg('location__reviews__rating')
        )

        return queryset.order_by('-created_at')


    # Automatically set user field when creating favorites:
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
