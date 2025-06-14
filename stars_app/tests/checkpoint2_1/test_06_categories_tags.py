"""
Test Suite for Location Categories and Tags System
=================================================

This test module validates the categorization system including:
- Pre-defined location categories with icons
- User-generated tags with approval workflow
- Many-to-many relationships for categories and tags
- Filtering by categories and tags
- Tag usage counting and popularity
- Category default data population

How to run these tests:
----------------------
# Run all category/tag tests:
python manage.py test stars_app.tests.checkpoint2.1.test_06_categories_tags

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_06_categories_tags.CategoryTest

# Run with specific test method:
python manage.py test stars_app.tests.checkpoint2.1.test_06_categories_tags.CategoryTest.test_default_categories_exist

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_06_categories_tags
coverage report

Test Categories:
---------------
1. CategoryTest - Tests pre-defined category system
2. TagTest - Tests user-generated tag system
3. LocationCategoryAssignmentTest - Tests assigning categories to locations
4. LocationTagAssignmentTest - Tests assigning tags to locations
5. FilteringByCategoryTagTest - Tests search/filter functionality

Requirements:
------------
- Django test framework
- Default categories populated via migration
- Authenticated users for tag creation
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation, LocationCategory, LocationTag


class CategoryTest(TestCase):
    """Test pre-defined category system"""
    
    def test_default_categories_exist(self):
        """Test that default categories were created by migration"""
        # Check that categories exist
        categories = LocationCategory.objects.all()
        self.assertGreater(categories.count(), 0)
        
        # Check specific categories
        expected_types = ['PARK', 'MOUNTAIN', 'DESERT', 'BEACH', 'OBSERVATORY']
        for cat_type in expected_types:
            self.assertTrue(
                LocationCategory.objects.filter(category_type=cat_type).exists(),
                f"Category type {cat_type} should exist"
            )
            
    def test_category_properties(self):
        """Test category model properties"""
        mountain_cat = LocationCategory.objects.filter(category_type='MOUNTAIN').first()
        
        self.assertIsNotNone(mountain_cat)
        self.assertEqual(mountain_cat.name, 'Mountain/Peak')
        self.assertEqual(mountain_cat.slug, 'mountainpeak')
        self.assertEqual(mountain_cat.icon, '⛰️')
        self.assertIn('mountain', mountain_cat.description.lower())
        
    def test_category_uniqueness(self):
        """Test that category types are unique"""
        # Try to create duplicate category type
        existing_cat = LocationCategory.objects.first()
        
        with self.assertRaises(Exception):  # IntegrityError
            LocationCategory.objects.create(
                name='Duplicate',
                slug='duplicate',
                category_type=existing_cat.category_type  # Should fail
            )
            
    def test_category_icon_display(self):
        """Test that categories have appropriate icons"""
        categories = LocationCategory.objects.all()
        
        for category in categories:
            self.assertIsNotNone(category.icon)
            self.assertGreater(len(category.icon), 0)
            
    def test_category_ordering(self):
        """Test that categories are ordered by name"""
        categories = list(LocationCategory.objects.all().values_list('name', flat=True))
        sorted_categories = sorted(categories)
        
        self.assertEqual(categories, sorted_categories)


class TagTest(TestCase):
    """Test user-generated tag system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='tagcreator', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        
    def test_create_tag(self):
        """Test creating a new tag"""
        tag = LocationTag.objects.create(
            name='Beginner Friendly',
            slug='beginner-friendly',
            created_by=self.user
        )
        
        self.assertEqual(tag.name, 'Beginner Friendly')
        self.assertEqual(tag.slug, 'beginner-friendly')
        self.assertEqual(tag.created_by, self.user)
        self.assertEqual(tag.usage_count, 0)
        self.assertFalse(tag.is_approved)  # Default should be False
        
    def test_tag_slug_generation(self):
        """Test automatic slug generation from name"""
        tag_name = 'Wheelchair Accessible'
        expected_slug = slugify(tag_name)
        
        tag = LocationTag.objects.create(
            name=tag_name,
            slug=expected_slug,
            created_by=self.user
        )
        
        self.assertEqual(tag.slug, 'wheelchair-accessible')
        
    def test_tag_approval_workflow(self):
        """Test tag approval process"""
        tag = LocationTag.objects.create(
            name='New Tag',
            slug='new-tag',
            created_by=self.user,
            is_approved=False
        )
        
        # Initially not approved
        self.assertFalse(tag.is_approved)
        
        # Admin approves
        tag.is_approved = True
        tag.save()
        
        tag.refresh_from_db()
        self.assertTrue(tag.is_approved)
        
    def test_tag_usage_count_update(self):
        """Test usage count calculation"""
        tag = LocationTag.objects.create(
            name='Popular Tag',
            slug='popular-tag',
            created_by=self.user,
            is_approved=True
        )
        
        # Create locations and assign tag
        for i in range(3):
            location = ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            location.tags.add(tag)
            
        # Update usage count
        tag.update_usage_count()
        
        tag.refresh_from_db()
        self.assertEqual(tag.usage_count, 3)
        
    def test_tag_ordering_by_usage(self):
        """Test that tags are ordered by usage count descending"""
        # Create tags with different usage counts
        popular_tag = LocationTag.objects.create(
            name='Popular',
            slug='popular',
            usage_count=100
        )
        
        medium_tag = LocationTag.objects.create(
            name='Medium',
            slug='medium',
            usage_count=50
        )
        
        unpopular_tag = LocationTag.objects.create(
            name='Unpopular',
            slug='unpopular',
            usage_count=5
        )
        
        tags = list(LocationTag.objects.all())
        self.assertEqual(tags[0], popular_tag)
        self.assertEqual(tags[1], medium_tag)
        self.assertEqual(tags[2], unpopular_tag)


class LocationCategoryAssignmentTest(TestCase):
    """Test assigning categories to locations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Multi-category Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Get some categories
        self.mountain_cat = LocationCategory.objects.filter(category_type='MOUNTAIN').first()
        self.park_cat = LocationCategory.objects.filter(category_type='PARK').first()
        self.observatory_cat = LocationCategory.objects.filter(category_type='OBSERVATORY').first()
        
    def test_assign_single_category(self):
        """Test assigning a single category to location"""
        self.location.categories.add(self.mountain_cat)
        
        self.assertEqual(self.location.categories.count(), 1)
        self.assertIn(self.mountain_cat, self.location.categories.all())
        
    def test_assign_multiple_categories(self):
        """Test assigning multiple categories to location"""
        self.location.categories.add(self.mountain_cat, self.park_cat, self.observatory_cat)
        
        self.assertEqual(self.location.categories.count(), 3)
        
        category_types = list(self.location.categories.values_list('category_type', flat=True))
        self.assertIn('MOUNTAIN', category_types)
        self.assertIn('PARK', category_types)
        self.assertIn('OBSERVATORY', category_types)
        
    def test_category_relationship_from_category_side(self):
        """Test accessing locations from category"""
        # Assign category to multiple locations
        location2 = ViewingLocation.objects.create(
            name='Another Mountain Location',
            latitude=41.0,
            longitude=-106.0,
            added_by=self.user
        )
        
        self.location.categories.add(self.mountain_cat)
        location2.categories.add(self.mountain_cat)
        
        # Access locations through category
        mountain_locations = self.mountain_cat.locations.all()
        self.assertEqual(mountain_locations.count(), 2)
        
    def test_location_serializer_includes_categories(self):
        """Test that location API response includes categories"""
        self.location.categories.add(self.mountain_cat, self.park_cat)
        
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 2)
        
        # Check category structure
        category_slugs = [cat['slug'] for cat in data['categories']]
        self.assertIn('mountainpeak', category_slugs)
        self.assertIn('nationalstate-park', category_slugs)


class LocationTagAssignmentTest(TestCase):
    """Test assigning tags to locations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Tagged Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Create some tags
        self.beginner_tag = LocationTag.objects.create(
            name='Beginner Friendly',
            slug='beginner-friendly',
            created_by=self.user,
            is_approved=True
        )
        
        self.accessible_tag = LocationTag.objects.create(
            name='Wheelchair Accessible',
            slug='wheelchair-accessible',
            created_by=self.user,
            is_approved=True
        )
        
        self.unapproved_tag = LocationTag.objects.create(
            name='Unapproved Tag',
            slug='unapproved-tag',
            created_by=self.user,
            is_approved=False
        )
        
    def test_assign_approved_tags(self):
        """Test assigning approved tags to location"""
        self.location.tags.add(self.beginner_tag, self.accessible_tag)
        
        self.assertEqual(self.location.tags.count(), 2)
        self.assertIn(self.beginner_tag, self.location.tags.all())
        self.assertIn(self.accessible_tag, self.location.tags.all())
        
    def test_assign_unapproved_tag(self):
        """Test that unapproved tags can still be assigned"""
        self.location.tags.add(self.unapproved_tag)
        
        self.assertEqual(self.location.tags.count(), 1)
        self.assertIn(self.unapproved_tag, self.location.tags.all())
        
    def test_tag_usage_count_updates(self):
        """Test that tag usage count updates when assigned"""
        initial_count = self.beginner_tag.usage_count
        
        # Assign to multiple locations
        for i in range(3):
            loc = ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            loc.tags.add(self.beginner_tag)
            
        # Update usage count
        self.beginner_tag.update_usage_count()
        self.beginner_tag.refresh_from_db()
        
        self.assertEqual(self.beginner_tag.usage_count, initial_count + 3)
        
    def test_location_serializer_includes_tags(self):
        """Test that location API response includes tags"""
        self.location.tags.add(self.beginner_tag, self.accessible_tag)
        
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('tags', data)
        self.assertEqual(len(data['tags']), 2)
        
        # Check tag structure
        tag_slugs = [tag['slug'] for tag in data['tags']]
        self.assertIn('beginner-friendly', tag_slugs)
        self.assertIn('wheelchair-accessible', tag_slugs)
        
        # Check tag includes creator info
        for tag in data['tags']:
            self.assertIn('created_by', tag)
            self.assertIn('usage_count', tag)
            self.assertIn('is_approved', tag)


class FilteringByCategoryTagTest(TestCase):
    """Test search/filter functionality with categories and tags"""
    
    def setUp(self):
        """Set up test data with various category/tag combinations"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Get categories
        self.mountain_cat = LocationCategory.objects.filter(category_type='MOUNTAIN').first()
        self.park_cat = LocationCategory.objects.filter(category_type='PARK').first()
        self.observatory_cat = LocationCategory.objects.filter(category_type='OBSERVATORY').first()
        
        # Create tags
        self.beginner_tag = LocationTag.objects.create(
            name='Beginner',
            slug='beginner',
            is_approved=True
        )
        
        self.accessible_tag = LocationTag.objects.create(
            name='Accessible',
            slug='accessible',
            is_approved=True
        )
        
        # Create locations with different combinations
        self.mountain_park = ViewingLocation.objects.create(
            name='Mountain Park',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        self.mountain_park.categories.add(self.mountain_cat, self.park_cat)
        self.mountain_park.tags.add(self.beginner_tag)
        
        self.accessible_observatory = ViewingLocation.objects.create(
            name='Accessible Observatory',
            latitude=41.0,
            longitude=-106.0,
            added_by=self.user
        )
        self.accessible_observatory.categories.add(self.observatory_cat)
        self.accessible_observatory.tags.add(self.accessible_tag, self.beginner_tag)
        
        self.remote_mountain = ViewingLocation.objects.create(
            name='Remote Mountain',
            latitude=42.0,
            longitude=-107.0,
            added_by=self.user
        )
        self.remote_mountain.categories.add(self.mountain_cat)
        # No tags - not beginner friendly
        
    def test_filter_by_single_category(self):
        """Test filtering by single category slug"""
        response = self.client.get(f'/api/v1/viewing-locations/?category={self.mountain_cat.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)  # Mountain Park and Remote Mountain
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Mountain Park', names)
        self.assertIn('Remote Mountain', names)
        self.assertNotIn('Accessible Observatory', names)
        
    def test_filter_by_multiple_categories(self):
        """Test filtering by multiple categories (AND logic)"""
        response = self.client.get(
            f'/api/v1/viewing-locations/?categories={self.mountain_cat.slug},{self.park_cat.slug}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Only Mountain Park has both categories
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Mountain Park')
        
    def test_filter_by_single_tag(self):
        """Test filtering by single tag slug"""
        response = self.client.get('/api/v1/viewing-locations/?tag=accessible')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Accessible Observatory')
        
    def test_filter_by_multiple_tags(self):
        """Test filtering by multiple tags"""
        response = self.client.get('/api/v1/viewing-locations/?tags=beginner')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)  # Both beginner-friendly locations
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Mountain Park', names)
        self.assertIn('Accessible Observatory', names)
        
    def test_combine_category_and_tag_filters(self):
        """Test combining category and tag filters"""
        response = self.client.get(
            f'/api/v1/viewing-locations/?category={self.mountain_cat.slug}&tag=beginner'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Only Mountain Park is both mountain category AND beginner tag
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Mountain Park')
        
    def test_invalid_category_slug(self):
        """Test filtering with non-existent category slug"""
        response = self.client.get('/api/v1/viewing-locations/?category=nonexistent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 0)  # No results for invalid category