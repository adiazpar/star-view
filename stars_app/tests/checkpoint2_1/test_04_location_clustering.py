"""
Test Suite for Location Clustering System
========================================

This test module validates the map clustering functionality including:
- Dynamic clustering based on zoom levels
- Cluster radius calculations
- Bounds-based filtering
- Cluster statistics (average quality, verification status)
- Performance with large datasets

How to run these tests:
----------------------
# Run all clustering tests:
python manage.py test stars_app.tests.checkpoint2.1.test_04_location_clustering

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_04_location_clustering.ClusteringAlgorithmTest

# Run with timing information:
python manage.py test stars_app.tests.checkpoint2.1.test_04_location_clustering --timing

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_04_location_clustering
coverage report

Test Categories:
---------------
1. ClusteringAlgorithmTest - Tests core clustering algorithm
2. ZoomLevelTest - Tests zoom-based clustering behavior
3. BoundsFilteringTest - Tests geographical bounds filtering
4. ClusterStatisticsTest - Tests cluster aggregate calculations
5. PerformanceTest - Tests clustering with large datasets

Requirements:
------------
- Django test framework
- ClusteringService implementation
- Test locations with various distributions
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation
from stars_app.services.clustering_service import ClusteringService
import time


class ClusteringAlgorithmTest(TestCase):
    """Test the core clustering algorithm"""
    
    def setUp(self):
        """Create test locations"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create cluster of 3 nearby locations (within 1km)
        self.cluster_center = ViewingLocation.objects.create(
            name='Cluster Center',
            latitude=40.0,
            longitude=-105.0,
            quality_score=90,
            added_by=self.user
        )
        
        self.cluster_member1 = ViewingLocation.objects.create(
            name='Cluster Member 1',
            latitude=40.005,  # ~0.5km away
            longitude=-105.0,
            quality_score=85,
            added_by=self.user
        )
        
        self.cluster_member2 = ViewingLocation.objects.create(
            name='Cluster Member 2',
            latitude=40.0,
            longitude=-105.008,  # ~0.8km away
            quality_score=80,
            added_by=self.user
        )
        
        # Create isolated location
        self.isolated = ViewingLocation.objects.create(
            name='Isolated Location',
            latitude=41.0,  # ~111km away
            longitude=-105.0,
            quality_score=95,
            added_by=self.user
        )
        
    def test_haversine_distance_calculation(self):
        """Test the haversine distance formula accuracy"""
        # Test known distances
        distance = ClusteringService.haversine_distance(
            40.0, -105.0,  # Denver area
            40.01, -105.0  # ~1.11km north
        )
        self.assertAlmostEqual(distance, 1.11, places=1)
        
        # Test same location
        distance = ClusteringService.haversine_distance(
            40.0, -105.0,
            40.0, -105.0
        )
        self.assertEqual(distance, 0.0)
        
    def test_zoom_cluster_radius(self):
        """Test cluster radius calculation for different zoom levels"""
        # Test various zoom levels
        test_cases = [
            (0, 100.0),      # Zoom 0: 100km
            (5, 17.68),      # Zoom 5: ~17.68km
            (10, 3.125),     # Zoom 10: ~3.125km
            (15, 0.55),      # Zoom 15: ~0.55km
            (16, 0.05),      # Zoom 16+: 50m fixed radius for high detail
            (20, 0.05),      # Zoom 20: 50m fixed radius for high detail
        ]
        
        for zoom, expected_radius in test_cases:
            radius = ClusteringService.get_zoom_cluster_radius(zoom)
            self.assertAlmostEqual(radius, expected_radius, places=2)
            
    def test_basic_clustering(self):
        """Test basic clustering of nearby locations"""
        locations = [
            {
                'id': loc.id,
                'name': loc.name,
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'quality_score': loc.quality_score
            }
            for loc in ViewingLocation.objects.all()
        ]
        
        # Cluster at zoom level 10 (~3km radius)
        clusters = ClusteringService.cluster_locations(locations, zoom_level=10)
        
        # Should have 2 items: 1 cluster and 1 individual location
        self.assertEqual(len(clusters), 2)
        
        # Find the cluster
        cluster = next(c for c in clusters if c.get('type') == 'cluster')
        individual = next(c for c in clusters if c.get('type') == 'location')
        
        # Verify cluster contains 3 locations
        self.assertEqual(cluster['count'], 3)
        self.assertEqual(len(cluster['locations']), 3)
        
        # Verify individual location
        self.assertEqual(individual['name'], 'Isolated Location')


class ZoomLevelTest(TestCase):
    """Test zoom-based clustering behavior"""
    
    def setUp(self):
        """Set up test client and locations"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create locations at various distances
        # Group 1: Very close (100m apart)
        for i in range(3):
            ViewingLocation.objects.create(
                name=f'Very Close {i}',
                latitude=40.0 + (i * 0.001),  # ~100m apart
                longitude=-105.0,
                added_by=self.user
            )
            
        # Group 2: Medium distance (5km from group 1)
        for i in range(2):
            ViewingLocation.objects.create(
                name=f'Medium Distance {i}',
                latitude=40.05,
                longitude=-105.0 + (i * 0.001),
                added_by=self.user
            )
            
    def test_high_zoom_no_clustering(self):
        """Test that high zoom levels show individual locations"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=18')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # At zoom 18, radius is very small, so minimal clustering
        self.assertEqual(data['total_locations'], 5)
        self.assertGreaterEqual(data['individual_count'], 3)
        
    def test_medium_zoom_partial_clustering(self):
        """Test medium zoom levels create some clusters"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=12')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should cluster the very close locations
        self.assertGreater(data['cluster_count'], 0)
        self.assertLess(len(data['clusters']), 5)  # Some clustering occurred
        
    def test_low_zoom_maximum_clustering(self):
        """Test low zoom levels create large clusters"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # At zoom 5, should cluster most/all locations
        self.assertEqual(len(data['clusters']), 1)  # All in one cluster
        self.assertEqual(data['cluster_count'], 1)


class BoundsFilteringTest(TestCase):
    """Test geographical bounds filtering in clustering"""
    
    def setUp(self):
        """Create locations across a wide area"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create locations in different regions
        self.north_locations = []
        for i in range(3):
            loc = ViewingLocation.objects.create(
                name=f'North Location {i}',
                latitude=41.0 + (i * 0.01),
                longitude=-105.0,
                added_by=self.user
            )
            self.north_locations.append(loc)
            
        self.south_locations = []
        for i in range(2):
            loc = ViewingLocation.objects.create(
                name=f'South Location {i}',
                latitude=39.0 + (i * 0.01),
                longitude=-105.0,
                added_by=self.user
            )
            self.south_locations.append(loc)
            
    def test_bounds_filtering_north_only(self):
        """Test filtering to show only northern locations"""
        response = self.client.get(
            '/api/v1/viewing-locations/clustered/?'
            'zoom=10&'
            'north=42&south=40.5&'
            'east=-104&west=-106'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should only include northern locations
        self.assertEqual(data['total_locations'], 3)
        
    def test_bounds_filtering_south_only(self):
        """Test filtering to show only southern locations"""
        response = self.client.get(
            '/api/v1/viewing-locations/clustered/?'
            'zoom=10&'
            'north=40&south=38&'
            'east=-104&west=-106'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Should only include southern locations
        self.assertEqual(data['total_locations'], 2)
        
    def test_bounds_filtering_none_in_bounds(self):
        """Test bounds that exclude all locations"""
        response = self.client.get(
            '/api/v1/viewing-locations/clustered/?'
            'zoom=10&'
            'north=38&south=37&'  # Too far south
            'east=-104&west=-106'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total_locations'], 0)
        self.assertEqual(len(data['clusters']), 0)


class ClusterStatisticsTest(TestCase):
    """Test cluster statistics calculations"""
    
    def setUp(self):
        """Create locations with various properties"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        
        # Create verified high-quality location
        self.verified_location = ViewingLocation.objects.create(
            name='Verified Location',
            latitude=40.0,
            longitude=-105.0,
            is_verified=True,
            verified_by=self.admin,
            added_by=self.user
        )
        # Manually set quality score after creation
        ViewingLocation.objects.filter(pk=self.verified_location.pk).update(quality_score=95)
        self.verified_location.refresh_from_db()
        
        # Create unverified medium-quality locations nearby
        self.unverified1 = ViewingLocation.objects.create(
            name='Unverified 1',
            latitude=40.001,
            longitude=-105.0,
            is_verified=False,
            added_by=self.user
        )
        # Manually set quality score after creation
        ViewingLocation.objects.filter(pk=self.unverified1.pk).update(quality_score=70)
        self.unverified1.refresh_from_db()
        
        self.unverified2 = ViewingLocation.objects.create(
            name='Unverified 2',
            latitude=40.0,
            longitude=-105.001,
            is_verified=False,
            added_by=self.user
        )
        # Manually set quality score after creation
        ViewingLocation.objects.filter(pk=self.unverified2.pk).update(quality_score=60)
        self.unverified2.refresh_from_db()
        
    def test_cluster_average_quality_score(self):
        """Test calculation of average quality score in clusters"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=12')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Find the cluster
        cluster = next(c for c in data['clusters'] if c.get('type') == 'cluster')
        
        # Average should be (95 + 70 + 60) / 3 = 75
        self.assertAlmostEqual(cluster['avg_quality_score'], 75.0, places=1)
        
    def test_cluster_verification_status(self):
        """Test has_verified flag in clusters"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=12')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        cluster = next(c for c in data['clusters'] if c.get('type') == 'cluster')
        
        # Should be true since one location is verified
        self.assertTrue(cluster['has_verified'])
        
    def test_cluster_bounds_calculation(self):
        """Test cluster boundary calculations"""
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=12')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        cluster = next(c for c in data['clusters'] if c.get('type') == 'cluster')
        
        # Check bounds encompass all locations
        self.assertLessEqual(cluster['bounds']['south'], 40.0)
        self.assertGreaterEqual(cluster['bounds']['north'], 40.001)
        self.assertLessEqual(cluster['bounds']['west'], -105.001)
        self.assertGreaterEqual(cluster['bounds']['east'], -105.0)


class PerformanceTest(TestCase):
    """Test clustering performance with large datasets"""
    
    def setUp(self):
        """Create many locations for performance testing"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create 100 locations in a grid pattern
        locations = []
        for lat in range(10):
            for lng in range(10):
                locations.append(ViewingLocation(
                    name=f'Location {lat}-{lng}',
                    latitude=40.0 + (lat * 0.1),
                    longitude=-105.0 + (lng * 0.1),
                    quality_score=50 + (lat + lng),
                    added_by=self.user
                ))
                
        # Bulk create for efficiency
        ViewingLocation.objects.bulk_create(locations)
        
    def test_clustering_performance(self):
        """Test that clustering completes in reasonable time"""
        start_time = time.time()
        
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=8')
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should complete within 2 seconds even with 100 locations
        self.assertLess(duration, 2.0)
        
        data = response.json()
        self.assertEqual(data['total_locations'], 100)
        
    def test_clustering_with_filters(self):
        """Test clustering performance with additional filters"""
        start_time = time.time()
        
        # Apply quality filter to reduce dataset before clustering
        response = self.client.get(
            '/api/v1/viewing-locations/clustered/?zoom=10&min_quality_score=60'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(duration, 1.5)  # Should be faster with filter
        
        data = response.json()
        # Should have fewer locations due to quality filter
        self.assertLess(data['total_locations'], 100)
        
    def test_individual_location_properties(self):
        """Test that individual locations retain all properties"""
        # Create a unique isolated location
        special_location = ViewingLocation.objects.create(
            name='Special Isolated Location',
            latitude=45.0,  # Far from others
            longitude=-110.0,
            is_verified=True,
            added_by=self.user
        )
        # Manually set properties after creation
        ViewingLocation.objects.filter(pk=special_location.pk).update(
            quality_score=100,
            light_pollution_value=15.5,
            rating_count=10,
            average_rating=4.5
        )
        special_location.refresh_from_db()
        
        response = self.client.get('/api/v1/viewing-locations/clustered/?zoom=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        # Find the special location
        special = next(
            c for c in data['clusters'] 
            if c.get('type') == 'location' and c.get('name') == 'Special Isolated Location'
        )
        
        # Verify all properties are preserved
        self.assertEqual(special['quality_score'], 100)
        self.assertTrue(special['is_verified'])
        self.assertEqual(special['light_pollution_value'], 15.5)
        self.assertEqual(special['rating_count'], 10)
        self.assertEqual(special['average_rating'], 4.5)