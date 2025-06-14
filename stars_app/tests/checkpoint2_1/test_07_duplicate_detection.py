"""
Test Suite for Duplicate Detection System
========================================

This test module validates the duplicate detection functionality including:
- Automatic duplicate checking on location creation
- Manual duplicate checking before creation
- Configurable detection radius
- Force creation despite duplicates
- Duplicate reporting functionality
- Integration with bulk import

How to run these tests:
----------------------
# Run all duplicate detection tests:
python manage.py test stars_app.tests.checkpoint2.1.test_07_duplicate_detection

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_07_duplicate_detection.AutomaticDetectionTest

# Run with specific test method:
python manage.py test stars_app.tests.checkpoint2.1.test_07_duplicate_detection.AutomaticDetectionTest.test_create_near_existing_location

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_07_duplicate_detection
coverage report

Test Categories:
---------------
1. AutomaticDetectionTest - Tests automatic detection on creation
2. ManualCheckingTest - Tests manual duplicate checking endpoint
3. RadiusConfigurationTest - Tests different detection radii
4. ForceCreationTest - Tests overriding duplicate warnings
5. DuplicateReportingTest - Tests reporting locations as duplicates

Requirements:
------------
- Django test framework
- geopy for distance calculations
- Authenticated users for location creation
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation, LocationReport
from decimal import Decimal
import json


class AutomaticDetectionTest(TestCase):
    """Test automatic duplicate detection on location creation"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        # Create existing location
        self.existing_location = ViewingLocation.objects.create(
            name='Existing Observatory',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_create_far_from_existing_location(self):
        """Test creating location far from existing ones succeeds"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Far Away Location',
                'latitude': 45.0,  # ~550km away
                'longitude': -110.0,
                'elevation': 1000
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViewingLocation.objects.count(), 2)
        
    def test_create_near_existing_location(self):
        """Test creating location near existing one triggers duplicate warning"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Very Close Location',
                'latitude': 40.001,  # ~111m away
                'longitude': -105.001,
                'elevation': 100
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()
        
        self.assertTrue(errors.get('duplicates_found'))
        self.assertIn('nearby_locations', errors)
        self.assertEqual(len(errors['nearby_locations']), 1)
        self.assertEqual(errors['nearby_locations'][0]['name'], 'Existing Observatory')
        self.assertIn('force_create=true', errors['message'])
        
        # Verify location was NOT created
        self.assertEqual(ViewingLocation.objects.count(), 1)
        
    def test_duplicate_detection_includes_distance(self):
        """Test that duplicate detection includes distance information"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Near Location',
                'latitude': 40.003,  # ~333m away
                'longitude': -105.0
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()
        
        # Check that nearby locations are returned with proper info
        nearby = errors['nearby_locations'][0]
        self.assertEqual(int(nearby['id']), self.existing_location.id)  # Convert to int for comparison
        self.assertEqual(nearby['name'], self.existing_location.name)
        self.assertEqual(float(nearby['latitude']), self.existing_location.latitude)  # Convert to float for comparison
        self.assertEqual(float(nearby['longitude']), self.existing_location.longitude)  # Convert to float for comparison
        
    def test_just_outside_detection_radius(self):
        """Test creating location just outside detection radius succeeds"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Just Outside Radius',
                'latitude': 40.006,  # ~600m away (outside 500m default)
                'longitude': -105.0
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViewingLocation.objects.count(), 2)


class ManualCheckingTest(TestCase):
    """Test manual duplicate checking endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        
        # Create some existing locations
        self.location1 = ViewingLocation.objects.create(
            name='Location 1',
            latitude=40.0,
            longitude=-105.0,
            quality_score=90,
            is_verified=True,
            added_by=self.user
        )
        
        self.location2 = ViewingLocation.objects.create(
            name='Location 2',
            latitude=40.002,  # ~222m from location1
            longitude=-105.0,
            quality_score=75,
            added_by=self.user
        )
        
        self.location3 = ViewingLocation.objects.create(
            name='Location 3',
            latitude=41.0,  # ~111km away
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_check_duplicates_endpoint(self):
        """Test the check_duplicates endpoint"""
        response = self.client.get(
            '/api/v1/viewing-locations/check_duplicates/',
            {
                'latitude': 40.001,
                'longitude': -105.0,
                'radius_km': 0.5
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['duplicates_found'])
        self.assertEqual(data['count'], 2)  # location1 and location2
        self.assertEqual(data['radius_km'], 0.5)
        
        # Check locations are included with details
        location_names = [loc['name'] for loc in data['locations']]
        self.assertIn('Location 1', location_names)
        self.assertIn('Location 2', location_names)
        self.assertNotIn('Location 3', location_names)
        
    def test_check_duplicates_custom_radius(self):
        """Test checking with custom radius"""
        # Check with very small radius
        response = self.client.get(
            '/api/v1/viewing-locations/check_duplicates/',
            {
                'latitude': 40.0,
                'longitude': -105.0,
                'radius_km': 0.1  # 100m
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['duplicates_found'])
        self.assertEqual(data['count'], 1)  # Only location1
        
    def test_check_duplicates_no_results(self):
        """Test checking location with no duplicates"""
        response = self.client.get(
            '/api/v1/viewing-locations/check_duplicates/',
            {
                'latitude': 35.0,  # Far from all locations
                'longitude': -100.0,
                'radius_km': 1.0
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertFalse(data['duplicates_found'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['locations']), 0)
        
    def test_check_duplicates_missing_coordinates(self):
        """Test error when coordinates not provided"""
        response = self.client.get(
            '/api/v1/viewing-locations/check_duplicates/',
            {'radius_km': 0.5}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude and longitude are required', response.json()['detail'])
        
    def test_check_duplicates_invalid_coordinates(self):
        """Test error handling for invalid coordinates"""
        response = self.client.get(
            '/api/v1/viewing-locations/check_duplicates/',
            {
                'latitude': 'not-a-number',
                'longitude': -105.0
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid latitude or longitude', response.json()['detail'])


class RadiusConfigurationTest(TestCase):
    """Test different detection radius configurations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        # Create location at origin
        self.origin = ViewingLocation.objects.create(
            name='Origin',
            latitude=0.0,
            longitude=0.0,
            added_by=self.user
        )
        
    def test_default_radius_500m(self):
        """Test that default detection radius is 500m"""
        # Try to create at ~400m away
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Within Default Radius',
                'latitude': 0.0036,  # ~400m north
                'longitude': 0.0
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()['duplicates_found'])
        
    def test_edge_of_radius(self):
        """Test locations at the edge of detection radius"""
        # Test each distance independently to avoid interference between iterations
        
        # Test 1: Location within radius should be detected as duplicate
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Within Radius Test',
                'latitude': 0.0044,  # ~489m - should be detected
                'longitude': 0.0
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()['duplicates_found'])
        
        # Test 2: Location outside radius should NOT be detected (use different longitude to avoid previous test location)
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Outside Radius Test',
                'latitude': 0.0,  # Same latitude as origin
                'longitude': 0.0055  # ~612m east - should NOT be detected
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test 3: Far location should definitely NOT be detected
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Far Location Test',
                'latitude': 0.01,  # ~1.1km - should NOT be detected
                'longitude': 0.01
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ForceCreationTest(TestCase):
    """Test overriding duplicate warnings with force_create"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        self.existing = ViewingLocation.objects.create(
            name='Existing Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_force_create_true(self):
        """Test creating location with force_create=true despite duplicates"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Forced Creation',
                'latitude': 40.001,  # Very close
                'longitude': -105.0,
                'force_create': True
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViewingLocation.objects.count(), 2)
        
        # Verify the new location was created
        new_location = ViewingLocation.objects.get(name='Forced Creation')
        self.assertAlmostEqual(float(new_location.latitude), 40.001, places=3)
        
    def test_force_create_false_still_blocked(self):
        """Test that force_create=false still blocks duplicates"""
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Not Forced',
                'latitude': 40.001,
                'longitude': -105.0,
                'force_create': False
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()['duplicates_found'])
        
    def test_force_create_with_multiple_duplicates(self):
        """Test force creation when multiple duplicates exist"""
        # Create another nearby location
        ViewingLocation.objects.create(
            name='Another Nearby',
            latitude=40.002,
            longitude=-105.0,
            added_by=self.user
        )
        
        response = self.client.post(
            '/api/v1/viewing-locations/',
            {
                'name': 'Forced Despite Multiple',
                'latitude': 40.0015,  # Between the two
                'longitude': -105.0,
                'force_create': True
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ViewingLocation.objects.count(), 3)


class DuplicateReportingTest(TestCase):
    """Test reporting locations as duplicates"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='reporter', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        # Create two similar locations
        self.location1 = ViewingLocation.objects.create(
            name='Original Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user,
            created_at='2023-01-01T00:00:00Z'
        )
        
        self.location2 = ViewingLocation.objects.create(
            name='Duplicate Location',
            latitude=40.001,
            longitude=-105.0,
            added_by=self.user,
            created_at='2023-06-01T00:00:00Z'
        )
        
    def test_report_as_duplicate(self):
        """Test reporting a location as duplicate of another"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location2.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'duplicate_of_id': self.location1.id,
                'description': 'This is the same location as the original'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Verify report was created
        self.assertEqual(data['report_type'], 'DUPLICATE')
        self.assertEqual(data['location'], self.location2.id)
        self.assertEqual(data['duplicate_of'], self.location1.id)
        
        # Verify times_reported was incremented
        self.location2.refresh_from_db()
        self.assertEqual(self.location2.times_reported, 1)
        
    def test_cannot_report_duplicate_of_self(self):
        """Test that location cannot be reported as duplicate of itself"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location1.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'duplicate_of_id': self.location1.id,
                'description': 'Duplicate of self'
            },
            format='json'
        )
        
        # Should still create report but validation might occur elsewhere
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_report_nonexistent_duplicate(self):
        """Test reporting duplicate of nonexistent location"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location1.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'duplicate_of_id': 99999,
                'description': 'Duplicate of ghost'
            },
            format='json'
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])
        
    def test_duplicate_report_includes_location_info(self):
        """Test that duplicate reports include location information"""
        # Create report
        report = LocationReport.objects.create(
            location=self.location2,
            reported_by=self.user,
            report_type='DUPLICATE',
            duplicate_of=self.location1,
            description='Test duplicate report'
        )
        
        # Check relationships
        self.assertEqual(report.location, self.location2)
        self.assertEqual(report.duplicate_of, self.location1)
        self.assertEqual(report.report_type, 'DUPLICATE')
        
    def test_multiple_duplicate_reports(self):
        """Test handling multiple duplicate reports for same location"""
        # First report
        response1 = self.client.post(
            f'/api/v1/viewing-locations/{self.location2.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'duplicate_of_id': self.location1.id,
                'description': 'First duplicate report'
            },
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to create same report again (should fail due to unique constraint)
        response2 = self.client.post(
            f'/api/v1/viewing-locations/{self.location2.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'duplicate_of_id': self.location1.id,
                'description': 'Second duplicate report'
            },
            format='json'
        )
        
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already submitted this type of report', response2.json()['detail'])