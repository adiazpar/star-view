# ----------------------------------------------------------------------------------------------------- #
# This views_location.py file handles all location-related views and API endpoints:                     #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints and template views for managing stargazing locations. Handles location    #
# creation, retrieval, updates, and enrichment with geographic data (elevation, address).               #
#                                                                                                       #
# Key Features:                                                                                         #
# - LocationViewSet: Full CRUD API for locations with filtering, search, and ordering                   #
# - Map optimization: Lightweight endpoints for 3D globe (map_markers + info_panel, 96%+ reduction)     #
# - Report handling: Users can report problematic locations using the generic Report model              #
# - Template view: location_details displays location info with reviews (read-only)                     #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                               #
# - Delegates business logic to service layer (ReportService, VoteService)                              #
# - Errors raised as exceptions, caught by global exception handler (Phase 4)                           #
# - Template views are read-only; all write operations use API endpoints                                #
# - Favorite operations are handled by FavoriteLocationViewSet in views_favorite.py                     #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Avg, Count, Q, Exists, OuterRef

# REST Framework imports:
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

# Model imports:
from ..models import Location
from ..models import Review
from ..models import FavoriteLocation

# Serializer imports:
from ..serializers import LocationSerializer
from ..serializers import MapLocationSerializer
from ..serializers import LocationInfoPanelSerializer

# Service imports:
from ..services import ReportService
from ..services import VoteService

# Throttle imports:
from starview_app.utils import ContentCreationThrottle, ReportThrottle

# Cache imports:
from starview_app.utils import (
    location_list_key,
    location_detail_key,
    map_markers_key,
    invalidate_location_list,
    invalidate_location_detail,
    invalidate_map_markers,
    invalidate_all_location_caches,
)
from django.core.cache import cache



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       LOCATION VIEWSET                                                #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# API ViewSet for managing stargazing locations.                                #
#                                                                               #
# Provides endpoints for creating, retrieving, updating, and deleting           #
# locations. Includes actions for reporting and optimized endpoints for map     #
# display (map_markers, info_panel).                                            #
# ----------------------------------------------------------------------------- #
class LocationViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticatedOrReadOnly]


    # Use different serializers for list vs detail views:
    def get_serializer_class(self):
        # For list view, don't include nested reviews (too much data)
        # Reviews are available via the nested endpoint /api/locations/{id}/reviews/
        if self.action == 'list':
            from ..serializers import LocationListSerializer
            return LocationListSerializer

        # SCALABILITY NOTE:
        # Currently 'retrieve' (detail) view returns LocationSerializer with ALL nested reviews.
        # This works fine for locations with 1-20 reviews, but can be slow with 100+ reviews.
        #
        # For better scalability, change this to:
        #   return LocationListSerializer
        #
        # Then have frontend fetch reviews separately via:
        #   GET /api/locations/{id}/reviews/?page=1 (already paginated, 20 per page)
        return LocationSerializer


    # Optimize queryset with select_related, prefetch_related, and annotations:
    def get_queryset(self):
        queryset = Location.objects.select_related(
            'added_by',
            'verified_by'
        ).annotate(
            review_count_annotated=Count('reviews'),
            average_rating_annotated=Avg('reviews__rating')
        )

        # For detail view, prefetch nested reviews with votes to avoid N+1
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'reviews__user',
                'reviews__photos',
                'reviews__votes',  # Prefetch votes for reviews
                'reviews__comments__user',
                'reviews__comments__votes'  # Prefetch votes for comments
            )
        else:
            # For list view, we don't include nested reviews in serializer
            # so no need to prefetch them
            pass

        # Add is_favorited annotation for authenticated users
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited_annotated=Exists(
                    FavoriteLocation.objects.filter(
                        user=self.request.user,
                        location=OuterRef('pk')
                    )
                )
            )

        return queryset


    # ----------------------------------------------------------------------------- #
    # List all locations with pagination and caching.                               #
    #                                                                               #
    # Cache Strategy:                                                               #
    # - Cache each page separately for 15 minutes (900 seconds)                     #
    # - Authenticated users get different cache (includes is_favorited)             #
    # - Invalidated when: new location created, location deleted                    #
    #                                                                               #
    # Performance Impact:                                                           #
    # - Before caching: 4 queries per request (already optimized with annotations)  #
    # - After caching: 0 queries for cache hits (~90%+ of requests)                 #
    # ----------------------------------------------------------------------------- #
    def list(self, request, *args, **kwargs):
        page = request.GET.get('page', 1)

        # Different cache keys for authenticated vs anonymous users
        # (authenticated includes is_favorited annotation)
        if request.user.is_authenticated:
            cache_key = f'{location_list_key(page)}:user:{request.user.id}'
        else:
            cache_key = location_list_key(page)

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Cache miss - get data from database
        queryset = self.filter_queryset(self.get_queryset())

        # Paginate the queryset
        page_obj = self.paginate_queryset(queryset)
        if page_obj is not None:
            serializer = self.get_serializer(page_obj, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data

        # Cache for 15 minutes
        cache.set(cache_key, response_data, timeout=900)

        return Response(response_data)


    # ----------------------------------------------------------------------------- #
    # Retrieve a single location with caching.                                      #
    #                                                                               #
    # Cache Strategy:                                                               #
    # - Cache each location separately for 15 minutes (900 seconds)                 #
    # - Authenticated users get different cache (includes is_favorited, nested      #
    # reviews with user_vote)                                                       #
    # - Invalidated when: location updated, review added/updated/deleted            #
    #                                                                               #
    # Performance Impact:                                                           #
    # - Before caching: 9 queries per request (with prefetching)                    #
    # - After caching: 0 queries for cache hits (~80%+ of requests)                 #
    # ----------------------------------------------------------------------------- #
    def retrieve(self, request, *args, **kwargs):
        location_id = kwargs.get('pk')

        # Different cache keys for authenticated vs anonymous users
        if request.user.is_authenticated:
            cache_key = f'{location_detail_key(location_id)}:user:{request.user.id}'
        else:
            cache_key = location_detail_key(location_id)

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Cache miss - get data from database
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = serializer.data

        # Cache for 15 minutes
        cache.set(cache_key, response_data, timeout=900)

        return Response(response_data)


    # Apply different throttles based on action:
    def get_throttles(self):
        if self.action == 'create':
            # Limit location creation to prevent spam
            return [ContentCreationThrottle()]
        elif self.action == 'report':
            # Limit reports to prevent report abuse
            return [ReportThrottle()]
        return super().get_throttles()


    # ----------------------------------------------------------------------------- #
    # Create a new location and set the user who added it.                          #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_create() to inject    #
    # the current user as added_by. Without this override, DRF would just call      #
    # serializer.save() with no additional context. We also invalidate caches       #
    # since the location list and map markers now have new data.                    #
    # ----------------------------------------------------------------------------- #
    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

        # Invalidate caches since new location was created
        invalidate_location_list()  # Clear all location list pages
        invalidate_map_markers()  # Clear map markers cache


    # ----------------------------------------------------------------------------- #
    # Update a location and invalidate related caches.                              #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_update() to add       #
    # cache invalidation. Without this override, DRF would just call                #
    # serializer.save() with no cache clearing, causing stale data to be served.    #
    # ----------------------------------------------------------------------------- #
    def perform_update(self, serializer):
        location = self.get_object()
        serializer.save()

        # Invalidate caches since location was updated
        invalidate_all_location_caches(location.id)  # Clear all related caches


    # ----------------------------------------------------------------------------- #
    # Delete a location and invalidate related caches.                              #
    #                                                                               #
    # DRF Note: This overrides ModelViewSet's default perform_destroy() to add      #
    # cache invalidation. Without this override, DRF would just call                #
    # instance.delete() with no cache clearing, causing deleted locations to        #
    # still appear in cached responses.                                             #
    # ----------------------------------------------------------------------------- #
    def perform_destroy(self, instance):
        location_id = instance.id
        instance.delete()

        # Invalidate caches since location was deleted
        invalidate_location_list()  # Clear location list
        invalidate_map_markers()  # Clear map markers
        invalidate_location_detail(location_id)  # Clear this location's detail


    # Submit a report about this location using the ReportService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        location = self.get_object()

        # Use ReportService to handle report submission
        # ReportService raises ValidationError on failure (caught by exception handler)
        report = ReportService.submit_report(
            user=request.user,
            content_object=location,
            report_type=request.data.get('report_type', 'OTHER'),
            description=request.data.get('description', '')
        )

        # Increment report counter on the location
        location.times_reported += 1
        location.save()

        # Return success response
        content_type_name = report.content_type.model.replace('_', ' ').capitalize()
        return Response(
            {'detail': f'{content_type_name} reported successfully'},
            status=status.HTTP_201_CREATED
        )


    # ----------------------------------------------------------------------------- #
    # Get minimal location data optimized for map display.                          #
    #                                                                               #
    # Returns a lightweight JSON array containing only the essential fields         #
    # needed to render markers on the 3D globe interface.                           #
    #                                                                               #
    # Cache Strategy:                                                               #
    # - Cached for 30 minutes (1800 seconds) - map data changes infrequently        #
    # - Same for all users (no user-specific data)                                  #
    # - Invalidated when: location created, location deleted, coordinates change    #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['GET'], serializer_class=MapLocationSerializer)
    def map_markers(self, request):

        # Try to get from cache (same for all users)
        cache_key = map_markers_key()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Cache miss - get data from database
        # Get all locations
        queryset = Location.objects.all()

        # Optimize database query - only fetch needed columns
        queryset = queryset.only('id', 'name', 'latitude', 'longitude')

        # Serialize and return as simple array
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data

        # Cache for 30 minutes (longer than list/detail since map data rarely changes)
        cache.set(cache_key, response_data, timeout=1800)

        return Response(response_data)


    # ----------------------------------------------------------------------------- #
    # Get optimized location data for map info panel display.                       #
    #                                                                               #
    # Returns just enough data to populate the info panel that appears when         #
    # a user clicks a marker on the map. Excludes heavy nested data like full       #
    # review content, photos, comments, and vote data.                              #
    # ----------------------------------------------------------------------------- #
    @action(detail=True, methods=['GET'], serializer_class=LocationInfoPanelSerializer)
    def info_panel(self, request, pk=None):
        
        location = self.get_object()
        serializer = self.get_serializer(location)
        return Response(serializer.data)



# ----------------------------------------------------------------------------- #
# Display detailed information about a location including reviews.              #
#                                                                               #
# Shows all reviews with the user's review first (if exists) and enriches       #
# them with vote information for authenticated users using VoteService.         #
# ----------------------------------------------------------------------------- #
def location_details(request, location_id):

    location = get_object_or_404(Location, pk=location_id)
    all_reviews = Review.objects.filter(location=location)

    # Initialize variables
    user_has_reviewed = False
    is_owner = False

    if request.user.is_authenticated:
        # Check if user owns the location
        is_owner = location.added_by == request.user

        # Check if user has already reviewed
        user_has_reviewed = all_reviews.filter(user=request.user).exists()

        # Get user's review and other reviews
        user_review = all_reviews.filter(user=request.user).first()
        other_reviews = all_reviews.exclude(user=request.user)
    else:
        user_review = None
        other_reviews = all_reviews

    # Order other reviews by created_at
    other_reviews = other_reviews.order_by('-created_at')

    # Combine reviews (user's review first, then others)
    if user_review:
        reviews_list = [user_review] + list(other_reviews)
    else:
        reviews_list = list(other_reviews)

    # Create vote dictionaries to pass to template
    comment_votes = {}

    # Add vote information using VoteService
    for review in reviews_list:
        # Get vote data for this review
        vote_data = VoteService.get_vote_counts(review, request.user)
        setattr(review, 'user_vote', vote_data['user_vote'])

        # Get vote data for comments
        comments = review.comments.all()
        for comment in comments:
            comment_vote_data = VoteService.get_vote_counts(comment, request.user)
            # Convert vote format for template (expects -1, 0, 1)
            if comment_vote_data['user_vote'] == 'up':
                comment_votes[comment.id] = 1
            elif comment_vote_data['user_vote'] == 'down':
                comment_votes[comment.id] = -1
            else:
                comment_votes[comment.id] = 0

    # Calculate review statistics
    total_reviews = all_reviews.count()
    if total_reviews > 0:
        avg_rating = all_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    else:
        avg_rating = 0

    context = {
        'location': location,
        'reviews_list': reviews_list,
        'user_has_reviewed': user_has_reviewed,
        'is_owner': is_owner,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'total_reviews': total_reviews,
        'average_rating': avg_rating,
        'comment_votes': comment_votes,
    }
    return render(request, 'stars_app/location/location_base.html', context)
