from rest_framework import serializers
from stars_app.models.viewinglocation import ViewingLocation
import csv
import json
import io


class BulkLocationImportSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    data = serializers.JSONField(required=False)
    format = serializers.ChoiceField(choices=['csv', 'json'], default='json')
    dry_run = serializers.BooleanField(default=True, help_text="If true, validates without saving")
    
    def validate(self, attrs):
        if not attrs.get('file') and not attrs.get('data'):
            raise serializers.ValidationError("Either 'file' or 'data' must be provided")
        
        if attrs.get('file') and attrs.get('data'):
            raise serializers.ValidationError("Provide either 'file' or 'data', not both")
        
        return attrs
    
    def parse_csv(self, file_content):
        """Parse CSV file and return list of location data"""
        locations = []
        text_content = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
        csv_reader = csv.DictReader(io.StringIO(text_content))
        
        required_fields = ['name', 'latitude', 'longitude']
        
        for row in csv_reader:
            # Validate required fields
            missing_fields = [field for field in required_fields if not row.get(field)]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Row missing required fields: {', '.join(missing_fields)} - {row}"
                )
            
            try:
                location_data = {
                    'name': row['name'],
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'elevation': float(row.get('elevation', 0)),
                    'formatted_address': row.get('formatted_address', ''),
                    'administrative_area': row.get('administrative_area', ''),
                    'locality': row.get('locality', ''),
                    'country': row.get('country', ''),
                }
                locations.append(location_data)
            except (ValueError, KeyError) as e:
                raise serializers.ValidationError(f"Invalid data in row: {row} - {str(e)}")
        
        return locations
    
    def parse_json(self, data):
        """Parse JSON data and return list of location data and validation errors"""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(f"Invalid JSON: {str(e)}")
        
        if not isinstance(data, list):
            raise serializers.ValidationError("JSON data must be a list of locations")
        
        locations = []
        validation_errors = []
        required_fields = ['name', 'latitude', 'longitude']
        
        for idx, item in enumerate(data):
            # Validate required fields
            missing_fields = [field for field in required_fields if not item.get(field)]
            if missing_fields:
                validation_errors.append({
                    'index': idx,
                    'error': f"Missing required fields: {', '.join(missing_fields)}",
                    'item': item
                })
                continue
            
            try:
                latitude = float(item['latitude'])
                longitude = float(item['longitude'])
                
                # Validate coordinate ranges
                if not (-90 <= latitude <= 90):
                    validation_errors.append({
                        'index': idx,
                        'error': f"Invalid latitude {latitude}: must be between -90 and 90",
                        'item': item
                    })
                    continue
                    
                if not (-180 <= longitude <= 180):
                    validation_errors.append({
                        'index': idx,
                        'error': f"Invalid longitude {longitude}: must be between -180 and 180",
                        'item': item
                    })
                    continue
                
                location_data = {
                    'name': item['name'],
                    'latitude': latitude,
                    'longitude': longitude,
                    'elevation': float(item.get('elevation', 0)),
                    'formatted_address': item.get('formatted_address', ''),
                    'administrative_area': item.get('administrative_area', ''),
                    'locality': item.get('locality', ''),
                    'country': item.get('country', ''),
                }
                locations.append(location_data)
            except (ValueError, KeyError, TypeError) as e:
                validation_errors.append({
                    'index': idx,
                    'error': f"Invalid data: {str(e)}",
                    'item': item
                })
        
        return locations, validation_errors
    
    def check_duplicates(self, locations, user):
        """Check for duplicates within import data and existing database"""
        from geopy.distance import geodesic
        
        results = []
        duplicate_threshold_km = 0.5  # 500 meters
        
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
        
        # Check against existing locations in database
        for loc in locations:
            existing_nearby = []
            
            # Query for locations within a rough bounding box first (more efficient)
            lat_range = 0.01  # Roughly 1.1 km
            lng_range = 0.01
            
            nearby_locations = ViewingLocation.objects.filter(
                latitude__range=(loc['latitude'] - lat_range, loc['latitude'] + lat_range),
                longitude__range=(loc['longitude'] - lng_range, loc['longitude'] + lng_range)
            )
            
            # Calculate precise distances
            for existing in nearby_locations:
                distance = geodesic(
                    (loc['latitude'], loc['longitude']),
                    (existing.latitude, existing.longitude)
                ).km
                if distance < duplicate_threshold_km:
                    existing_nearby.append({
                        'id': existing.id,
                        'name': existing.name,
                        'distance_km': round(distance, 3),
                        'is_verified': existing.is_verified
                    })
            
            results.append({
                'location': loc,
                'existing_nearby': existing_nearby,
                'duplicates_in_import': loc.get('duplicates_in_import', []),
                'is_duplicate': len(existing_nearby) > 0
            })
        
        return results
    
    def create_locations(self, validated_locations, user):
        """Create ViewingLocation objects from validated data"""
        created_locations = []
        
        for loc_data in validated_locations:
            location = ViewingLocation(
                name=loc_data['name'],
                latitude=loc_data['latitude'],
                longitude=loc_data['longitude'],
                elevation=loc_data['elevation'],
                formatted_address=loc_data.get('formatted_address', ''),
                administrative_area=loc_data.get('administrative_area', ''),
                locality=loc_data.get('locality', ''),
                country=loc_data.get('country', ''),
                added_by=user
            )
            created_locations.append(location)
        
        # Bulk create for efficiency
        return ViewingLocation.objects.bulk_create(created_locations)