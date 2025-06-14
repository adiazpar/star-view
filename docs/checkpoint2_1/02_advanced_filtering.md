# Advanced Search and Filtering System

## Overview
This document details the implementation of a comprehensive filtering system for viewing locations using django-filter. The system provides powerful search capabilities including radius-based searches, quality filtering, and multi-criteria filtering.

## Why Advanced Filtering Was Needed

### Previous State
- Basic filtering limited to a few fields
- No geographical/radius-based search
- No quality-based filtering
- Limited search capabilities
- No date range filtering

### Problems Solved
- **Location Discovery**: Users couldn't find locations near them
- **Quality Search**: No way to filter by quality metrics
- **Advanced Queries**: Complex searches required custom code
- **Performance**: Database queries were inefficient
- **User Experience**: Finding relevant locations was difficult

## Implementation Details

### ViewingLocationFilter Class

```python
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
    
    # Category and tag filters
    category = django_filters.CharFilter(field_name='categories__slug', lookup_expr='exact')
    categories = django_filters.CharFilter(method='filter_categories')
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='exact')
    tags = django_filters.CharFilter(method='filter_tags')
```

### Key Filter Methods

#### Radius-Based Search
```python
def filter_by_radius(self, queryset, name, value):
    """Filter locations within a radius (km) of a given lat/lng point"""
    lat = self.request.GET.get('lat')
    lng = self.request.GET.get('lng')
    radius = self.request.GET.get('radius', 50)  # Default 50km
    
    if lat and lng and radius:
        # Use geopy to calculate distances
        filtered_ids = []
        for location in queryset:
            distance = geodesic(
                (lat, lng),
                (location.latitude, location.longitude)
            ).km
            if distance <= radius:
                filtered_ids.append(location.id)
        
        return queryset.filter(id__in=filtered_ids)
```

#### Multiple Category/Tag Filtering
```python
def filter_categories(self, queryset, name, value):
    """Filter by multiple categories (comma-separated slugs)"""
    category_slugs = [slug.strip() for slug in value.split(',')]
    return queryset.filter(categories__slug__in=category_slugs).distinct()
```

## Usage Examples

### Find Dark Sky Locations Near Me
```bash
GET /api/v1/locations/?lat=40.7128&lng=-74.0060&radius=50&min_quality_score=80
```

### Find Verified Mountain Observatories
```bash
GET /api/v1/locations/?verified_only=true&categories=mountain,observatory
```

### Recently Added High-Quality Locations
```bash
GET /api/v1/locations/?added_after=2024-01-01&min_quality_score=90&ordering=-created_at
```

### Locations with Low Light Pollution
```bash
GET /api/v1/locations/?max_light_pollution=20&min_reviews=5
```

### Complex Multi-Criteria Search
```bash
GET /api/v1/locations/?verified_only=true&min_quality_score=70&max_light_pollution=30&categories=park&radius=100&lat=34.0522&lng=-118.2437
```

## Filter Parameters Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `is_verified` | boolean | Filter by verification status |
| `verified_only` | boolean | Show only verified locations |
| `min_quality_score` | number | Minimum quality score (0-100) |
| `max_quality_score` | number | Maximum quality score (0-100) |
| `min_light_pollution` | number | Minimum light pollution value |
| `max_light_pollution` | number | Maximum light pollution value |
| `min_reviews` | number | Minimum number of reviews |
| `min_visitor_count` | number | Minimum number of visitors |
| `radius` | number | Search radius in km |
| `lat` | number | Latitude for radius search |
| `lng` | number | Longitude for radius search |
| `recently_visited` | boolean | Visited in last 30 days |
| `added_after` | datetime | Added after this date |
| `added_before` | datetime | Added before this date |
| `min_rating` | number | Minimum average rating |
| `category` | string | Single category slug |
| `categories` | string | Comma-separated category slugs |
| `tag` | string | Single tag slug |
| `tags` | string | Comma-separated tag slugs |

## Benefits

### For Users
- Find locations that match specific criteria
- Discover nearby dark sky locations
- Filter by quality and verification
- Save complex searches

### For Performance
- Efficient database queries
- Reduced data transfer
- Optimized for common searches
- Scalable filtering system

### For Developers
- Consistent filter API
- Easy to add new filters
- Reusable filter logic
- Well-documented parameters

## Integration with Other Features

- **Map Display**: Filters apply to clustered map view
- **Bulk Import**: Use filters to check for existing locations
- **User Favorites**: Filter favorite locations
- **Export**: Export filtered location sets