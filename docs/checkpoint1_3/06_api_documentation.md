# API Documentation Implementation

## Overview
This document details the implementation of comprehensive, interactive API documentation for the Event Horizon astronomy application using drf-spectacular (OpenAPI/Swagger). The documentation provides developers with clear, testable, and self-updating API references.

## Why API Documentation Was Needed

### Previous State
- No centralized API documentation
- Developers had to read source code to understand endpoints
- No way to test API endpoints interactively
- Poor developer onboarding experience
- Inconsistent documentation across different endpoints

### Problems Solved
- **Developer Experience**: Clear, interactive documentation improves API adoption
- **Self-Documentation**: Documentation automatically updates with code changes
- **Testing Interface**: Developers can test endpoints directly in the browser
- **Onboarding**: New developers can quickly understand and use the API
- **Professional Standard**: Industry-standard OpenAPI documentation format

## Implementation Details

### 1. Documentation Framework Setup

#### Dependencies and Installation
```python
# requirements.txt
drf-spectacular==0.27.0
pyyaml==6.0.1
uritemplate==4.1.1

# settings/base.py
INSTALLED_APPS = [
    # ... other apps
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # ... other settings
}
```

#### URL Configuration
```python
# django_project/urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ... other patterns
    
    # API Documentation endpoints
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### 2. Spectacular Configuration

#### Comprehensive Settings
```python
# settings/base.py
SPECTACULAR_SETTINGS = {
    'TITLE': 'Event Horizon API',
    'DESCRIPTION': '''
Event Horizon is an astronomical viewing location platform that helps stargazers 
find optimal locations for celestial observations. This API provides access to 
viewing locations, celestial events, reviews, and environmental data.

## Features
- **Viewing Locations**: Discover and manage optimal stargazing locations
- **Celestial Events**: Track meteors, eclipses, planets, auroras, and comets
- **Environmental Data**: Light pollution estimates, weather forecasts, moon conditions
- **Community Reviews**: User ratings and reviews for viewing locations
- **Real-time Data**: Live weather and astronomical conditions

## Authentication
Most endpoints require authentication. You can authenticate using:
- Session authentication (for web interface)
- Basic authentication (for API clients)

## Versioning
This API uses URL path versioning. All endpoints are prefixed with `/api/v1/`.

## Pagination
All list endpoints support pagination with configurable page sizes:
- Default page size: 20 items
- Maximum page size: 100 items
- Use `page` and `page_size` query parameters

## Filtering and Search
Most endpoints support filtering and search capabilities:
- Use `search` parameter for text-based searches
- Use field-specific filters (e.g., `quality_score__gte=80`)
- Use `ordering` parameter for sorting (e.g., `-quality_score`)
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    # Contact and License Information
    'CONTACT': {
        'name': 'Event Horizon Team',
        'email': 'eventhorizonnotifications@gmail.com',
    },
    'LICENSE': {
        'name': 'MIT License',
    },
    
    # Organization and Tagging
    'TAGS': [
        {
            'name': 'Viewing Locations',
            'description': 'Manage astronomical viewing locations with quality scores and environmental data',
        },
        {
            'name': 'Location Management',
            'description': 'Advanced location features including verification, clustering, and bulk operations',
        },
        {
            'name': 'Photos',
            'description': 'Upload and manage photos for viewing locations',
        },
        {
            'name': 'Categories & Tags',
            'description': 'Organize locations with categories and user-generated tags',
        },
        {
            'name': 'Community Moderation',
            'description': 'Report and moderate location content and issues',
        },
        {
            'name': 'User Reputation',
            'description': 'User contribution tracking and reputation scoring system',
        },
        {
            'name': 'Celestial Events',
            'description': 'Access information about astronomical events like meteors, eclipses, and planet visibility',
        },
        {
            'name': 'Reviews',
            'description': 'User reviews and ratings for viewing locations',
        },
        {
            'name': 'Comments',
            'description': 'Community comments and discussions on reviews',
        },
        {
            'name': 'User Management',
            'description': 'User profiles and authentication',
        },
        {
            'name': 'Favorites',
            'description': 'User favorite locations and personal collections',
        },
        {
            'name': 'Weather & Forecasts',
            'description': 'Weather data and astronomical forecasts',
        },
    ],
    
    # Schema Generation Options
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'ENUM_NAME_OVERRIDES': {
        'ValidationErrorEnum': 'drf_spectacular.plumbing.ValidationErrorEnum.choices',
    },
    
    # Response Examples
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'defaultModelRendering': 'example',
        'displayRequestDuration': True,
        'docExpansion': 'none',
        'filter': True,
        'operationsSorter': 'alpha',
        'showExtensions': True,
        'showCommonExtensions': True,
        'tagsSorter': 'alpha',
        'tryItOutEnabled': True,
    },
}
```

### 3. Enhanced ViewSet Documentation

#### Schema Decorators
```python
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        description="Retrieve a list of viewing locations with filtering and search capabilities",
        summary="List viewing locations",
        tags=["Viewing Locations"],
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in location name, address, or locality',
                examples=[
                    OpenApiExample(
                        'Observatory Search',
                        value='observatory',
                        description='Find locations with "observatory" in the name'
                    ),
                    OpenApiExample(
                        'City Search',
                        value='Los Angeles',
                        description='Find locations near Los Angeles'
                    ),
                ]
            ),
            OpenApiParameter(
                name='quality_score__gte',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Minimum quality score (0-100)',
                examples=[
                    OpenApiExample('High Quality', value=80),
                    OpenApiExample('Excellent Quality', value=90),
                ]
            ),
            OpenApiParameter(
                name='light_pollution_value__lte',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Maximum light pollution value (lower is better)',
                examples=[
                    OpenApiExample('Dark Sky', value=20.0),
                    OpenApiExample('Very Dark', value=15.0),
                ]
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Sort order. Prefix with "-" for descending.',
                enum=['-quality_score', 'quality_score', 'light_pollution_value', '-created_at'],
                examples=[
                    OpenApiExample('Best Quality First', value='-quality_score'),
                    OpenApiExample('Darkest Skies First', value='light_pollution_value'),
                ]
            ),
        ]
    ),
    create=extend_schema(
        description="Create a new viewing location",
        summary="Add viewing location",
        tags=["Viewing Locations"],
    ),
    retrieve=extend_schema(
        description="Get detailed information about a specific viewing location",
        summary="Get location details",
        tags=["Viewing Locations"],
    ),
    update=extend_schema(
        description="Update a viewing location's information",
        summary="Update location",
        tags=["Viewing Locations"],
    ),
    destroy=extend_schema(
        description="Delete a viewing location",
        summary="Delete location",
        tags=["Viewing Locations"],
    )
)
class ViewingLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing astronomical viewing locations.
    
    Viewing locations represent places suitable for astronomical observations,
    complete with quality scores, light pollution data, and environmental information.
    """
    # ... implementation
```

#### Custom Action Documentation
```python
@extend_schema(
    methods=['POST'],
    description="Add this location to the current user's favorites",
    summary="Favorite location",
    tags=["Viewing Locations", "Favorites"],
    request=None,  # No request body needed
    responses={
        200: ViewingLocationSerializer,
        400: OpenApiResponse(description="Location already favorited"),
    },
    examples=[
        OpenApiExample(
            'Success Response',
            value={
                "id": 1,
                "name": "Mount Wilson Observatory",
                "is_favorited": True,
                "favorite_count": 25
            },
            response_only=True,
        ),
    ]
)
@action(detail=True, methods=['POST'])
def favorite(self, request, pk=None):
    """Add location to user's favorites."""
    # ... implementation
```

### 4. Serializer Documentation Enhancement

#### Detailed Field Documentation
```python
class ViewingLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing locations with comprehensive astronomical data.
    """
    
    added_by = serializers.SerializerMethodField(
        help_text="User who added this location"
    )
    is_favorited = serializers.SerializerMethodField(
        help_text="Whether the current user has favorited this location"
    )
    reviews = LocationReviewSerializer(
        many=True, 
        read_only=True,
        help_text="User reviews for this location"
    )
    average_rating = serializers.SerializerMethodField(
        help_text="Average rating from all reviews (1-5 stars)"
    )
    moon_phase_info = serializers.SerializerMethodField(
        help_text="Current moon phase information"
    )

    class Meta:
        model = ViewingLocation
        fields = [
            'id', 'name', 'latitude', 'longitude', 'elevation',
            'formatted_address', 'administrative_area', 'locality', 'country',
            'light_pollution_value', 'quality_score', 'added_by',
            'created_at', 'is_favorited', 'cloudCoverPercentage', 'forecast',
            'reviews', 'average_rating', 'review_count', 'moon_phase_info'
        ]
        
        extra_kwargs = {
            'name': {
                'help_text': 'Descriptive name for the viewing location',
                'example': 'Mount Wilson Observatory'
            },
            'latitude': {
                'help_text': 'Latitude in decimal degrees (-90 to 90)',
                'example': 34.2258
            },
            'longitude': {
                'help_text': 'Longitude in decimal degrees (-180 to 180)',
                'example': -118.0581
            },
            'quality_score': {
                'help_text': 'Overall viewing quality score (0-100, higher is better)',
                'example': 85
            },
            'light_pollution_value': {
                'help_text': 'Light pollution measurement (lower is better for astronomy)',
                'example': 18.5
            },
        }
```

#### Response Examples
```python
from drf_spectacular.utils import OpenApiExample

@extend_schema(
    responses={
        200: ViewingLocationSerializer(many=True),
        400: OpenApiResponse(description="Invalid parameters"),
    },
    examples=[
        OpenApiExample(
            'Viewing Location List',
            value={
                "count": 150,
                "next": "http://localhost:8000/api/v1/viewing-locations/?page=2",
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "name": "Mount Wilson Observatory",
                        "latitude": 34.2258,
                        "longitude": -118.0581,
                        "elevation": 1742,
                        "quality_score": 95,
                        "light_pollution_value": 12.3,
                        "is_favorited": True,
                        "average_rating": 4.8,
                        "moon_phase_info": {
                            "percentage": 75.5,
                            "short_name": "Waxing Gibbous",
                            "description": "The moon is 75% illuminated and growing"
                        }
                    }
                ]
            },
            response_only=True,
        ),
    ]
)
def list(self, request, *args, **kwargs):
    return super().list(request, *args, **kwargs)
```

### 5. Error Response Documentation

#### Standardized Error Schemas
```python
from drf_spectacular.utils import OpenApiResponse

# Common error responses
COMMON_RESPONSES = {
    400: OpenApiResponse(
        description="Bad Request - Invalid input data",
        examples=[
            OpenApiExample(
                'Validation Error',
                value={
                    "rating": ["Rating must be between 1 and 5"],
                    "comment": ["This field may not be blank"]
                }
            ),
        ]
    ),
    401: OpenApiResponse(
        description="Unauthorized - Authentication required",
        examples=[
            OpenApiExample(
                'Not Authenticated',
                value={"detail": "Authentication credentials were not provided."}
            ),
        ]
    ),
    403: OpenApiResponse(
        description="Forbidden - Insufficient permissions",
        examples=[
            OpenApiExample(
                'Permission Denied',
                value={"detail": "You do not have permission to perform this action."}
            ),
        ]
    ),
    404: OpenApiResponse(
        description="Not Found - Resource does not exist",
        examples=[
            OpenApiExample(
                'Not Found',
                value={"detail": "Not found."}
            ),
        ]
    ),
}

# Apply to ViewSets
@extend_schema_view(
    create=extend_schema(responses={**COMMON_RESPONSES, 201: ViewingLocationSerializer}),
    update=extend_schema(responses={**COMMON_RESPONSES, 200: ViewingLocationSerializer}),
    destroy=extend_schema(responses={**COMMON_RESPONSES, 204: None}),
)
class ViewingLocationViewSet(viewsets.ModelViewSet):
    # ... implementation
```

### 6. Generated Documentation Structure

#### Available Documentation Endpoints
```
GET /api/v1/docs/      # Interactive Swagger UI
GET /api/v1/redoc/     # Alternative ReDoc interface
GET /api/v1/schema/    # Raw OpenAPI schema (JSON)
```

#### Interactive Features in Swagger UI

**Authentication Testing:**
- Built-in authentication forms
- Session-based authentication support
- Token authentication support
- Persistent authorization across requests

**Request Testing:**
- Interactive parameter forms
- Request body editors with validation
- Real API calls from the documentation
- Response inspection and formatting

**Schema Exploration:**
- Expandable/collapsible sections
- Model schema definitions
- Field-level documentation
- Example values and descriptions

### 7. Client Code Generation

#### OpenAPI Schema Export
```bash
# Generate schema file
python manage.py spectacular --file api_schema.yaml

# Generate in different formats
python manage.py spectacular --format openapi-json --file api_schema.json
```

#### Client Generation Examples
```bash
# Generate Python client
openapi-generator-cli generate \
    -i api_schema.yaml \
    -g python \
    -o ./python-client \
    --package-name event_horizon_client

# Generate JavaScript client
openapi-generator-cli generate \
    -i api_schema.yaml \
    -g javascript \
    -o ./js-client

# Generate Swift client
openapi-generator-cli generate \
    -i api_schema.yaml \
    -g swift5 \
    -o ./swift-client
```

#### Generated Client Usage
```python
# Generated Python client example
import event_horizon_client
from event_horizon_client.rest import ApiException

configuration = event_horizon_client.Configuration(
    host="http://localhost:8000"
)

with event_horizon_client.ApiClient(configuration) as api_client:
    api_instance = event_horizon_client.ViewingLocationsApi(api_client)
    
    try:
        # List viewing locations
        api_response = api_instance.viewing_locations_list(
            search="observatory",
            quality_score_gte=80,
            ordering="-quality_score"
        )
        print(f"Found {api_response.count} locations")
        
        for location in api_response.results:
            print(f"{location.name}: Quality {location.quality_score}")
            
    except ApiException as e:
        print(f"Exception: {e}")
```

### 8. Documentation Maintenance

#### Automated Updates
```python
# Documentation automatically updates when:
# 1. Model fields change
# 2. Serializer fields are modified
# 3. ViewSet methods are updated
# 4. URL patterns change

# No manual documentation updates needed!
```

#### Version-Specific Documentation
```python
# Future: Different documentation per API version
SPECTACULAR_SETTINGS = {
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]+/',
    'VERSION': '1.0.0',  # Will be 2.0.0 for v2 API
}
```

### 9. Performance Considerations

#### Schema Generation Optimization
```python
# Cache schema generation in production
SPECTACULAR_SETTINGS = {
    'SERVE_INCLUDE_SCHEMA': False,  # Don't serve schema in production
    'SCHEMA_CACHE_TIMEOUT': 3600,   # Cache schema for 1 hour
}

# Generate static schema files for production
# python manage.py spectacular --file static/api_schema.yaml
```

#### Documentation Asset Optimization
```python
# settings/production.py
SPECTACULAR_SETTINGS = {
    'SWAGGER_UI_DIST': 'SIDECAR',  # Use local Swagger UI assets
    'REDOC_DIST': 'SIDECAR',       # Use local ReDoc assets
}
```

### 10. Testing Documentation

#### Schema Validation Tests
```python
from rest_framework.test import APITestCase
from drf_spectacular.openapi import AutoSchema

class DocumentationTestCase(APITestCase):
    def test_schema_generation(self):
        """Test that API schema generates without errors."""
        from django.urls import reverse
        
        schema_url = reverse('schema')
        response = self.client.get(schema_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('openapi', response.json())
        self.assertIn('info', response.json())
        self.assertIn('paths', response.json())
    
    def test_swagger_ui_loads(self):
        """Test that Swagger UI page loads correctly."""
        docs_url = reverse('swagger-ui')
        response = self.client.get(docs_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger-ui')
    
    def test_redoc_loads(self):
        """Test that ReDoc page loads correctly."""
        redoc_url = reverse('redoc')
        response = self.client.get(redoc_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'redoc')
    
    def test_endpoint_documentation(self):
        """Test that all endpoints are documented."""
        schema_url = reverse('schema')
        response = self.client.get(schema_url)
        schema = response.json()
        
        # Check that key endpoints are documented
        paths = schema['paths']
        self.assertIn('/api/v1/viewing-locations/', paths)
        self.assertIn('/api/v1/celestial-events/', paths)
        self.assertIn('/api/v1/user-profiles/', paths)
        
        # Check that operations are documented
        locations_path = paths['/api/v1/viewing-locations/']
        self.assertIn('get', locations_path)
        self.assertIn('post', locations_path)
```

#### Documentation Accuracy Tests
```python
def test_parameter_documentation(self):
    """Test that filter parameters are properly documented."""
    schema_url = reverse('schema')
    response = self.client.get(schema_url)
    schema = response.json()
    
    # Check viewing locations list endpoint
    list_operation = schema['paths']['/api/v1/viewing-locations/']['get']
    
    # Verify documented parameters match actual implementation
    parameter_names = [param['name'] for param in list_operation.get('parameters', [])]
    
    expected_params = ['search', 'quality_score__gte', 'ordering', 'page', 'page_size']
    for param in expected_params:
        self.assertIn(param, parameter_names)
```

### 11. Benefits Achieved

#### Developer Experience Benefits
- **Self-Service**: Developers can explore the API independently
- **Interactive Testing**: Test endpoints directly in the browser
- **Automatic Updates**: Documentation stays synchronized with code
- **Professional Standard**: Industry-standard OpenAPI format
- **Client Generation**: Automatic SDK generation for multiple languages

#### Maintenance Benefits
- **Zero Maintenance**: Documentation updates automatically
- **Consistency**: All endpoints follow the same documentation standards
- **Validation**: Schema validation ensures documentation accuracy
- **Version Control**: Documentation changes tracked with code changes

#### Adoption Benefits
- **Lower Barrier to Entry**: Easy for new developers to understand the API
- **Reduced Support**: Fewer questions about API usage
- **Better Integration**: Clear examples and schemas aid integration
- **Professional Image**: High-quality documentation builds trust

### 12. Documentation Examples

#### Complete Endpoint Documentation
```yaml
# Generated OpenAPI schema excerpt
/api/v1/viewing-locations/:
  get:
    operationId: viewing_locations_list
    description: Retrieve a list of viewing locations with filtering and search capabilities
    summary: List viewing locations
    tags:
      - Viewing Locations
    parameters:
      - name: search
        in: query
        description: Search in location name, address, or locality
        required: false
        schema:
          type: string
        examples:
          Observatory Search:
            value: observatory
            description: Find locations with "observatory" in the name
      - name: quality_score__gte
        in: query
        description: Minimum quality score (0-100)
        required: false
        schema:
          type: integer
        examples:
          High Quality:
            value: 80
    responses:
      '200':
        description: Successful response
        content:
          application/json:
            schema:
              type: object
              properties:
                count:
                  type: integer
                next:
                  type: string
                  nullable: true
                previous:
                  type: string
                  nullable: true
                results:
                  type: array
                  items:
                    $ref: '#/components/schemas/ViewingLocation'
```

#### Model Schema Documentation
```yaml
# Generated model schema
components:
  schemas:
    ViewingLocation:
      type: object
      properties:
        id:
          type: integer
          readOnly: true
        name:
          type: string
          description: Descriptive name for the viewing location
          example: Mount Wilson Observatory
          maxLength: 200
        latitude:
          type: number
          format: double
          description: Latitude in decimal degrees (-90 to 90)
          example: 34.2258
        longitude:
          type: number
          format: double
          description: Longitude in decimal degrees (-180 to 180)
          example: -118.0581
        quality_score:
          type: integer
          description: Overall viewing quality score (0-100, higher is better)
          example: 85
          readOnly: true
      required:
        - name
        - latitude
        - longitude
```

## Future Enhancements

### Planned Improvements
1. **Interactive Tutorials**: Step-by-step API usage guides
2. **Code Examples**: Language-specific implementation examples
3. **Performance Metrics**: Response time documentation
4. **Webhook Documentation**: Event notification documentation
5. **SDK Documentation**: Generated client library documentation

### Advanced Features
```python
# Custom schema processors
def custom_preprocessing_hook(endpoints):
    """Add custom documentation enhancements."""
    for path, path_regex, method, callback in endpoints:
        # Add custom tags, descriptions, or examples
        pass
    return endpoints

SPECTACULAR_SETTINGS = {
    'PREPROCESSING_HOOKS': ['myapp.schema.custom_preprocessing_hook'],
}
```

## Troubleshooting

### Common Issues
1. **Schema Generation Errors**: Check for circular imports in serializers
2. **Missing Endpoints**: Verify ViewSets are properly registered
3. **Authentication Issues**: Ensure proper authentication configuration
4. **Performance Issues**: Consider schema caching for production

### Debug Tips
```python
# Generate schema manually for debugging
from drf_spectacular.openapi import AutoSchema
from django.urls import reverse

schema_generator = AutoSchema()
schema = schema_generator.get_schema(request=None, public=True)
print(schema)

# Check specific endpoint schemas
from drf_spectacular.utils import extend_schema_view
print(ViewingLocationViewSet.__dict__)
```

---

## Checkpoint 2.1 API Endpoints

### Location Management Endpoints

#### Bulk Import
```http
POST /api/v1/viewing-locations/bulk_import/
```
**Description**: Import multiple locations via CSV/JSON with validation and duplicate detection

**Authentication**: Required

**Parameters**:
- `format` (string): "csv" or "json"
- `dry_run` (boolean): Validate without saving
- `data` (array): Location data array
- `file` (file): CSV/JSON file upload

**Example Request**:
```json
{
  "format": "json",
  "dry_run": false,
  "data": [
    {
      "name": "Dark Sky Location",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "elevation": 100
    }
  ]
}
```

**Responses**:
- `200`: Import successful with results summary
- `400`: Validation errors or duplicate conflicts
- `401`: Authentication required

#### Clustered Locations
```http
GET /api/v1/viewing-locations/clustered/
```
**Description**: Get locations with clustering for map display based on zoom level and bounds

**Authentication**: None required

**Parameters**:
- `zoom` (integer): Map zoom level (1-20)
- `north` (float): Northern boundary
- `south` (float): Southern boundary  
- `east` (float): Eastern boundary
- `west` (float): Western boundary

**Example Request**:
```http
GET /api/v1/viewing-locations/clustered/?zoom=10&north=41&south=40&east=-73&west=-75
```

**Response Example**:
```json
{
  "clusters": [
    {
      "type": "cluster",
      "latitude": 40.5,
      "longitude": -74.0,
      "count": 15,
      "average_quality": 78.5,
      "has_verified": true
    },
    {
      "type": "location", 
      "id": 123,
      "name": "Individual Location",
      "latitude": 40.1,
      "longitude": -74.5,
      "quality_score": 95
    }
  ],
  "total_locations": 45,
  "zoom_level": 10
}
```

#### Duplicate Detection
```http
POST /api/v1/viewing-locations/check_duplicates/
```
**Description**: Check for duplicate locations within specified radius

**Authentication**: None required

**Parameters**:
- `latitude` (float): Location latitude
- `longitude` (float): Location longitude  
- `radius_km` (float): Search radius in kilometers (default: 0.5)

**Example Request**:
```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_km": 1.0
}
```

**Response Example**:
```json
{
  "duplicates": [
    {
      "id": 15,
      "name": "Similar Location",
      "distance_km": 0.3,
      "latitude": 40.7145,
      "longitude": -74.0070
    }
  ],
  "count": 1
}
```

### Photo Management Endpoints

#### Upload Photo
```http
POST /api/v1/viewing-locations/{id}/upload_photo/
```
**Description**: Upload a photo to a viewing location

**Authentication**: Required

**Parameters**:
- `image` (file): Image file
- `caption` (string): Optional photo caption
- `is_primary` (boolean): Set as primary photo

**Example Response**:
```json
{
  "id": 42,
  "image": "/media/location_photos/1/abc123.jpg",
  "caption": "Amazing Milky Way view",
  "is_primary": true,
  "is_approved": true,
  "uploaded_by": "photographer123",
  "uploaded_at": "2024-01-15T22:30:00Z"
}
```

#### Get Location Photos
```http
GET /api/v1/viewing-locations/{id}/photos/
```
**Description**: Get all photos for a location

**Authentication**: None required

**Response Example**:
```json
[
  {
    "id": 42,
    "image": "/media/location_photos/1/abc123.jpg",
    "caption": "Amazing Milky Way view",
    "is_primary": true,
    "uploaded_by": "photographer123",
    "uploaded_at": "2024-01-15T22:30:00Z"
  }
]
```

#### Set Primary Photo
```http
POST /api/v1/viewing-locations/{id}/set_primary_photo/
```
**Description**: Set a photo as the primary photo for a location

**Authentication**: Required

**Parameters**:
- `photo_id` (integer): ID of photo to set as primary

### Community Moderation Endpoints

#### Submit Report
```http
POST /api/v1/viewing-locations/{id}/report/
```
**Description**: Report issues with a location

**Authentication**: Required

**Parameters**:
- `report_type` (string): "DUPLICATE", "INACCURATE", "SPAM", "CLOSED", "DANGEROUS", "OTHER"
- `description` (string): Detailed description of the issue
- `duplicate_of_id` (integer): For DUPLICATE reports, ID of original location

**Example Request**:
```json
{
  "report_type": "INACCURATE",
  "description": "GPS coordinates are off by 2km. Actual location is further north."
}
```

**Response Example**:
```json
{
  "id": 15,
  "report_type": "INACCURATE", 
  "description": "GPS coordinates are off by 2km...",
  "location": 123,
  "reported_by": "username",
  "status": "PENDING",
  "submitted_at": "2024-01-15T22:30:00Z"
}
```

#### View Reports (Admin Only)
```http
GET /api/v1/viewing-locations/{id}/reports/
```
**Description**: View all reports for a location (admin users only)

**Authentication**: Required (Admin)

**Response Example**:
```json
[
  {
    "id": 15,
    "report_type": "INACCURATE",
    "description": "GPS coordinates are off...",
    "reported_by": "username",
    "status": "REVIEWED",
    "reviewed_by": "admin",
    "review_notes": "Confirmed and corrected",
    "reviewed_at": "2024-01-16T10:00:00Z"
  }
]
```

### User Reputation Endpoints

#### Get User Reputation
```http
GET /api/v1/users/{id}/
```
**Description**: Get user profile including reputation data

**Authentication**: None required (public read access)

**Response Example**:
```json
{
  "id": 123,
  "username": "stargazer",
  "profile": {
    "reputation_score": 150,
    "verified_locations_count": 5,
    "helpful_reviews_count": 8,
    "quality_photos_count": 12,
    "is_trusted_contributor": true
  }
}
```

### Enhanced Filtering Parameters

All `/api/v1/viewing-locations/` endpoints now support these additional filters:

#### Verification Filters
- `is_verified` (boolean): Show only verified locations
- `verified_only` (boolean): Alternative verified filter
- `times_reported__lte` (integer): Maximum number of reports
- `visitor_count__gte` (integer): Minimum visitor count

#### Category and Tag Filters  
- `category` (string): Single category slug
- `categories` (string): Comma-separated category slugs
- `tag` (string): Single tag slug
- `tags` (string): Comma-separated tag slugs

#### Geographic Filters
- `lat` + `lng` + `radius` (float): Radius search from coordinates
- Bounds filtering: `north`, `south`, `east`, `west`

#### Date Filters
- `recently_visited` (boolean): Visited in last 30 days
- `added_after` (date): Added after date
- `added_before` (date): Added before date

**Example Advanced Filter**:
```http
GET /api/v1/viewing-locations/?is_verified=true&min_quality_score=80&category=nationalstate-park&lat=40.7&lng=-74.0&radius=10
```

### Management Commands

#### Update User Reputation
```bash
# Update all users
python manage.py update_reputation

# Update specific user
python manage.py update_reputation --user username
```

### Error Responses

All new endpoints follow standard error response format:

**400 Bad Request**:
```json
{
  "detail": "Invalid report type",
  "field_errors": {
    "report_type": ["Select a valid choice"]
  }
}
```

**401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**:
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

**API Documentation Implementation Complete** ✅  
Professional, interactive, and automatically maintained API documentation is now available, providing excellent developer experience and reducing support overhead.