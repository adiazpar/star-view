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
# - Delegates business logic to service layer (ReportService, VoteService, ResponseService)             #
# - Template views are read-only; all write operations use API endpoints                                #
# - Favorite operations are handled by FavoriteLocationViewSet in views_favorite.py                     #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Avg

# REST Framework imports:
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

# Model imports:
from ..models import Location
from ..models import Review

# Serializer imports:
from ..serializers import LocationSerializer
from ..serializers import MapLocationSerializer
from ..serializers import LocationInfoPanelSerializer

# Service imports:
from ..services import ReportService
from ..services import ResponseService
from ..services import VoteService



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
    
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    # Create a new location:
    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)


    # Submit a report about this location using the ReportService:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        location = self.get_object()

        # Use ReportService to handle report submission
        success, message, status_code = ReportService.submit_report(
            user=request.user,
            content_object=location,
            report_type=request.data.get('report_type', 'OTHER'),
            description=request.data.get('description', '')
        )

        if success:
            # Increment report counter on the location
            location.times_reported += 1
            location.save()
            return ResponseService.success(message, status_code=status_code)
        else:
            return ResponseService.error(message, status_code=status_code)


    # ----------------------------------------------------------------------------- #
    # Get minimal location data optimized for map display.                          #
    #                                                                               #
    # Returns a lightweight JSON array containing only the essential fields         #
    # needed to render markers on the 3D globe interface.                           #
    # ----------------------------------------------------------------------------- #
    @action(detail=False, methods=['GET'], serializer_class=MapLocationSerializer)
    def map_markers(self, request):
        
        # Get all locations
        queryset = Location.objects.all()

        # Optimize database query - only fetch needed columns
        queryset = queryset.only('id', 'name', 'latitude', 'longitude')

        # Serialize and return as simple array
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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
# Shows all reviews with the user's review first (if exists) and enriches      #
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
    return render(request, 'stars_app/location_details/base.html', context)
