# Service Layer Architecture

## Overview
Extracted complex business logic from Django models into dedicated service classes. This separation improves code organization, testability, and reusability while following the Single Responsibility Principle.

## Why This Change Was Made

### Problems with Fat Models
The original `ViewingLocation` model had become a "God Object" with over 200 lines of code handling:
- Data persistence
- API integrations (Mapbox, NOAA weather)
- Complex calculations (quality scores, moon phases)
- External service coordination
- Business rule implementation

### Issues This Created
- **Hard to Test**: Business logic was tightly coupled to database models
- **Difficult to Debug**: Complex methods mixed data access with business logic
- **Poor Reusability**: Logic was locked inside specific models
- **Maintenance Nightmare**: Changes to business rules required model modifications
- **Violation of SRP**: Models had too many responsibilities

### Before Example
```python
class ViewingLocation(models.Model):
    # ... field definitions ...
    
    def get_moon_phase_name(self):
        """50+ lines of complex moon phase calculation logic"""
        if self.moon_phase is None:
            return {'short_name': 'Unknown', 'description': 'Moon phase data not available'}
        
        phase = self.moon_phase % 100
        
        if phase == 0 or phase == 100:
            return {'short_name': 'New Moon', 'description': 'The Moon is not visible from Earth'}
        elif 0 < phase <= 24:
            return {'short_name': 'Waxing Crescent', 'description': 'Less than half...'}
        # ... 40+ more lines ...
    
    def update_address_from_coordinates(self):
        """60+ lines of Mapbox API integration"""
        try:
            mapbox_token = settings.MAPBOX_TOKEN
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{self.longitude},{self.latitude}.json"
            # ... complex API handling ...
        except Exception as e:
            # ... error handling ...
    
    def calculate_quality_score(self):
        """80+ lines of quality calculation algorithm"""
        # Complex scoring algorithm mixed with data access
        
    # ... 5 more complex methods ...
```

**Problems**: 
- 200+ lines in one model
- Business logic mixed with data persistence
- Hard to test individual calculations
- Impossible to reuse logic elsewhere

## What Was Implemented

### 1. LocationService
**File**: `stars_app/services/location_service.py`

Handles all business logic related to viewing locations:

```python
class LocationService:
    """Service for handling viewing location business logic"""

    @staticmethod
    def update_address_from_coordinates(location):
        """Updates address fields using Mapbox reverse geocoding"""
        try:
            mapbox_token = settings.MAPBOX_TOKEN
            
            url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                   f"{location.longitude},{location.latitude}.json"
                   f"?access_token={mapbox_token}&types=place,region,country")
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                return False
            
            # Process response and update location object
            # ... implementation details ...
            
            return True
        except Exception as e:
            print(f"Error updating address: {str(e)}")
            return False

    @staticmethod
    def calculate_quality_score(location):
        """Calculate overall quality score for a location"""
        try:
            score = 0
            has_elevation = location.elevation and location.elevation > 0
            
            # Define weights
            weights = {
                'light_pollution': 0.3,
                'cloud_cover': 0.3,
                'elevation': 0.2 if has_elevation else 0,
                'moon': 0.2
            }
            
            # Redistribute weights if no elevation
            if not has_elevation:
                weights['light_pollution'] += 0.1
                weights['cloud_cover'] += 0.1
            
            # Calculate component scores
            if location.light_pollution_value:
                lp_score = min(100, max(0, (location.light_pollution_value - 16) * (100/6)))
                score += lp_score * weights['light_pollution']
            
            # ... more calculations ...
            
            location.quality_score = round(score, 1)
            location.save(update_fields=['quality_score'])
            return True
            
        except Exception as e:
            print(f"Error calculating quality score: {str(e)}")
            return False
    
    @staticmethod
    def initialize_location_data(location):
        """Initialize all location data after creation"""
        if getattr(settings, 'DISABLE_EXTERNAL_APIS', False):
            return
            
        # Coordinate all data updates
        try:
            LocationService.update_address_from_coordinates(location)
        except Exception as e:
            print(f"Warning: Could not update address: {e}")
            
        try:
            LocationService.update_elevation_from_mapbox(location)
        except Exception as e:
            print(f"Warning: Could not update elevation: {e}")
            
        # ... more service calls ...
```

### 2. MoonPhaseService
**File**: `stars_app/services/moon_phase_service.py`

Handles moon phase calculations and descriptions:

```python
class MoonPhaseService:
    """Service for handling moon phase calculations and descriptions"""

    @staticmethod
    def get_moon_phase_name(moon_phase_percentage):
        """
        Converts moon phase percentage (0-100) to descriptive phase names.
        
        Returns both a short and detailed description of the phase.
        """
        if moon_phase_percentage is None:
            return {
                'short_name': 'Unknown',
                'description': 'Moon phase data not available'
            }
        
        # Normalize the percentage
        phase = moon_phase_percentage % 100
        
        # Define phase ranges and descriptions
        if phase == 0 or phase == 100:
            return {
                'short_name': 'New Moon',
                'description': 'The Moon is not visible from Earth'
            }
        elif 0 < phase <= 24:
            return {
                'short_name': 'Waxing Crescent',
                'description': 'Less than half of the Moon is illuminated and increasing'
            }
        # ... more phase definitions ...
```

### 3. Updated Model Implementation
**File**: `stars_app/models/viewinglocation.py`

Model now delegates to services:

```python
class ViewingLocation(TimestampedModel, LocationModel, RatableModel):
    # ... field definitions only ...
    
    # Simple delegation methods
    def get_moon_phase_name(self):
        """Get moon phase name and description"""
        return MoonPhaseService.get_moon_phase_name(self.moon_phase)

    def update_address_from_coordinates(self):
        """Updates address fields using Mapbox reverse geocoding"""
        return LocationService.update_address_from_coordinates(self)

    def calculate_quality_score(self):
        """Calculate overall quality score"""
        return LocationService.calculate_quality_score(self)

    def save(self, *args, **kwargs):
        try:
            is_new = not self.pk
            
            # First save to get the ID
            super().save(*args, **kwargs)
            
            # Delegate complex initialization to service
            if is_new or any(field in kwargs.get('update_fields', []) for field in ['latitude', 'longitude']):
                print(f"Updating data for location {self.name}")
                LocationService.initialize_location_data(self)
                
        except Exception as e:
            print(f"Error saving viewing location: {e}")
            raise
```

## Impact on Codebase

### Code Organization Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Model Length** | 400+ lines | 120 lines |
| **Business Logic Location** | Mixed in models | Dedicated services |
| **Testing Complexity** | Requires database | Can test logic independently |
| **Reusability** | Locked in models | Available to any part of app |
| **Maintenance** | Change models for business rules | Change services only |

### Testability Improvements

#### Before (Model-based testing)
```python
def test_moon_phase_calculation():
    # Required database setup
    location = ViewingLocation.objects.create(
        name="Test Location",
        latitude=40.0,
        longitude=-74.0,
        moon_phase=75.5
    )
    
    # Test coupled to database model
    result = location.get_moon_phase_name()
    assert result['short_name'] == 'Full Moon'
```

#### After (Service-based testing)
```python
def test_moon_phase_calculation():
    # Pure function testing - no database needed
    result = MoonPhaseService.get_moon_phase_name(75.5)
    assert result['short_name'] == 'Full Moon'
    
def test_moon_phase_edge_cases():
    # Easy to test edge cases
    assert MoonPhaseService.get_moon_phase_name(None)['short_name'] == 'Unknown'
    assert MoonPhaseService.get_moon_phase_name(0)['short_name'] == 'New Moon'
    assert MoonPhaseService.get_moon_phase_name(100)['short_name'] == 'New Moon'
    
def test_location_service_with_mock():
    # Can mock external API calls easily
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'features': []}
        
        location = Mock()
        result = LocationService.update_address_from_coordinates(location)
        assert result == False
```

### Reusability Benefits

#### Service Methods Can Be Used Anywhere
```python
# In views
def location_detail_view(request, location_id):
    location = get_object_or_404(ViewingLocation, id=location_id)
    
    # Can call service directly
    moon_info = MoonPhaseService.get_moon_phase_name(location.moon_phase)
    
    context = {
        'location': location,
        'moon_phase': moon_info
    }
    return render(request, 'location_detail.html', context)

# In API serializers
class LocationSerializer(serializers.ModelSerializer):
    moon_phase_name = serializers.SerializerMethodField()
    
    def get_moon_phase_name(self, obj):
        return MoonPhaseService.get_moon_phase_name(obj.moon_phase)

# In management commands
class Command(BaseCommand):
    def handle(self, *args, **options):
        for location in ViewingLocation.objects.all():
            LocationService.calculate_quality_score(location)

# In Celery tasks
@app.task
def update_location_data(location_id):
    location = ViewingLocation.objects.get(id=location_id)
    LocationService.initialize_location_data(location)
```

## Service Design Patterns

### 1. Static Methods vs Instance Methods
We chose static methods because:
- Services are stateless
- No need to instantiate service objects
- Clear that methods don't modify service state
- Easy to call from anywhere

```python
# Static method pattern (what we use)
LocationService.calculate_quality_score(location)

# vs Instance method pattern
service = LocationService()
service.calculate_quality_score(location)
```

### 2. Service Coordination
```python
class LocationService:
    @staticmethod
    def initialize_location_data(location):
        """Coordinates multiple service calls"""
        # This method orchestrates multiple operations
        # Each operation is in its own method for clarity
        LocationService.update_address_from_coordinates(location)
        LocationService.update_elevation_from_mapbox(location)
        LocationService.update_light_pollution(location)
        LocationService.update_forecast(location)
        LocationService.calculate_quality_score(location)
```

### 3. Error Handling Strategy
```python
@staticmethod
def update_address_from_coordinates(location):
    try:
        # Complex operation
        return True
    except Exception as e:
        # Log error but don't crash
        print(f"Error updating address: {str(e)}")
        return False
```

**Benefits**:
- Services handle their own errors
- Models don't need complex error handling
- Operations can fail gracefully
- Easy to add logging/monitoring

## Performance Implications

### Before (Fat Models)
- All logic executed in model save()
- No control over which operations run
- Hard to optimize or cache
- Difficult to make operations asynchronous

### After (Service Layer)
- Can call specific services as needed
- Easy to add caching to service methods
- Can make service calls asynchronous
- Better control over external API calls

```python
# Can now optimize specific operations
@lru_cache(maxsize=1000)
def get_moon_phase_name(moon_phase_percentage):
    # Cached moon phase calculations
    
# Can make operations asynchronous
@celery.task
def update_location_data_async(location_id):
    location = ViewingLocation.objects.get(id=location_id)
    LocationService.initialize_location_data(location)
```

## Future Extensions

### Adding New Services
```python
# Easy to add new business logic
class WeatherService:
    @staticmethod
    def get_current_conditions(location):
        # Weather API integration
        
    @staticmethod
    def get_forecast(location, hours=24):
        # Forecast logic

class AstronomyService:
    @staticmethod
    def calculate_sunset_time(location, date):
        # Astronomical calculations
        
    @staticmethod
    def get_visible_planets(location, datetime):
        # Planet visibility calculations
```

### Service Composition
```python
class ObservationPlannerService:
    @staticmethod
    def create_observation_plan(location, date):
        # Compose multiple services
        weather = WeatherService.get_forecast(location)
        moon_phase = MoonPhaseService.get_moon_phase_name(location.moon_phase)
        planets = AstronomyService.get_visible_planets(location, date)
        
        return {
            'weather': weather,
            'moon': moon_phase,
            'planets': planets,
            'quality_score': location.quality_score
        }
```

## Best Practices

### When to Create a Service
Create a new service when:
- ✅ Logic is complex (>20 lines)
- ✅ Logic involves external APIs
- ✅ Logic might be reused elsewhere
- ✅ Logic has complex business rules
- ✅ Logic involves multiple steps/calculations

Don't create a service for:
- ❌ Simple field validation
- ❌ Basic data transformations
- ❌ Django model methods (save, clean, etc.)
- ❌ One-line operations

### Service Organization
```
services/
├── __init__.py
├── location_service.py      # ViewingLocation business logic
├── moon_phase_service.py    # Moon phase calculations  
├── weather_service.py       # Weather API integration
├── astronomy_service.py     # Astronomical calculations
└── notification_service.py  # Email/notification logic
```

### Testing Strategy
```python
# Test services independently
class TestLocationService(TestCase):
    def test_calculate_quality_score(self):
        # Test with mock location object
        
# Test model integration
class TestViewingLocationModel(TestCase):
    def test_save_calls_location_service(self):
        # Test that model delegates correctly
```

## Migration Guide

If you need to add new business logic:

1. **Don't add it to models** - Create a service instead
2. **Make service methods static** - Unless you need state
3. **Handle errors gracefully** - Return success/failure indicators
4. **Add tests for services** - Much easier than testing models
5. **Keep models thin** - Only data and simple delegation methods

This service layer architecture provides a solid foundation for maintainable, testable, and reusable business logic.