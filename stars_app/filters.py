import django_filters
from django.db.models import Q
from stars_app.models.viewinglocation import ViewingLocation
from geopy.distance import geodesic


class ViewingLocationFilter(django_filters.FilterSet):
    # Basic filters
    min_quality_score = django_filters.NumberFilter(field_name='quality_score', lookup_expr='gte')
    max_quality_score = django_filters.NumberFilter(field_name='quality_score', lookup_expr='lte')
    
    min_light_pollution = django_filters.NumberFilter(field_name='light_pollution_value', lookup_expr='gte')
    max_light_pollution = django_filters.NumberFilter(field_name='light_pollution_value', lookup_expr='lte')
    
    # Verification filters
    verified_only = django_filters.BooleanFilter(method='filter_verified_only')
    min_reviews = django_filters.NumberFilter(method='filter_min_reviews')
    min_visitor_count = django_filters.NumberFilter(field_name='visitor_count', lookup_expr='gte')
    
    # Location-based filters
    radius = django_filters.NumberFilter(method='filter_by_radius')
    lat = django_filters.NumberFilter(method='filter_by_radius')
    lng = django_filters.NumberFilter(method='filter_by_radius')
    
    # Time-based filters
    recently_visited = django_filters.BooleanFilter(method='filter_recently_visited')
    added_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    added_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Advanced filters
    has_photos = django_filters.BooleanFilter(method='filter_has_photos')
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    
    # Category and tag filters
    category = django_filters.CharFilter(field_name='categories__slug', lookup_expr='exact')
    categories = django_filters.CharFilter(method='filter_categories')
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='exact')
    tags = django_filters.CharFilter(method='filter_tags')
    
    class Meta:
        model = ViewingLocation
        fields = {
            'country': ['exact', 'icontains'],
            'administrative_area': ['exact', 'icontains'],
            'locality': ['exact', 'icontains'],
            'is_verified': ['exact'],
            'times_reported': ['exact', 'lt', 'gt'],
        }
    
    def filter_verified_only(self, queryset, name, value):
        """Filter to show only verified locations when True"""
        if value:
            return queryset.filter(is_verified=True)
        return queryset
    
    def filter_min_reviews(self, queryset, name, value):
        """Filter locations with minimum number of reviews"""
        return queryset.filter(rating_count__gte=value)
    
    def filter_by_radius(self, queryset, name, value):
        """Filter locations within a radius (km) of a given lat/lng point"""
        # Only apply radius filtering when all three parameters are present
        lat = self.request.GET.get('lat')
        lng = self.request.GET.get('lng')
        radius = self.request.GET.get('radius')
        
        # Return original queryset unless we have all required parameters
        if not (lat and lng and radius):
            return queryset
            
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
            
            # Filter locations within the radius
            filtered_ids = []
            for location in queryset:
                distance = geodesic(
                    (lat, lng),
                    (location.latitude, location.longitude)
                ).km
                if distance <= radius:
                    filtered_ids.append(location.id)
            
            return queryset.filter(id__in=filtered_ids)
        except (ValueError, TypeError):
            return queryset
    
    def filter_recently_visited(self, queryset, name, value):
        """Filter locations visited in the last 30 days"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(last_visited__gte=thirty_days_ago)
        return queryset
    
    def filter_has_photos(self, queryset, name, value):
        """Filter locations that have photos (placeholder for future implementation)"""
        # This will be implemented when photo upload feature is added
        return queryset
    
    def filter_min_rating(self, queryset, name, value):
        """Filter locations with minimum average rating"""
        return queryset.filter(average_rating__gte=value)
    
    def filter_categories(self, queryset, name, value):
        """Filter by multiple categories (comma-separated slugs) - AND operation"""
        category_slugs = [slug.strip() for slug in value.split(',')]
        # Filter locations that have ALL specified categories
        for slug in category_slugs:
            queryset = queryset.filter(categories__slug=slug)
        return queryset.distinct()
    
    def filter_tags(self, queryset, name, value):
        """Filter by multiple tags (comma-separated slugs)"""
        tag_slugs = [slug.strip() for slug in value.split(',')]
        return queryset.filter(tags__slug__in=tag_slugs).distinct()