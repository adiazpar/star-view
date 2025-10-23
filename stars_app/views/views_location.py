# ----------------------------------------------------------------------------------------------------- #
# This views_location.py file handles all location-related views and API endpoints:                    #
#                                                                                                       #
# Purpose:                                                                                              #
# Provides REST API endpoints and template views for managing stargazing locations. Handles location   #
# creation, retrieval, updates, and enrichment with geographic data (elevation, address).              #
#                                                                                                       #
# Key Features:                                                                                         #
# - LocationViewSet: Full CRUD API for locations with filtering, search, and ordering                  #
# - Map optimization: Lightweight endpoints for 3D globe (map_markers + info_panel, 96%+ reduction)    #
# - Duplicate detection: Checks for nearby locations before creation to prevent duplicates             #
# - Favorite management: Users can favorite/unfavorite locations and check favorite status             #
# - Report handling: Users can report problematic locations using the generic Report model             #
# - Data enrichment: Automatic elevation and address updates via Mapbox APIs                           #
# - Template view: location_details displays location info with reviews for authenticated users        #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                              #
# - Integrates with ContentTypes framework for generic relationships (Vote, Report models)             #
# - Delegates geographic operations to geopy library for distance calculations                         #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models import Avg

# REST Framework imports:
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

# Model imports:
from ..models import Location
from ..models import FavoriteLocation
from ..models import Review
from ..models import Report
from ..models import Vote

# Serializer imports:
from ..serializers import LocationSerializer
from ..serializers import MapLocationSerializer
from ..serializers import LocationInfoPanelSerializer
from ..serializers import ReportSerializer

# Service imports:
from ..services import ReportService
from ..services import ResponseService

# Other imports:
from itertools import chain



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       LOCATION VIEWSET                                                #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

# ----------------------------------------------------------------------------- #
# API ViewSet for managing stargazing locations.                                #
#                                                                               #
# Provides endpoints for creating, retreiving, updating, and deleting           #
# locations. Includes actions for favoriting, reporting, duplicate checking,    #
# and review management.                                                        #
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


    # Get all reports for this location:
    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def reports(self, request, pk=None):
        location = self.get_object()

        # Only staff can see all reports
        if not request.user.is_staff:
            return ResponseService.error(
                'You do not have permission to view reports',
                status_code=status.HTTP_403_FORBIDDEN
            )

        content_type = ContentType.objects.get_for_model(location)

        # Get all reports for this location
        reports = Report.objects.filter(
            content_type=content_type,
            object_id=location.id
        )
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)


    # Check if a location is favorited by the current user:
    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def is_favorited(self, request, pk=None):
        location = self.get_object()
        is_favorited = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).exists()
        message = 'Location is favorited' if is_favorited else 'Location is not favorited'
        return ResponseService.success(
            message,
            data={'is_favorited': is_favorited}
        )


    # Add a location to user's favorites:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        location = self.get_object()

        # Check if already favorited:
        existing_favorite = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).first()

        if existing_favorite:
            return ResponseService.error(
                'Location already favorited',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create a new favorite:
        FavoriteLocation.objects.create(
            user=request.user,
            location=location
        )
        serializer = self.get_serializer(location)
        return Response(serializer.data)


    # Remove a location from a user's favorites:
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        location = self.get_object()

        deleted_count, _ = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).delete()

        if deleted_count:
            serializer = self.get_serializer(location)
            return Response(serializer.data)
        return ResponseService.error(
            'Location was not favorited',
            status_code=status.HTTP_400_BAD_REQUEST
        )

        
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
        queryset = queryset.only('id', 'name', 'latitude', 'longitude', 'quality_score')

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
# Shows all reviews with the user's review first (if exists), handles vote      #
# information for authenticated users, and allows review submissions.           #
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
    reviews_list = list(chain([user_review], other_reviews)) if user_review else list(other_reviews)
    reviews_list = [r for r in reviews_list if r is not None]

    # Create vote dictionaries to pass to template
    comment_votes = {}

    # Add vote information for authenticated users
    for review in reviews_list:
        if request.user.is_authenticated:
            # Get the vote for this review using generic Vote model
            review_content_type = ContentType.objects.get_for_model(review)

            vote = Vote.objects.filter(
                user=request.user,
                content_type=review_content_type,
                object_id=review.id
            ).first()

            # Add vote information as an attribute
            setattr(review, 'user_vote', 'up' if vote and vote.is_upvote else 'down' if vote else None)
        else:
            setattr(review, 'user_vote', None)

        # Prefetch comments with vote information
        comments = review.comments.all()
        for comment in comments:
            if request.user.is_authenticated:
                # Get user's vote on this comment using generic Vote model
                comment_content_type = ContentType.objects.get_for_model(comment)

                comment_vote = Vote.objects.filter(
                    user=request.user,
                    content_type=comment_content_type,
                    object_id=comment.id
                ).first()

                if comment_vote:
                    user_vote_value = 1 if comment_vote.is_upvote else -1
                    comment_votes[comment.id] = user_vote_value
                else:
                    comment_votes[comment.id] = 0
            else:
                comment_votes[comment.id] = 0

    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated and not is_owner:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating:
            review, created = Review.objects.get_or_create(
                location=location,
                user=request.user,
                defaults={'rating': rating, 'comment': comment}
            )
            if not created:
                review.rating = rating
                review.comment = comment
                review.save()

            # Handle image uploads
            uploaded_images = request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.model_review_photo import ReviewPhoto

                # Validate number of images (max 5 per review)
                existing_photos_count = review.photos.count()
                if existing_photos_count + len(uploaded_images) > 5:
                    return redirect('location_details', location_id=location_id)

                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5-existing_photos_count]):
                    try:
                        ReviewPhoto.objects.create(
                            review=review,
                            image=image,
                            order=existing_photos_count + idx
                        )
                    except Exception as e:
                        # Continue processing other images on error
                        pass

            # Review submitted successfully
            return redirect('location_details', location_id=location_id)

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
