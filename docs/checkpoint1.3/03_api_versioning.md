# API Versioning Implementation

## Overview
This document details the implementation of API versioning for the Event Horizon astronomy application. Versioning enables backwards-compatible API evolution and ensures existing clients continue to work when new features are added.

## Why API Versioning Was Needed

### Previous State
- No versioning strategy in place
- API changes could break existing clients
- No clear upgrade path for API consumers
- Difficult to introduce breaking changes safely

### Problems Solved
- **Breaking Changes**: New features can be added without breaking existing clients
- **Client Compatibility**: Multiple API versions can coexist
- **Gradual Migration**: Clients can upgrade at their own pace
- **Clear Communication**: Version numbers indicate API capabilities
- **Future-Proofing**: Foundation for long-term API evolution

## Implementation Details

### 1. Versioning Strategy Selection

#### Chosen Approach: Namespace Versioning
```python
# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'VERSION_PARAM': 'version',
}
```

**Why Namespace Versioning:**
- **URL Clarity**: Version is explicit in the URL path
- **Easy Routing**: Django URL patterns handle versioning naturally
- **Client-Friendly**: Simple for clients to understand and use
- **Documentation**: Clear separation in API documentation

#### Alternative Approaches Considered

**Header Versioning**
```python
# Not chosen - hidden from URL
'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning'
# Usage: Accept: application/json; version=v1
```

**Query Parameter Versioning**
```python
# Not chosen - clutters URLs
'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.QueryParameterVersioning'
# Usage: /api/locations/?version=v1
```

**Host Versioning**
```python
# Not chosen - requires subdomain setup
'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.HostNameVersioning'
# Usage: v1.api.eventhorizon.com
```

### 2. URL Structure Implementation

#### URL Configuration
```python
# stars_app/urls.py
urlpatterns = [
    # Versioned API endpoints
    path('api/v1/', include(router.urls)),
    path('api/v1/', include(locations_router.urls)),
    path('api/v1/', include(reviews_router.urls)),
    
    # Non-versioned endpoints (legacy)
    path('', views.home, name='home'),
    path('map/', views.map, name='map'),
    # ... other views
]
```

#### Main Project URLs
```python
# django_project/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('stars_app.urls')),
    
    # Versioned API Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### 3. Generated API Endpoints

#### Core Endpoints (v1)
```
# Viewing Locations
GET    /api/v1/viewing-locations/
POST   /api/v1/viewing-locations/
GET    /api/v1/viewing-locations/{id}/
PUT    /api/v1/viewing-locations/{id}/
PATCH  /api/v1/viewing-locations/{id}/
DELETE /api/v1/viewing-locations/{id}/

# Custom Actions
POST   /api/v1/viewing-locations/{id}/favorite/
POST   /api/v1/viewing-locations/{id}/unfavorite/
POST   /api/v1/viewing-locations/{id}/update-elevation/
POST   /api/v1/viewing-locations/{id}/add-review/

# Celestial Events
GET    /api/v1/celestial-events/
POST   /api/v1/celestial-events/
GET    /api/v1/celestial-events/{id}/
PUT    /api/v1/celestial-events/{id}/
DELETE /api/v1/celestial-events/{id}/

# User Management
GET    /api/v1/users/
GET    /api/v1/users/{id}/
GET    /api/v1/user-profiles/
POST   /api/v1/user-profiles/
PUT    /api/v1/user-profiles/{id}/

# Favorites and Reviews
GET    /api/v1/favorite-locations/
POST   /api/v1/favorite-locations/
GET    /api/v1/review-votes/
POST   /api/v1/review-votes/

# Forecasts
GET    /api/v1/forecasts/
GET    /api/v1/forecasts/{id}/
```

#### Nested Endpoints (v1)
```
# Location Reviews
GET    /api/v1/viewing-locations/{id}/reviews/
POST   /api/v1/viewing-locations/{id}/reviews/
GET    /api/v1/viewing-locations/{id}/reviews/{review_id}/
PUT    /api/v1/viewing-locations/{id}/reviews/{review_id}/
DELETE /api/v1/viewing-locations/{id}/reviews/{review_id}/

# Review Comments  
GET    /api/v1/viewing-locations/{id}/reviews/{review_id}/comments/
POST   /api/v1/viewing-locations/{id}/reviews/{review_id}/comments/
DELETE /api/v1/viewing-locations/{id}/reviews/{review_id}/comments/{comment_id}/
```

#### Documentation Endpoints (v1)
```
GET    /api/v1/docs/     # Interactive Swagger UI
GET    /api/v1/redoc/    # Alternative documentation
GET    /api/v1/schema/   # OpenAPI schema JSON
```

### 4. Version Detection in Views

#### Accessing Version Information
```python
class ViewingLocationViewSet(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        # Access the requested version
        version = request.version
        print(f"API version requested: {version}")
        
        # Version-specific logic (for future versions)
        if version == 'v1':
            # v1 behavior
            pass
        elif version == 'v2':
            # v2 behavior (future)
            pass
            
        return super().list(request, *args, **kwargs)
```

#### Version-Specific Serializers (Future Use)
```python
def get_serializer_class(self):
    if self.request.version == 'v1':
        return ViewingLocationSerializerV1
    elif self.request.version == 'v2':
        return ViewingLocationSerializerV2
    return super().get_serializer_class()
```

### 5. Documentation Versioning

#### Spectacular Configuration
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Event Horizon API',
    'VERSION': '1.0.0',
    'DESCRIPTION': '''
Event Horizon API v1 provides access to astronomical viewing locations,
celestial events, reviews, and environmental data.

## Versioning
This API uses URL path versioning. All endpoints are prefixed with `/api/v1/`.

## Authentication
Most endpoints require authentication using session or token authentication.
    ''',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Event Horizon Team',
        'email': 'eventhorizonnotifications@gmail.com',
    },
    'TAGS': [
        {
            'name': 'Viewing Locations',
            'description': 'Manage astronomical viewing locations (v1)',
        },
        {
            'name': 'Celestial Events', 
            'description': 'Access celestial event data (v1)',
        },
    ],
}
```

## Client Usage Examples

### 1. JavaScript/Web Clients
```javascript
// Base API configuration
const API_BASE = 'http://localhost:8000/api/v1/';

// Fetch viewing locations
async function getViewingLocations() {
    const response = await fetch(`${API_BASE}viewing-locations/`);
    return response.json();
}

// Create new location
async function createLocation(locationData) {
    const response = await fetch(`${API_BASE}viewing-locations/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(locationData)
    });
    return response.json();
}
```

### 2. Mobile App Clients
```swift
// iOS Swift example
struct APIClient {
    private let baseURL = "https://api.eventhorizon.com/api/v1/"
    
    func fetchViewingLocations() async throws -> [ViewingLocation] {
        let url = URL(string: "\(baseURL)viewing-locations/")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ViewingLocationResponse.self, from: data).results
    }
}
```

### 3. Python Clients
```python
import requests

class EventHorizonAPI:
    def __init__(self, base_url="http://localhost:8000/api/v1/"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_viewing_locations(self, page=1, page_size=20):
        response = self.session.get(
            f"{self.base_url}viewing-locations/",
            params={'page': page, 'page_size': page_size}
        )
        return response.json()
    
    def create_review(self, location_id, rating, comment):
        response = self.session.post(
            f"{self.base_url}viewing-locations/{location_id}/reviews/",
            json={'rating': rating, 'comment': comment}
        )
        return response.json()
```

### 4. cURL Examples
```bash
# Get viewing locations
curl -H "Accept: application/json" \
     http://localhost:8000/api/v1/viewing-locations/

# Create new location (with auth)
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Token your_token_here" \
     -d '{"name": "New Observatory", "latitude": 40.7128, "longitude": -74.0060}' \
     http://localhost:8000/api/v1/viewing-locations/

# Search and filter
curl "http://localhost:8000/api/v1/viewing-locations/?search=observatory&quality_score__gte=80"
```

## Migration Strategy

### 1. Current State (v1 Only)
```
/api/v1/viewing-locations/  ✅ Available
/api/viewing-locations/     ❌ No longer available
```

### 2. Future v2 Migration Plan

#### Phase 1: Dual Support
```python
# URLs support both versions
urlpatterns = [
    path('api/v1/', include(router_v1.urls)),
    path('api/v2/', include(router_v2.urls)),  # New version
]

# Settings allow both versions
'ALLOWED_VERSIONS': ['v1', 'v2']
'DEFAULT_VERSION': 'v2'  # New clients get v2 by default
```

#### Phase 2: Version-Specific Features
```python
class ViewingLocationViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.request.version == 'v1':
            return ViewingLocationSerializerV1
        elif self.request.version == 'v2':
            return ViewingLocationSerializerV2  # Enhanced features
        return super().get_serializer_class()
```

#### Phase 3: v1 Deprecation
```python
# Add deprecation warnings
if request.version == 'v1':
    response = super().list(request, *args, **kwargs)
    response['X-API-Deprecation-Warning'] = 'API v1 is deprecated. Please migrate to v2.'
    return response
```

#### Phase 4: v1 Removal
```python
# Remove v1 support
'ALLOWED_VERSIONS': ['v2', 'v3']  # v1 no longer supported
```

## Version Change Examples

### Backwards Compatible Changes (Same Version)
```python
# ✅ Adding optional fields
class ViewingLocationSerializer(serializers.ModelSerializer):
    # New optional field - won't break existing clients
    weather_quality = serializers.FloatField(required=False)

# ✅ Adding new endpoints
# /api/v1/celestial-events/{id}/visibility/ (new action)

# ✅ Adding query parameters
# ?include_weather=true (optional parameter)
```

### Breaking Changes (New Version Required)
```python
# ❌ Removing required fields - needs v2
# ❌ Changing response format - needs v2  
# ❌ Changing authentication - needs v2

# Example v2 changes:
class ViewingLocationSerializerV2(serializers.ModelSerializer):
    # Breaking change: coordinates now in nested object
    coordinates = serializers.SerializerMethodField()
    
    def get_coordinates(self, obj):
        return {
            'latitude': obj.latitude,
            'longitude': obj.longitude,
            'elevation': obj.elevation
        }
    
    class Meta:
        model = ViewingLocation
        fields = ['id', 'name', 'coordinates', ...]  # latitude/longitude removed
```

## Testing Versioning

### 1. Unit Tests
```python
def test_v1_api_response():
    response = client.get('/api/v1/viewing-locations/')
    assert response.status_code == 200
    assert 'results' in response.json()

def test_version_detection():
    response = client.get('/api/v1/viewing-locations/')
    # Check that v1 format is returned
    data = response.json()['results'][0]
    assert 'latitude' in data  # v1 format
    assert 'coordinates' not in data  # v2 format
```

### 2. Integration Tests
```python
def test_api_documentation_versioning():
    # v1 documentation
    response = client.get('/api/v1/docs/')
    assert response.status_code == 200
    
    # Schema includes version info
    schema_response = client.get('/api/v1/schema/')
    schema = schema_response.json()
    assert schema['info']['version'] == '1.0.0'
```

### 3. Client Compatibility Tests
```python
def test_client_backwards_compatibility():
    # Test that v1 clients still work after v2 is added
    
    # Old client code (should still work)
    response = requests.get('http://localhost:8000/api/v1/viewing-locations/')
    data = response.json()
    
    # Verify v1 response format unchanged
    assert 'latitude' in data['results'][0]
    assert 'longitude' in data['results'][0]
```

## Performance Considerations

### 1. Version Detection Overhead
```python
# Minimal overhead - version parsed once per request
class VersioningMixin:
    @cached_property
    def version(self):
        return self.versioning_scheme.determine_version(self.request)
```

### 2. Multiple Version Support
```python
# Efficient serializer selection
_serializer_cache = {
    'v1': ViewingLocationSerializerV1,
    'v2': ViewingLocationSerializerV2,
}

def get_serializer_class(self):
    return _serializer_cache.get(self.request.version, self.serializer_class)
```

### 3. Documentation Generation
```python
# Separate schema generation per version
SPECTACULAR_SETTINGS = {
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]+/',  # Auto-detect version
    'VERSION': lambda request: request.version,
}
```

## Benefits Achieved

### 1. Client Stability
- Existing API clients continue working
- No surprise breaking changes
- Predictable upgrade paths

### 2. Development Flexibility
- New features can be added safely
- Breaking changes possible with new versions
- Clear communication of capabilities

### 3. Professional API
- Industry-standard versioning approach
- Clear documentation for each version
- Proper client support

### 4. Future-Proofing
- Foundation for long-term API evolution
- Ability to deprecate old versions gracefully
- Support for multiple client generations

## Monitoring and Analytics

### 1. Version Usage Tracking
```python
# Custom middleware to track version usage
class APIVersionTrackingMiddleware:
    def process_request(self, request):
        if request.path.startswith('/api/'):
            version = getattr(request, 'version', 'unknown')
            # Log version usage for analytics
            logger.info(f"API version {version} accessed", extra={
                'version': version,
                'endpoint': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT')
            })
```

### 2. Deprecation Warnings
```python
class DeprecatedVersionMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        if request.version == 'v1':
            response['X-API-Deprecation'] = 'true'
            response['X-API-Deprecation-Date'] = '2024-12-31'
            response['X-API-Sunset-Date'] = '2025-06-30'
            
        return response
```

## Troubleshooting

### Common Issues

1. **404 on API Endpoints**: Check version prefix in URL
2. **Incorrect Version Detection**: Verify URL patterns
3. **Documentation Not Loading**: Check versioned documentation URLs
4. **Client Compatibility**: Ensure clients use correct version

### Debug Commands
```bash
# Check URL patterns
python manage.py show_urls | grep api

# Test version detection
curl -I http://localhost:8000/api/v1/viewing-locations/

# Verify schema generation
python manage.py spectacular --file schema.yml
```

### Migration Checklist
- [ ] URL patterns include version prefix
- [ ] Documentation URLs are versioned
- [ ] Client applications updated to use versioned URLs
- [ ] Monitoring includes version tracking
- [ ] Deprecation plan documented

## Future Roadmap

### v2 Planning (Future)
- Enhanced coordinate system support
- Improved astronomical calculations
- Real-time event notifications
- Advanced filtering capabilities
- GraphQL support consideration

### v3 Considerations (Future)
- Hypermedia APIs (HATEOAS)
- Webhook support
- Real-time subscriptions
- Advanced analytics endpoints

---

**API Versioning Implementation Complete** ✅  
The foundation is now in place for stable, backwards-compatible API evolution with professional version management.