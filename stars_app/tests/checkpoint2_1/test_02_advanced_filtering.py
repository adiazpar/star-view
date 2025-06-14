"""
Test Suite for Advanced Search and Filtering System
==================================================

This test module validates the comprehensive filtering system including:
- Quality score range filtering
- Light pollution filtering
- Radius-based geographical searches
- Date range filtering
- Category and tag filtering
- Complex multi-criteria searches

How to run these tests:
----------------------
# Run all filtering tests:
python manage.py test stars_app.tests.checkpoint2.1.test_02_advanced_filtering

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_02_advanced_filtering.QualityFilteringTest

# Run with verbose output:
python manage.py test stars_app.tests.checkpoint2.1.test_02_advanced_filtering --verbosity=2

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_02_advanced_filtering
coverage report

Test Categories:
---------------
1. QualityFilteringTest - Tests filtering by quality metrics
2. GeographicalFilteringTest - Tests radius-based location searches
3. TimeBasedFilteringTest - Tests date range and recency filters
4. CategoryTagFilteringTest - Tests category and tag-based filtering
5. ComplexFilteringTest - Tests combining multiple filter criteria

Requirements:
------------
- Django test framework
- geopy library for distance calculations
- Test database with spatial support
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation, LocationCategory, LocationTag
from datetime import datetime, timedelta
import json


@override_settings(DISABLE_EXTERNAL_APIS=True)
class QualityFilteringTest(TestCase):
    """Test filtering by quality metrics like score and light pollution"""
    
    def setUp(self):
        """Create locations with varying quality scores"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create locations with different quality scores
        self.high_quality = ViewingLocation.objects.create(
            name='High Quality Site',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.high_quality.pk).update(
            quality_score=95.0,
            light_pollution_value=18.5  # Lower is better (darker)
        )
        self.high_quality.refresh_from_db()
        
        self.medium_quality = ViewingLocation.objects.create(
            name='Medium Quality Site',
            latitude=40.1,
            longitude=-105.1,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.medium_quality.pk).update(
            quality_score=70.0,
            light_pollution_value=20.0
        )
        self.medium_quality.refresh_from_db()
        
        self.low_quality = ViewingLocation.objects.create(
            name='Low Quality Site',
            latitude=40.2,
            longitude=-105.2,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.low_quality.pk).update(
            quality_score=45.0,
            light_pollution_value=22.5  # Higher means more light pollution
        )
        self.low_quality.refresh_from_db()
    
    def test_filter_by_minimum_quality_score(self):
        """Test filtering locations with minimum quality score"""
        response = self.client.get('/api/v1/viewing-locations/?min_quality_score=80')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'High Quality Site')
        
    def test_filter_by_quality_score_range(self):
        """Test filtering locations within quality score range"""
        response = self.client.get('/api/v1/viewing-locations/?min_quality_score=60&max_quality_score=80')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Medium Quality Site')
        
    def test_filter_by_light_pollution_range(self):
        """Test filtering by light pollution values"""
        # Get locations with low light pollution (darker skies)
        response = self.client.get('/api/v1/viewing-locations/?max_light_pollution=19')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'High Quality Site')
        
    def test_combined_quality_filters(self):
        """Test combining multiple quality filters"""
        response = self.client.get(
            '/api/v1/viewing-locations/?min_quality_score=65&max_light_pollution=21'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)  # High and Medium quality sites
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('High Quality Site', names)
        self.assertIn('Medium Quality Site', names)


@override_settings(DISABLE_EXTERNAL_APIS=True)
class GeographicalFilteringTest(TestCase):
    """Test radius-based geographical filtering"""
    
    def setUp(self):
        """Create locations at various distances"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Center point: Denver, CO
        self.center_lat = 39.7392
        self.center_lng = -104.9903
        
        # Create nearby location (within 10km)
        self.nearby = ViewingLocation.objects.create(
            name='Nearby Location',
            latitude=39.7500,  # ~1.5km away
            longitude=-104.9900,
            added_by=self.user
        )
        
        # Create medium distance location (within 50km)
        self.medium = ViewingLocation.objects.create(
            name='Medium Distance',
            latitude=39.9000,  # ~20km away
            longitude=-105.0000,
            added_by=self.user
        )
        
        # Create far location (outside 50km)
        self.far = ViewingLocation.objects.create(
            name='Far Location',
            latitude=40.5000,  # ~85km away
            longitude=-105.0000,
            added_by=self.user
        )
    
    def test_radius_search_10km(self):
        """Test searching within 10km radius"""
        response = self.client.get(
            f'/api/v1/viewing-locations/?lat={self.center_lat}&lng={self.center_lng}&radius=10'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Nearby Location')
        
    def test_radius_search_50km(self):
        """Test searching within 50km radius"""
        response = self.client.get(
            f'/api/v1/viewing-locations/?lat={self.center_lat}&lng={self.center_lng}&radius=50'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Nearby Location', names)
        self.assertIn('Medium Distance', names)
        self.assertNotIn('Far Location', names)
        
    def test_radius_search_without_coordinates(self):
        """Test that radius filter is ignored without lat/lng"""
        response = self.client.get('/api/v1/viewing-locations/?radius=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should return all locations when coordinates missing
        self.assertEqual(data['count'], 3)
        
    def test_invalid_coordinates(self):
        """Test handling of invalid coordinate values"""
        response = self.client.get('/api/v1/viewing-locations/?lat=invalid&lng=-104&radius=10')
        # django-filters validates NumberFilter inputs, so invalid values return 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error message
        data = response.json()
        self.assertIn('lat', data)  # Should have validation error for lat field


@override_settings(DISABLE_EXTERNAL_APIS=True)
class TimeBasedFilteringTest(TestCase):
    """Test filtering by dates and time ranges"""
    
    def setUp(self):
        """Create locations with different creation and visit dates"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create old location
        self.old_location = ViewingLocation.objects.create(
            name='Old Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        # Manually set created_at to 60 days ago
        self.old_location.created_at = timezone.now() - timedelta(days=60)
        self.old_location.save()
        
        # Create recent location
        self.recent_location = ViewingLocation.objects.create(
            name='Recent Location',
            latitude=40.1,
            longitude=-105.1,
            added_by=self.user
        )
        
        # Create recently visited location
        self.visited_location = ViewingLocation.objects.create(
            name='Recently Visited',
            latitude=40.2,
            longitude=-105.2,
            added_by=self.user,
            last_visited=timezone.now() - timedelta(days=5)
        )
        
    def test_filter_added_after_date(self):
        """Test filtering locations added after specific date"""
        # Get locations added in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        # Format as YYYY-MM-DD HH:MM:SS
        date_str = thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.get(f'/api/v1/viewing-locations/?added_after={date_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)  # Recent and Visited locations
        
        names = [loc['name'] for loc in data['results']]
        self.assertNotIn('Old Location', names)
        
    def test_filter_added_before_date(self):
        """Test filtering locations added before specific date"""
        # Get locations added before 40 days ago
        forty_days_ago = timezone.now() - timedelta(days=40)
        date_str = forty_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.get(f'/api/v1/viewing-locations/?added_before={date_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Old Location')
        
    def test_filter_recently_visited(self):
        """Test filtering for recently visited locations"""
        response = self.client.get('/api/v1/viewing-locations/?recently_visited=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Recently Visited')
        
    def test_date_range_filter(self):
        """Test filtering within date range"""
        # Get locations added between 70 and 10 days ago
        start_date = (timezone.now() - timedelta(days=70)).strftime('%Y-%m-%d %H:%M:%S')
        end_date = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        response = self.client.get(
            f'/api/v1/viewing-locations/?added_after={start_date}&added_before={end_date}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Old Location')


@override_settings(DISABLE_EXTERNAL_APIS=True)
class CategoryTagFilteringTest(TestCase):
    """Test filtering by categories and tags"""
    
    def setUp(self):
        """Create locations with categories and tags"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Get or create categories
        self.mountain_cat = LocationCategory.objects.filter(category_type='MOUNTAIN').first()
        if not self.mountain_cat:
            self.mountain_cat = LocationCategory.objects.create(
                name='Mountain',
                slug='mountain',
                category_type='MOUNTAIN'
            )
        self.park_cat = LocationCategory.objects.filter(category_type='PARK').first()
        if not self.park_cat:
            self.park_cat = LocationCategory.objects.create(
                name='Park',
                slug='park',
                category_type='PARK'
            )
        
        # Create tags
        self.beginner_tag = LocationTag.objects.create(
            name='Beginner Friendly',
            slug='beginner-friendly',
            is_approved=True
        )
        self.accessible_tag = LocationTag.objects.create(
            name='Wheelchair Accessible',
            slug='wheelchair-accessible',
            is_approved=True
        )
        
        # Create locations with categories and tags
        self.mountain_park = ViewingLocation.objects.create(
            name='Mountain Park Observatory',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        self.mountain_park.categories.add(self.mountain_cat, self.park_cat)
        self.mountain_park.tags.add(self.beginner_tag)
        
        self.accessible_park = ViewingLocation.objects.create(
            name='Accessible City Park',
            latitude=40.1,
            longitude=-105.1,
            added_by=self.user
        )
        self.accessible_park.categories.add(self.park_cat)
        self.accessible_park.tags.add(self.accessible_tag, self.beginner_tag)
        
        self.mountain_only = ViewingLocation.objects.create(
            name='Remote Mountain Peak',
            latitude=40.2,
            longitude=-105.2,
            added_by=self.user
        )
        self.mountain_only.categories.add(self.mountain_cat)
        
    def test_filter_by_single_category(self):
        """Test filtering by single category"""
        # Use the actual slug of the mountain category
        mountain_slug = self.mountain_cat.slug
        response = self.client.get(f'/api/v1/viewing-locations/?category={mountain_slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Mountain Park Observatory', names)
        self.assertIn('Remote Mountain Peak', names)
        
    def test_filter_by_multiple_categories(self):
        """Test filtering by multiple categories (AND operation)"""
        # Use the actual slugs
        mountain_slug = self.mountain_cat.slug
        park_slug = self.park_cat.slug
        response = self.client.get(f'/api/v1/viewing-locations/?categories={mountain_slug},{park_slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should return locations that have BOTH categories
        for location in data['results']:
            categories = [cat['slug'] for cat in location['categories']]
            self.assertIn(mountain_slug, categories)
            self.assertIn(park_slug, categories)
            
    def test_filter_by_single_tag(self):
        """Test filtering by single tag"""
        response = self.client.get('/api/v1/viewing-locations/?tag=wheelchair-accessible')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Accessible City Park')
        
    def test_filter_by_multiple_tags(self):
        """Test filtering by multiple tags"""
        response = self.client.get('/api/v1/viewing-locations/?tags=beginner-friendly')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Mountain Park Observatory', names)
        self.assertIn('Accessible City Park', names)


@override_settings(DISABLE_EXTERNAL_APIS=True)
class ComplexFilteringTest(TestCase):
    """Test combining multiple filter criteria"""
    
    def setUp(self):
        """Create diverse test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        
        # Get or create category
        self.park_cat = LocationCategory.objects.filter(category_type='PARK').first()
        if not self.park_cat:
            self.park_cat = LocationCategory.objects.create(
                name='Park',
                slug='park',
                category_type='PARK'
            )
        
        # Create ideal location (matches all criteria)
        self.ideal_location = ViewingLocation.objects.create(
            name='Perfect Dark Sky Park',
            latitude=39.7392,
            longitude=-104.9903,
            is_verified=True,
            verified_by=self.admin,
            visitor_count=25,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.ideal_location.pk).update(
            quality_score=92.0,
            light_pollution_value=17.5
        )
        self.ideal_location.refresh_from_db()
        self.ideal_location.categories.add(self.park_cat)
        
        # Create partial match location
        self.partial_match = ViewingLocation.objects.create(
            name='Good Urban Park',
            latitude=39.7500,
            longitude=-104.9900,
            is_verified=False,
            visitor_count=5,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.partial_match.pk).update(
            quality_score=75.0,
            light_pollution_value=21.0
        )
        self.partial_match.refresh_from_db()
        self.partial_match.categories.add(self.park_cat)
        
        # Create non-matching location
        self.no_match = ViewingLocation.objects.create(
            name='Poor Location',
            latitude=45.0,
            longitude=-110.0,
            added_by=self.user
        )
        # Manually set quality score and light pollution after creation
        ViewingLocation.objects.filter(pk=self.no_match.pk).update(
            quality_score=40.0,
            light_pollution_value=25.0
        )
        self.no_match.refresh_from_db()
        
    def test_complex_quality_and_verification_filter(self):
        """Test combining quality, verification, and visitor filters"""
        response = self.client.get(
            '/api/v1/viewing-locations/?'
            'verified_only=true&'
            'min_quality_score=90&'
            'max_light_pollution=18&'
            'min_visitor_count=20'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Perfect Dark Sky Park')
        
    def test_complex_location_and_category_filter(self):
        """Test combining geographical and category filters"""
        # Use the actual slug of the park category
        park_slug = self.park_cat.slug
        response = self.client.get(
            '/api/v1/viewing-locations/?'
            'lat=39.7392&lng=-104.9903&radius=5&'  # 5km radius
            f'category={park_slug}&'
            'min_quality_score=70'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)  # Both parks are within 5km
        
        names = [loc['name'] for loc in data['results']]
        self.assertIn('Perfect Dark Sky Park', names)
        self.assertIn('Good Urban Park', names)
        
    def test_all_filters_combined(self):
        """Test using many filters together"""
        # Use the actual slug of the park category
        park_slug = self.park_cat.slug
        response = self.client.get(
            '/api/v1/viewing-locations/?'
            'lat=39.7392&lng=-104.9903&radius=10&'
            f'category={park_slug}&'
            'is_verified=true&'
            'min_quality_score=90&'
            'max_light_pollution=20&'
            'min_visitor_count=10'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Only the ideal location matches all criteria
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Perfect Dark Sky Park')
        
    def test_no_results_with_strict_filters(self):
        """Test that overly strict filters return empty results"""
        response = self.client.get(
            '/api/v1/viewing-locations/?'
            'min_quality_score=100&'  # Impossible score
            'max_light_pollution=10'   # Unrealistic light pollution
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['results']), 0)