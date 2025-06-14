# Location Categories and Tags System

## Overview
This document details the implementation of a comprehensive categorization system for viewing locations. The system uses pre-defined categories for consistent classification and user-generated tags for flexible, community-driven organization.

## Why Categories and Tags Were Needed

### Previous State
- No way to classify location types
- Difficult to find specific kinds of locations
- No community-driven organization
- Limited search capabilities
- No standardized location types

### Problems Solved
- **Discovery**: Users couldn't find specific location types
- **Organization**: No systematic way to group locations
- **Flexibility**: Fixed categories too limiting
- **Search**: No tag-based discovery
- **Community Input**: No way for users to add classifications

## Implementation Details

### Two-Tier System Design

#### 1. LocationCategory (Pre-defined)
```python
class LocationCategory(models.Model):
    """Pre-defined categories for viewing locations"""
    CATEGORY_CHOICES = [
        ('PARK', 'National/State Park'),
        ('MOUNTAIN', 'Mountain/Peak'),
        ('DESERT', 'Desert'),
        ('BEACH', 'Beach/Coast'),
        ('OBSERVATORY', 'Observatory'),
        ('RURAL', 'Rural Area'),
        ('SUBURBAN', 'Suburban Area'),
        ('CAMPGROUND', 'Campground'),
        ('FIELD', 'Open Field'),
        ('LAKE', 'Lake/Reservoir'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
```

#### 2. LocationTag (User-generated)
```python
class LocationTag(TimestampedModel):
    """User-generated tags for viewing locations"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)
```

### Default Categories Migration

```python
def populate_default_categories(apps, schema_editor):
    LocationCategory = apps.get_model('stars_app', 'LocationCategory')
    
    default_categories = [
        {'name': 'National/State Park', 'category_type': 'PARK', 'icon': '🏞️'},
        {'name': 'Mountain/Peak', 'category_type': 'MOUNTAIN', 'icon': '⛰️'},
        {'name': 'Desert', 'category_type': 'DESERT', 'icon': '🏜️'},
        {'name': 'Beach/Coast', 'category_type': 'BEACH', 'icon': '🏖️'},
        {'name': 'Observatory', 'category_type': 'OBSERVATORY', 'icon': '🔭'},
        # ... more categories
    ]
    
    for cat_data in default_categories:
        LocationCategory.objects.create(
            name=cat_data['name'],
            slug=slugify(cat_data['name']),
            category_type=cat_data['category_type'],
            icon=cat_data['icon'],
            description=f"Viewing locations in {cat_data['name'].lower()}"
        )
```

### ViewingLocation Integration

```python
class ViewingLocation(ViewingLocationBase):
    # ... other fields ...
    
    # Categories and Tags
    categories = models.ManyToManyField(
        'LocationCategory',
        blank=True,
        related_name='locations',
        help_text="Categories this location belongs to"
    )
    tags = models.ManyToManyField(
        'LocationTag',
        blank=True,
        related_name='locations',
        help_text="Tags associated with this location"
    )
```

### Filtering Implementation

```python
# Single category filter
category = django_filters.CharFilter(field_name='categories__slug', lookup_expr='exact')

# Multiple categories filter
def filter_categories(self, queryset, name, value):
    """Filter by multiple categories (comma-separated slugs)"""
    category_slugs = [slug.strip() for slug in value.split(',')]
    return queryset.filter(categories__slug__in=category_slugs).distinct()
```

## Usage Examples

### Filter by Category
```bash
# Get all mountain locations
GET /api/v1/locations/?category=mountain-peak

# Get locations that are both mountain AND observatory
GET /api/v1/locations/?categories=mountain-peak,observatory
```

### Filter by Tags
```bash
# Get locations tagged with "milky-way"
GET /api/v1/locations/?tag=milky-way

# Get locations with multiple tags
GET /api/v1/locations/?tags=beginner-friendly,wheelchair-accessible
```

### Location Data with Categories/Tags
```json
{
    "id": 123,
    "name": "Mount Wilson Observatory",
    "categories": [
        {
            "id": 2,
            "name": "Mountain/Peak",
            "slug": "mountain-peak",
            "category_type": "MOUNTAIN",
            "icon": "⛰️",
            "location_count": 45
        },
        {
            "id": 5,
            "name": "Observatory",
            "slug": "observatory",
            "category_type": "OBSERVATORY",
            "icon": "🔭",
            "location_count": 12
        }
    ],
    "tags": [
        {
            "id": 15,
            "name": "Historic Site",
            "slug": "historic-site",
            "created_by": "admin",
            "usage_count": 23,
            "is_approved": true
        },
        {
            "id": 27,
            "name": "Guided Tours",
            "slug": "guided-tours",
            "created_by": "user123",
            "usage_count": 8,
            "is_approved": true
        }
    ]
}
```

## Category Reference

| Category | Icon | Description | Typical Features |
|----------|------|-------------|------------------|
| National/State Park | 🏞️ | Protected natural areas | Dark skies, facilities, regulations |
| Mountain/Peak | ⛰️ | Elevated locations | High altitude, clear air, access challenges |
| Desert | 🏜️ | Arid regions | Low humidity, minimal light pollution |
| Beach/Coast | 🏖️ | Coastal areas | Ocean views, weather considerations |
| Observatory | 🔭 | Professional/public observatories | Equipment, programs, tours |
| Rural Area | 🌾 | Countryside locations | Low population, dark skies |
| Suburban Area | 🏘️ | Near populated areas | Accessible, some light pollution |
| Campground | 🏕️ | Camping facilities | Overnight stays, amenities |
| Open Field | 🌿 | Clear open spaces | 360° views, easy setup |
| Lake/Reservoir | 🏞️ | Water bodies | Stable air, reflections |

## Tag Management

### User Tag Creation
```python
# When users add tags to locations
def add_tag_to_location(location, tag_name, user):
    tag, created = LocationTag.objects.get_or_create(
        name=tag_name,
        defaults={
            'slug': slugify(tag_name),
            'created_by': user
        }
    )
    location.tags.add(tag)
    tag.update_usage_count()
```

### Tag Usage Tracking
```python
def update_usage_count(self):
    """Update the usage count based on actual usage"""
    self.usage_count = ViewingLocation.objects.filter(tags=self).count()
    self.save()
```

### Popular Tags
```bash
# Get most used tags
GET /api/v1/tags/?ordering=-usage_count&is_approved=true
```

## Benefits

### For Users
- Find locations by type quickly
- Discover similar locations
- Add community tags
- Filter searches effectively

### For Organization
- Consistent categorization
- Flexible tagging system
- Community-driven metadata
- Improved discoverability

### For Search
- Multi-criteria filtering
- Tag-based discovery
- Category combinations
- Related location finding

## Moderation Workflow

### Tag Approval Process
1. User creates new tag
2. Tag marked as `is_approved=False`
3. Tag visible to creator only
4. Admin reviews and approves
5. Tag becomes publicly visible

### Benefits of Moderation
- Prevent spam tags
- Ensure consistent naming
- Merge duplicate tags
- Maintain quality

## Future Enhancements

1. **Tag Suggestions**: Auto-suggest tags based on content
2. **Tag Synonyms**: Handle variations (e.g., "beginner" = "beginner-friendly")
3. **Tag Hierarchies**: Parent-child tag relationships
4. **Category Icons**: Custom SVG icons for better visualization
5. **Tag Clouds**: Visual representation of popular tags
6. **Smart Tagging**: AI-based automatic tagging
7. **Tag Subscriptions**: Follow specific tags for updates
8. **Category Stats**: Analytics per category

## Integration with Other Features

- **Search**: Categories and tags in search filters
- **Map Display**: Category icons on map markers
- **User Profiles**: Show user's favorite categories
- **Recommendations**: Suggest locations based on tag preferences
- **Export**: Include categories/tags in data exports