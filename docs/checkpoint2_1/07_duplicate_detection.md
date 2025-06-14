# Duplicate Detection System

## Overview
This document details the implementation of a comprehensive duplicate detection system for viewing locations. The system automatically checks for potential duplicates when creating new locations and provides tools for managing duplicate reports.

## Why Duplicate Detection Was Needed

### Previous State
- Multiple entries for same location
- No validation against existing locations  
- Confused users seeing duplicates
- Fragmented reviews and ratings
- Wasted database resources

### Problems Solved
- **Data Quality**: Multiple entries for same physical location
- **User Confusion**: Which location entry to use/review
- **Split Community**: Reviews scattered across duplicates
- **Search Pollution**: Duplicate results in searches
- **Database Efficiency**: Redundant data storage

## Implementation Details

### Automatic Detection on Creation

```python
def perform_create(self, serializer):
    latitude = serializer.validated_data['latitude']
    longitude = serializer.validated_data['longitude']
    
    # Check for nearby duplicates before creating
    duplicates = self.check_for_duplicates(latitude, longitude)
    if duplicates and not self.request.data.get('force_create', False):
        raise serializers.ValidationError({
            'duplicates_found': True,
            'nearby_locations': ViewingLocationSerializer(duplicates, many=True).data,
            'message': 'Similar locations found nearby. Add force_create=true to create anyway.'
        })
    
    serializer.save(added_by=self.request.user)
```

### Duplicate Detection Algorithm

```python
def check_for_duplicates(self, latitude, longitude, radius_km=0.5):
    """Check for duplicate locations within a radius"""
    from geopy.distance import geodesic
    
    # Query for locations within a rough bounding box first
    lat_range = 0.01  # Roughly 1.1 km
    lng_range = 0.01
    
    nearby_locations = ViewingLocation.objects.filter(
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
```

### Manual Duplicate Checking Endpoint

```python
@action(detail=False, methods=['POST'])
def check_duplicates(self, request):
    """Check for duplicate locations before creating"""
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    radius_km = float(request.data.get('radius_km', 0.5))
    
    duplicates = self.check_for_duplicates(latitude, longitude, radius_km)
    
    return Response({
        'duplicates_found': len(duplicates) > 0,
        'count': len(duplicates),
        'radius_km': radius_km,
        'locations': ViewingLocationSerializer(duplicates, many=True).data
    })
```

### Duplicate Reporting

```python
@action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
def report(self, request, pk=None):
    """Submit a report about this location"""
    location = self.get_object()
    
    report_data = {
        'location': location.id,
        'report_type': request.data.get('report_type'),
        'description': request.data.get('description'),
        'duplicate_of': request.data.get('duplicate_of_id')
    }
    
    # Create report with duplicate information
    report = LocationReport.objects.create(
        location=location,
        reported_by=request.user,
        report_type='DUPLICATE',
        duplicate_of_id=duplicate_of_id,
        description="Duplicate location"
    )
```

## Usage Examples

### Check Before Creating
```bash
curl -X POST http://localhost:8000/api/v1/locations/check_duplicates/ \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 0.5
  }'
```

Response:
```json
{
    "duplicates_found": true,
    "count": 2,
    "radius_km": 0.5,
    "locations": [
        {
            "id": 123,
            "name": "Central Park Observatory",
            "latitude": 40.7130,
            "longitude": -74.0058,
            "distance_km": 0.245,
            "is_verified": true,
            "quality_score": 85
        },
        {
            "id": 456,
            "name": "Central Park Stargazing Spot",
            "latitude": 40.7125,
            "longitude": -74.0062,
            "distance_km": 0.342,
            "is_verified": false,
            "quality_score": 72
        }
    ]
}
```

### Force Create Despite Duplicates
```bash
curl -X POST http://localhost:8000/api/v1/locations/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Special Spot",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "force_create": true
  }'
```

### Report a Duplicate
```bash
curl -X POST http://localhost:8000/api/v1/locations/123/report/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "DUPLICATE",
    "duplicate_of_id": 456,
    "description": "This is the same location as #456"
  }'
```

## Duplicate Detection in Bulk Import

The bulk import feature includes comprehensive duplicate checking:

```python
def check_duplicates(self, locations, user):
    """Check for duplicates within import data and existing database"""
    duplicate_threshold_km = 0.5
    
    # Check for duplicates within the import data
    for i, loc1 in enumerate(locations):
        loc1['duplicates_in_import'] = []
        for j, loc2 in enumerate(locations[i+1:], i+1):
            distance = geodesic(
                (loc1['latitude'], loc1['longitude']),
                (loc2['latitude'], loc2['longitude'])
            ).km
            if distance < duplicate_threshold_km:
                loc1['duplicates_in_import'].append({
                    'index': j,
                    'name': loc2['name'],
                    'distance_km': round(distance, 3)
                })
```

## Detection Parameters

### Default Settings
- **Radius**: 500 meters (0.5 km)
- **Bounding Box**: ~1.1 km for initial query
- **Precision**: Haversine formula for accurate distance

### Customizable Options
- Radius can be adjusted per request
- Different thresholds for different location types
- Consider elevation differences (future)

## Handling Duplicates

### For Users
1. Warning shown with nearby locations
2. Option to force create anyway
3. Can report existing duplicates
4. See distance to potential duplicates

### For Administrators
1. View duplicate reports
2. Merge duplicate locations (future)
3. Set canonical location
4. Transfer reviews/ratings

## Benefits

### Data Quality
- Prevents accidental duplicates
- Consolidates location information
- Improves search results
- Reduces confusion

### User Experience
- Clear warnings about duplicates
- Ability to override when needed
- Find existing locations easier
- Consolidated reviews

### Performance
- Fewer database entries
- More efficient searches
- Reduced storage needs
- Better caching

## Future Enhancements

1. **Smart Merging**: Automated duplicate merging with data preservation
2. **Fuzzy Matching**: Consider name similarity in detection
3. **Elevation Tolerance**: Account for vertical separation
4. **ML Detection**: Machine learning for better duplicate identification
5. **Bulk Operations**: Admin tools for mass duplicate resolution
6. **History Tracking**: Maintain merge/duplicate history
7. **User Notifications**: Notify users when their locations are merged
8. **API Deduplication**: Automatic deduplication in responses

## Integration with Other Features

- **Bulk Import**: Checks both within import and against database
- **Search Results**: Duplicate filtering in search
- **Map Display**: Hide duplicates on map
- **Verification**: Prefer verified location when duplicates exist
- **Reports**: Special handling for duplicate reports