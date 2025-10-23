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
# - Favorite management: Users can favorite/unfavorite locations and set custom nicknames              #
# - Report handling: Users can report problematic locations using the generic Report model             #
# - Data enrichment: Automatic elevation and address updates via Mapbox APIs                           #
# - Review integration: Users can add, update, and delete reviews for locations                        #
#                                                                                                       #
# Architecture:                                                                                         #
# - Uses Django REST Framework ViewSets for API endpoints                                              #
# - Integrates with ContentTypes framework for generic relationships (Vote, Report models)             #
# - Delegates geographic operations to geopy library for distance calculations                         #
# ----------------------------------------------------------------------------------------------------- #

# Django imports:
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.db.models import Avg
from django.core.paginator import Paginator

# REST Framework imports:
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

# Model imports:
from stars_app.models.model_location import Location
from stars_app.models.model_location_favorite import FavoriteLocation
from stars_app.models.model_review import Review
from stars_app.models.model_report import Report
from stars_app.models.model_vote import Vote
from django.contrib.auth.models import User

# Serializer imports:
from stars_app.serializers import (
    LocationSerializer,
    MapLocationSerializer,
    LocationInfoPanelSerializer,
    ReviewSerializer,
    ReportSerializer,
    FavoriteLocationSerializer,
)

# Service imports:
from stars_app.services import ResponseService

# Other imports:
from itertools import chain
import json
from rest_framework import serializers



# ----------------------------------------------------------------------------------------------------- #
#                                                                                                       #
#                                       LOCATION VIEWSET                                                #
#                                                                                                       #
# ----------------------------------------------------------------------------------------------------- #

class LocationViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing stargazing locations.

    Provides endpoints for creating, retrieving, updating, and deleting locations.
    Includes actions for favoriting, reporting, duplicate checking, and review management.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'formatted_address', 'locality']
    ordering_fields = ['quality_score', 'created_at', 'visitor_count', 'rating_count']
    ordering = ['-quality_score']


    def get_queryset(self):
        """Filter queryset to show only favorites if requested."""
        queryset = Location.objects.all()
        favorites_only = self.request.query_params.get('favorites_only', 'false')
        if favorites_only.lower() == 'true' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=self.request.user)
        return queryset


    def perform_create(self, serializer):
        """Create a new location with duplicate checking."""
        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        elevation = serializer.validated_data.get('elevation', 0)

        # Check for nearby duplicates before creating
        duplicates = self.check_for_duplicates(latitude, longitude)
        if duplicates and not self.request.data.get('force_create', False):
            nearby_locations = []
            for location in duplicates:
                nearby_locations.append({
                    'id': location.id,
                    'name': location.name,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'quality_score': location.quality_score,
                })

            raise serializers.ValidationError({
                'duplicates_found': True,
                'nearby_locations': nearby_locations,
                'message': 'Similar locations found nearby. Add force_create=true to create anyway.'
            })

        serializer.save(added_by=self.request.user)


    def check_for_duplicates(self, latitude, longitude, radius_km=0.5):
        """
        Check for duplicate locations within a radius using geopy.

        Args:
            latitude (float): Latitude to check
            longitude (float): Longitude to check
            radius_km (float): Search radius in kilometers (default 0.5)

        Returns:
            list: List of Location objects within the radius
        """
        from geopy.distance import geodesic

        # Query for locations within a rough bounding box first
        lat_range = 0.01  # Roughly 1.1 km
        lng_range = 0.01

        nearby_locations = Location.objects.filter(
            latitude__range=(latitude - lat_range, latitude + lat_range),
            longitude__range=(longitude - lng_range, longitude + lng_range)
        )

        # Calculate precise distances
        duplicates = []
        for location in nearby_locations:
            distance = geodesic(
                (latitude, longitude),
                (location.latitude, location.longitude)
            ).km
            if distance <= radius_km:
                duplicates.append(location)

        return duplicates


    @action(detail=True, methods=['POST'])
    def update_elevation(self, request, pk=None):
        """Manually trigger elevation update for a location."""
        location = self.get_object()
        success = location.update_elevation_from_mapbox()

        if success:
            location.calculate_quality_score()
            location.save()
            serializer = self.get_serializer(location)
            return Response(serializer.data)

        return Response(
            {'detail': 'Failed to update elevation'},
            status=status.HTTP_400_BAD_REQUEST
        )


    @action(detail=False, methods=['GET'])
    def check_duplicates(self, request):
        """Check for duplicate locations before creating."""
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius_km', 0.5))

        if not latitude or not longitude:
            return Response(
                {'detail': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Invalid latitude or longitude values'},
                status=status.HTTP_400_BAD_REQUEST
            )

        duplicates = self.check_for_duplicates(latitude, longitude, radius_km)

        return Response({
            'duplicates_found': len(duplicates) > 0,
            'count': len(duplicates),
            'radius_km': radius_km,
            'locations': LocationSerializer(duplicates, many=True).data
        })


    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        """Submit a report about this location using the generic Report model."""
        location = self.get_object()
        content_type = ContentType.objects.get_for_model(location)

        # Check if user already reported this location
        existing_report = Report.objects.filter(
            content_type=content_type,
            object_id=location.id,
            reported_by=request.user
        ).first()

        if existing_report:
            return Response(
                {'detail': 'You have already submitted a report for this location'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare additional data (e.g., duplicate location ID)
        additional_data = {}
        if request.data.get('duplicate_of_id'):
            additional_data['duplicate_of_id'] = request.data.get('duplicate_of_id')

        # Prepare report data for the generic Report model
        report_data = {
            'object_id': location.id,
            'report_type': request.data.get('report_type'),
            'description': request.data.get('description', ''),
            'additional_data': additional_data if additional_data else None
        }

        serializer = ReportSerializer(data=report_data)
        if serializer.is_valid():
            report = serializer.save(
                content_type=content_type,
                reported_by=request.user
            )

            # Increment report counter on the location
            location.times_reported += 1
            location.save()

            return Response(
                ReportSerializer(report).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['GET'], permission_classes=[IsAuthenticated])
    def reports(self, request, pk=None):
        """Get all reports for this location (staff only)."""
        location = self.get_object()

        # Only staff can see all reports
        if not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to view reports'},
                status=status.HTTP_403_FORBIDDEN
            )

        content_type = ContentType.objects.get_for_model(location)

        # Get all reports for this location
        reports = Report.objects.filter(
            content_type=content_type,
            object_id=location.id
        )
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['POST', 'GET'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add a location to user's favorites."""
        location = self.get_object()

        # Handle GET request case:
        if request.method == "GET":
            is_favorited = FavoriteLocation.objects.filter(
                user=request.user,
                location=location
            ).exists()
            return Response({
                'is_favorited': is_favorited,
                'detail': 'Location is favorited' if is_favorited else 'Location is not favorited'
            })

        # Check if already favorited:
        existing_favorite = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).first()

        if existing_favorite:
            return Response(
                {'detail': 'Location already favorited'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create a new favorite:
        FavoriteLocation.objects.create(
            user=request.user,
            location=location
        )
        serializer = self.get_serializer(location)
        return Response(serializer.data)


    @action(detail=True, methods=['POST', 'GET'], permission_classes=[IsAuthenticated])
    def unfavorite(self, request, pk=None):
        """Remove a location from user's favorites."""
        location = self.get_object()

        # If it's a GET request, just return the current status
        if request.method == 'GET':
            is_favorited = FavoriteLocation.objects.filter(
                user=request.user,
                location=location
            ).exists()
            return Response({
                'is_favorited': is_favorited,
                'detail': 'Location is favorited' if is_favorited else 'Location is not favorited'
            })

        deleted_count, _ = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).delete()

        if deleted_count:
            serializer = self.get_serializer(location)
            return Response(serializer.data)
        return Response(
            {'detail': 'Location was not favorited'},
            status=status.HTTP_400_BAD_REQUEST
        )


    @action(detail=True, methods=['GET'])
    def favorites(self, request):
        """Get all favorited locations for the current user."""
        favorites = self.get_queryset().filter(favorited_by__user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['POST'], url_path='update-nickname', url_name='update-nickname')
    def update_nickname(self, request, pk=None):
        """Update the nickname for a favorited location."""
        try:
            location = self.get_object()
            favorite = FavoriteLocation.objects.get(
                user=request.user,
                location=location
            )

            if not request.data:
                return Response(
                    {'success': False, 'detail': 'No data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            nickname = request.data.get('nickname', '').strip()
            favorite.nickname = nickname if nickname else None
            favorite.save()

            return Response({
                'success': True,
                'display_name': favorite.get_display_name(),
                'original_name': location.name,
                'detail': 'Nickname updated successfully'
            }, content_type='application/json')

        except FavoriteLocation.DoesNotExist:
            return Response(
                {'success': False, 'detail': 'Location is not in your favorites'},
                status=status.HTTP_404_NOT_FOUND,
                content_type='application/json'
            )
        except Exception as e:
            return Response(
                {'success': False, 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )


    @action(detail=True, methods=['POST'])
    def update_address(self, request, pk=None):
        """Manually trigger address update for a location."""
        location = self.get_object()
        success = location.update_address_from_coordinates()

        if success:
            location.save()
            serializer = self.get_serializer(location)
            return Response(serializer.data)

        return Response(
            {'detail': 'Failed to update address'},
            status=status.HTTP_400_BAD_REQUEST
        )


    @action(detail=True, methods=['POST'])
    def add_review(self, request, pk=None):
        """Add a review to a location."""
        location = self.get_object()

        # Check if user already reviewed this location
        existing_review = Review.objects.filter(
            user=request.user,
            location=location
        ).first()

        if existing_review:
            return Response(
                {'detail': 'You have already reviewed this location'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(user=request.user, location=location)

            # Handle image uploads
            uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.model_review_photo import ReviewPhoto

                # Validate number of images
                if len(uploaded_images) > 5:
                    review.delete()
                    return Response(
                        {'detail': 'You can upload a maximum of 5 photos per review'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Process each uploaded image
                for idx, image in enumerate(uploaded_images[:5]):
                    try:
                        ReviewPhoto.objects.create(
                            review=review,
                            image=image,
                            order=idx
                        )
                    except Exception as e:
                        # Continue processing other images on error
                        pass

            # Return the review with photos included
            serializer = ReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['PUT'])
    def update_review(self, request, pk=None):
        """Update an existing review for a location."""
        location = self.get_object()

        review = Review.objects.filter(
            user_id=request.user.id,
            location_id=location.id
        ).first()

        if not review:
            return Response(
                {'detail': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Handle image uploads for review updates
            uploaded_images = request.FILES.getlist('images') or request.FILES.getlist('review_images')
            if uploaded_images:
                from stars_app.models.model_review_photo import ReviewPhoto

                # Check existing photos count
                existing_photos_count = review.photos.count()
                if existing_photos_count + len(uploaded_images) > 5:
                    return Response(
                        {'detail': f'You can only have up to 5 photos per review. You already have {existing_photos_count} photos.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

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

            # Handle image deletions if specified
            delete_photo_ids = request.data.get('delete_photo_ids', [])
            if delete_photo_ids:
                # Parse JSON string if needed
                if isinstance(delete_photo_ids, str):
                    try:
                        delete_photo_ids = json.loads(delete_photo_ids)
                    except json.JSONDecodeError:
                        delete_photo_ids = []

                if delete_photo_ids:
                    review.photos.filter(id__in=delete_photo_ids).delete()

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['DELETE'])
    def delete_review(self, request, pk=None):
        """Delete a review for a location."""
        location = self.get_object()
        review = Review.objects.filter(
            user=request.user,
            location=location
        ).first()

        if not review:
            return Response(
                {'detail': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['GET'], serializer_class=MapLocationSerializer)
    def map_markers(self, request):
        """
        Get minimal location data optimized for map display.

        Returns a lightweight JSON array containing only the essential fields
        needed to render markers on the 3D globe interface. This endpoint:

        - Reduces payload size by ~97% compared to the full locations endpoint
        - Returns simple JSON array (no pagination wrapper)
        - Optimizes database query using .only() to fetch minimal columns

        Performance:
            - Full endpoint: ~500KB for 500 locations
            - This endpoint: ~15KB for 500 locations

        Response format:
            [
                {
                    "id": 1,
                    "name": "Dark Sky Observatory",
                    "latitude": 40.1234,
                    "longitude": -105.5678,
                    "quality_score": 87.5
                },
                ...
            ]

        Frontend integration:
            1. Use this endpoint for initial map load
            2. Convert response to GeoJSON for Mapbox GL JS
            3. On marker click, fetch info panel data via GET /api/locations/{id}/info_panel/

        Query parameters:
            - favorites_only: Filter to user's favorited locations (requires auth)
            - search: Search by name, address, or locality
            - ordering: Sort by quality_score, created_at, etc.
        """
        # Get filtered queryset (respects favorites_only and other filters)
        queryset = self.get_queryset()

        # Optimize database query - only fetch needed columns
        queryset = queryset.only('id', 'name', 'latitude', 'longitude', 'quality_score')

        # Serialize and return as simple array
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['GET'], serializer_class=LocationInfoPanelSerializer)
    def info_panel(self, request, pk=None):
        """
        Get optimized location data for map info panel display.

        Returns just enough data to populate the info panel that appears when
        a user clicks a marker on the map. Excludes heavy nested data like full
        review content, photos, comments, and vote data.

        Performance:
            - Full location endpoint: ~7KB (with all reviews/photos/votes)
            - This endpoint: ~300 bytes
            - Reduction: ~95%

        Response format:
            {
                "id": 1,
                "name": "Dark Sky Observatory",
                "latitude": 40.1234,
                "longitude": -105.5678,
                "elevation": 2500.0,
                "formatted_address": "123 Mountain Road, Colorado",
                "quality_score": 87.5,
                "added_by_id": 5,
                "average_rating": 4.5,
                "review_count": 12
            }

        Frontend integration:
            - Called by MapController.handleLocationSelection()
            - Use for info panel display only
            - For full details page, use GET /api/locations/{id}/
        """
        location = self.get_object()
        serializer = self.get_serializer(location)
        return Response(serializer.data)


class LocationCreateView(APIView):
    """
    DRF API endpoint for creating new locations (legacy, use LocationViewSet instead).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Create new viewing location
            location = Location.objects.create(
                name=request.data['name'],
                latitude=request.data['latitude'],
                longitude=request.data['longitude'],
                added_by=request.user
            )

            return ResponseService.success(
                'Location created successfully',
                data={
                    'id': location.id,
                    'name': location.name,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'elevation': location.elevation,
                    'formatted_address': location.formatted_address,
                    'quality_score': location.quality_score
                },
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            return ResponseService.error(str(e), status_code=status.HTTP_400_BAD_REQUEST)


def location_details(request, location_id):
    """
    Display detailed information about a location including reviews.

    Shows paginated reviews with the user's review first (if exists), handles vote
    information for authenticated users, and allows review submissions.
    """
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

    # Combine reviews and handle pagination
    reviews_list = list(chain([user_review], other_reviews)) if user_review else list(other_reviews)
    reviews_list = [r for r in reviews_list if r is not None]

    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Create vote dictionaries to pass to template
    comment_votes = {}

    # Add vote information for authenticated users
    for review in page_obj:
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
        'page_obj': page_obj,
        'user_has_reviewed': user_has_reviewed,
        'is_owner': is_owner,
        'mapbox_token': settings.MAPBOX_TOKEN,
        'total_reviews': total_reviews,
        'average_rating': avg_rating,
        'comment_votes': comment_votes,
    }
    return render(request, 'stars_app/location_details/base.html', context)
