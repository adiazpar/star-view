# Bulk Location Import Feature

## Overview
This document details the implementation of a bulk import system for viewing locations. The feature allows administrators and trusted users to import multiple locations at once from CSV or JSON files, with comprehensive validation and duplicate detection.

## Why Bulk Import Was Needed

### Previous State
- Locations added one at a time through UI
- No way to import from external sources
- Time-consuming for adding multiple locations
- No validation for bulk data
- Risk of creating many duplicates

### Problems Solved
- **Efficiency**: Adding many locations was extremely slow
- **Data Migration**: No way to import from other systems
- **Quality Control**: Manual entry led to inconsistencies
- **Duplicate Prevention**: Multiple similar locations created
- **Validation**: No way to validate data before import

## Implementation Details

### BulkLocationImportSerializer

```python
class BulkLocationImportSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    data = serializers.JSONField(required=False)
    format = serializers.ChoiceField(choices=['csv', 'json'], default='json')
    dry_run = serializers.BooleanField(default=True, help_text="If true, validates without saving")
```

### Key Features

#### 1. Format Support
- **CSV**: Standard comma-separated values with headers
- **JSON**: Array of location objects
- **File Upload**: Direct file upload support
- **Raw Data**: JSON data in request body

#### 2. Validation Process
```python
def parse_csv(self, file_content):
    """Parse CSV file and return list of location data"""
    required_fields = ['name', 'latitude', 'longitude']
    
    for row in csv_reader:
        # Validate required fields
        missing_fields = [field for field in required_fields if not row.get(field)]
        if missing_fields:
            raise serializers.ValidationError(
                f"Row missing required fields: {', '.join(missing_fields)}"
            )
```

#### 3. Duplicate Detection
```python
def check_duplicates(self, locations, user):
    """Check for duplicates within import data and existing database"""
    duplicate_threshold_km = 0.5  # 500 meters
    
    # Check within import data
    for i, loc1 in enumerate(locations):
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

### API Endpoint

```python
@action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
def bulk_import(self, request):
    """Bulk import locations from CSV or JSON file/data"""
    serializer = BulkLocationImportSerializer(data=request.data)
    
    # Features:
    # - Dry run mode for validation
    # - Duplicate detection
    # - Detailed error reporting
    # - Batch creation for efficiency
```

## Usage Examples

### CSV Import (Dry Run)
```bash
curl -X POST http://localhost:8000/api/v1/locations/bulk_import/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@locations.csv" \
  -F "format=csv" \
  -F "dry_run=true"
```

CSV Format:
```csv
name,latitude,longitude,elevation,formatted_address,country
"Dark Sky Park",40.7128,-74.0060,100,"123 Main St, New York, NY","USA"
"Mountain Observatory",34.0522,-118.2437,500,"456 Hill Rd, Los Angeles, CA","USA"
```

### JSON Import
```bash
curl -X POST http://localhost:8000/api/v1/locations/bulk_import/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "dry_run": false,
    "data": [
      {
        "name": "Desert Viewing Area",
        "latitude": 33.4484,
        "longitude": -112.0740,
        "elevation": 300,
        "formatted_address": "Phoenix, AZ",
        "country": "USA"
      }
    ]
  }'
```

### Response Format
```json
{
    "total_locations": 2,
    "duplicates_found": 1,
    "dry_run": true,
    "results": [
        {
            "location": {
                "name": "Dark Sky Park",
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "existing_nearby": [
                {
                    "id": 123,
                    "name": "Central Park Observatory",
                    "distance_km": 0.245,
                    "is_verified": true
                }
            ],
            "duplicates_in_import": [],
            "is_duplicate": true
        }
    ]
}
```

## Validation Rules

### Required Fields
- `name`: Location name (string)
- `latitude`: Valid latitude (-90 to 90)
- `longitude`: Valid longitude (-180 to 180)

### Optional Fields
- `elevation`: Elevation in meters (default: 0)
- `formatted_address`: Full address string
- `administrative_area`: State/Province
- `locality`: City/Town
- `country`: Country name

### Duplicate Detection
- Checks within 500m radius by default
- Compares against existing database locations
- Identifies duplicates within import batch
- Provides distance measurements

## Benefits

### For Administrators
- Import locations from external sources
- Migrate data from other systems
- Validate data before import
- Prevent duplicate creation

### For Data Quality
- Consistent data format
- Automatic validation
- Duplicate prevention
- Error reporting

### For Efficiency
- Bulk creation reduces time
- Batch database operations
- Dry run prevents mistakes
- Detailed import reports

## Security Considerations

- Requires authentication
- Permission checks for bulk operations
- File size limits enforced
- Input validation prevents injection

## Future Enhancements

1. **Import Templates**: Downloadable CSV/JSON templates
2. **Field Mapping**: Custom field mapping UI
3. **Import History**: Track import batches
4. **Undo Import**: Rollback capability
5. **Progress Tracking**: Real-time import progress
6. **Auto-Enrichment**: Automatic data enrichment during import