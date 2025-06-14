# Location Photo Upload System

## Overview
This document details the implementation of a comprehensive photo upload system for viewing locations. Users can upload photos of locations they've visited, helping others visualize the sites and verify their suitability for stargazing.

## Why Photo Uploads Were Needed

### Previous State
- No visual representation of locations
- Users relied only on text descriptions
- No way to verify location appearance
- Difficult to assess site conditions
- No community-contributed visual content

### Problems Solved
- **Visual Verification**: Users couldn't see what locations looked like
- **Site Assessment**: Hard to judge terrain, access, and facilities
- **Community Engagement**: No way for users to contribute visuals
- **Trust Building**: Text-only descriptions lacked credibility
- **Location Discovery**: Photos help users find exact spots

## Implementation Details

### LocationPhoto Model

```python
class LocationPhoto(TimestampedModel):
    """Photos uploaded for viewing locations"""
    location = models.ForeignKey(
        ViewingLocation,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_photos'
    )
    image = models.ImageField(
        upload_to=location_photo_path,
        help_text="Photo of the viewing location"
    )
    caption = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional caption for the photo"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo shown in location listings"
    )
    is_approved = models.BooleanField(
        default=True,  # Auto-approve for now
        help_text="Whether the photo has been approved by moderators"
    )
    
    # EXIF data (extracted from uploaded images)
    taken_at = models.DateTimeField(null=True, blank=True)
    camera_make = models.CharField(max_length=100, blank=True)
    camera_model = models.CharField(max_length=100, blank=True)
```

### Unique File Path Generation

```python
def location_photo_path(instance, filename):
    """Generate unique path for location photos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('location_photos', str(instance.location.id), filename)
```

This creates a structure like:
```
media/
  location_photos/
    123/  # Location ID
      a1b2c3d4.jpg
      e5f6g7h8.jpg
```

### Primary Photo Logic

```python
def save(self, *args, **kwargs):
    # Ensure only one primary photo per location
    if self.is_primary:
        LocationPhoto.objects.filter(
            location=self.location,
            is_primary=True
        ).exclude(pk=self.pk).update(is_primary=False)
    
    super().save(*args, **kwargs)
```

### API Endpoints

#### Upload Photo
```python
@action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
def upload_photo(self, request, pk=None):
    """Upload a photo for this location"""
    location = self.get_object()
    
    data = {
        'location': location.id,
        'image': request.FILES['image'],
        'caption': request.data.get('caption', ''),
        'is_primary': request.data.get('is_primary', False)
    }
    
    serializer = LocationPhotoSerializer(data=data)
    if serializer.is_valid():
        photo = serializer.save(uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

#### Get Location Photos
```python
@action(detail=True, methods=['GET'])
def photos(self, request, pk=None):
    """Get all photos for this location"""
    location = self.get_object()
    photos = location.photos.filter(is_approved=True)
    serializer = LocationPhotoSerializer(photos, many=True)
    return Response(serializer.data)
```

#### Set Primary Photo
```python
@action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
def set_primary_photo(self, request, pk=None):
    """Set a photo as the primary photo for this location"""
    # Only uploader or location owner can set primary
    if photo.uploaded_by != request.user and location.added_by != request.user:
        return Response({'detail': 'Permission denied'}, status=403)
```

## Usage Examples

### Upload a Photo
```bash
curl -X POST http://localhost:8000/api/v1/locations/123/upload_photo/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "image=@sunset_view.jpg" \
  -F "caption=Beautiful sunset view from the observation deck" \
  -F "is_primary=false"
```

### Get All Photos for a Location
```bash
GET /api/v1/locations/123/photos/
```

Response:
```json
[
    {
        "id": 1,
        "location": 123,
        "uploaded_by": "john_doe",
        "image_url": "/media/location_photos/123/a1b2c3d4.jpg",
        "caption": "Night sky view from the parking area",
        "is_primary": true,
        "is_approved": true,
        "taken_at": "2024-01-15T22:30:00Z",
        "camera_make": "Canon",
        "camera_model": "EOS R5",
        "created_at": "2024-01-16T10:00:00Z"
    }
]
```

### Set Primary Photo
```bash
curl -X POST http://localhost:8000/api/v1/locations/123/set_primary_photo/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"photo_id": 5}'
```

## Photo Display in Location Data

The ViewingLocationSerializer includes:
```python
photos = LocationPhotoSerializer(many=True, read_only=True)
primary_photo = serializers.SerializerMethodField()

def get_primary_photo(self, obj):
    primary = obj.photos.filter(is_primary=True, is_approved=True).first()
    if primary:
        return LocationPhotoSerializer(primary).data
    # If no primary, get the first approved photo
    first_photo = obj.photos.filter(is_approved=True).first()
    if first_photo:
        return LocationPhotoSerializer(first_photo).data
    return None
```

## Security Considerations

### File Validation
- Image file type checking
- File size limits (configured in settings)
- Malware scanning (future enhancement)

### Access Control
- Only authenticated users can upload
- Only uploader or location owner can set primary
- Approval workflow for moderation

### Storage Security
- Unique filenames prevent guessing
- Organized by location ID
- CDN-ready structure

## Benefits

### For Users
- Visual preview of locations
- Better location selection
- Community photo sharing
- Verification through photos

### For Location Quality
- Visual verification of conditions
- Multiple perspectives from visitors
- Seasonal variation documentation
- Access route visualization

### For Engagement
- Users contribute content
- Increased time on platform
- Social sharing opportunities
- Photography community building

## Future Enhancements

1. **EXIF Data Extraction**: Automatic extraction of camera settings and timestamp
2. **Image Processing**: Automatic resizing and optimization
3. **Moderation Queue**: Admin interface for photo approval
4. **AI Tagging**: Automatic detection of photo content
5. **360° Photos**: Support for panoramic images
6. **Photo Contests**: Community engagement through competitions
7. **Watermarking**: Optional watermarks for photographers
8. **Gallery Views**: Advanced photo browsing interfaces

## Integration with Other Features

- **User Reputation**: Quality photos contribute to reputation score
- **Location Verification**: Photos help verify location accuracy
- **Search Results**: Primary photos shown in search results
- **Map Popups**: Thumbnail photos in map markers
- **Social Sharing**: Photos used in social media previews