"""
Test Suite for Location Verification System
==========================================

This test module validates the location verification system functionality including:
- Verification field defaults and behavior
- Verification status filtering
- Report counting and visitor tracking
- Permissions for verification actions

How to run these tests:
----------------------
# Run all verification tests:
python manage.py test stars_app.tests.checkpoint2.1.test_01_verification_system

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_01_verification_system.VerificationFieldsTest

# Run a specific test method:
python manage.py test stars_app.tests.checkpoint2.1.test_01_verification_system.VerificationFieldsTest.test_default_verification_values

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_01_verification_system
coverage report

Test Categories:
---------------
1. VerificationFieldsTest - Tests model field defaults and basic behavior
2. VerificationFilteringTest - Tests API filtering by verification status
3. VerificationPermissionsTest - Tests who can verify locations
4. VerificationWorkflowTest - Tests the complete verification process

Requirements:
------------
- Django test framework
- Test database (automatically created)
- Authenticated user for some tests
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation
import json


class VerificationFieldsTest(TestCase):
    """Test that verification fields work correctly at the model level"""
    
    def setUp(self):
        """Create test user and location"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
    def test_default_verification_values(self):
        """Test that new locations have correct default verification values"""
        location = ViewingLocation.objects.create(
            name='Test Dark Sky Location',
            latitude=40.7128,
            longitude=-74.0060,
            elevation=100,
            added_by=self.user
        )
        
        # Check defaults
        self.assertFalse(location.is_verified)
        self.assertIsNone(location.verification_date)
        self.assertIsNone(location.verified_by)
        self.assertEqual(location.verification_notes, '')
        self.assertEqual(location.times_reported, 0)
        self.assertIsNone(location.last_visited)
        self.assertEqual(location.visitor_count, 0)
        
    def test_verification_process(self):
        """Test the verification process updates fields correctly"""
        admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        location = ViewingLocation.objects.create(
            name='Unverified Location',
            latitude=35.0,
            longitude=-120.0,
            added_by=self.user
        )
        
        # Verify the location
        location.is_verified = True
        location.verification_date = timezone.now()
        location.verified_by = admin_user
        location.verification_notes = 'Verified during site visit. Excellent conditions.'
        location.save()
        
        # Reload and check
        location.refresh_from_db()
        self.assertTrue(location.is_verified)
        self.assertIsNotNone(location.verification_date)
        self.assertEqual(location.verified_by, admin_user)
        self.assertEqual(location.verification_notes, 'Verified during site visit. Excellent conditions.')
        
    def test_report_counter_increment(self):
        """Test that report counter increments correctly"""
        location = ViewingLocation.objects.create(
            name='Reported Location',
            latitude=36.0,
            longitude=-121.0,
            added_by=self.user
        )
        
        # Simulate reports
        for i in range(3):
            location.times_reported += 1
            location.save()
            
        location.refresh_from_db()
        self.assertEqual(location.times_reported, 3)
        
    def test_visitor_tracking(self):
        """Test visitor count and last visited tracking"""
        location = ViewingLocation.objects.create(
            name='Popular Location',
            latitude=37.0,
            longitude=-122.0,
            added_by=self.user
        )
        
        # Update visitor info
        location.visitor_count = 5
        location.last_visited = timezone.now()
        location.save()
        
        location.refresh_from_db()
        self.assertEqual(location.visitor_count, 5)
        self.assertIsNotNone(location.last_visited)


class VerificationFilteringTest(TestCase):
    """Test API filtering by verification status"""
    
    def setUp(self):
        """Create test data with mix of verified and unverified locations"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
        # Create verified locations
        for i in range(3):
            ViewingLocation.objects.create(
                name=f'Verified Location {i}',
                latitude=40.0 + i,
                longitude=-74.0 + i,
                added_by=self.user,
                is_verified=True,
                verified_by=self.admin,
                verification_date=timezone.now()
            )
            
        # Create unverified locations
        for i in range(2):
            ViewingLocation.objects.create(
                name=f'Unverified Location {i}',
                latitude=35.0 + i,
                longitude=-118.0 + i,
                added_by=self.user,
                is_verified=False
            )
    
    def test_filter_verified_only(self):
        """Test filtering to show only verified locations"""
        response = self.client.get('/api/v1/viewing-locations/?is_verified=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 3)
        
        # Check all returned locations are verified
        for location in data['results']:
            self.assertTrue(location['is_verified'])
            
    def test_filter_unverified_only(self):
        """Test filtering to show only unverified locations"""
        response = self.client.get('/api/v1/viewing-locations/?is_verified=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 2)
        
        # Check all returned locations are unverified
        for location in data['results']:
            self.assertFalse(location['is_verified'])
            
    def test_filter_by_report_count(self):
        """Test filtering by number of times reported"""
        # Create a highly reported location
        problem_location = ViewingLocation.objects.create(
            name='Problem Location',
            latitude=38.0,
            longitude=-123.0,
            added_by=self.user,
            times_reported=5
        )
        
        # Filter for locations reported more than 3 times
        response = self.client.get('/api/v1/viewing-locations/?times_reported__gt=3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'Problem Location')
        
    def test_filter_by_visitor_count(self):
        """Test filtering by minimum visitor count"""
        # Update a location to have visitors
        location = ViewingLocation.objects.first()
        location.visitor_count = 10
        location.save()
        
        response = self.client.get('/api/v1/viewing-locations/?min_visitor_count=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['visitor_count'], 10)


class VerificationPermissionsTest(TestCase):
    """Test permissions for verification actions"""
    
    def setUp(self):
        """Create users with different permission levels"""
        self.client = APIClient()
        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            password='pass123',
            is_staff=True
        )
        self.location = ViewingLocation.objects.create(
            name='Test Location',
            latitude=40.0,
            longitude=-74.0,
            added_by=self.regular_user
        )
        
    def test_regular_user_cannot_verify(self):
        """Test that regular users cannot verify locations"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Attempt to update verification status
        response = self.client.patch(
            f'/api/v1/viewing-locations/{self.location.id}/',
            {'is_verified': True},
            format='json'
        )
        
        # Should succeed but verification fields should be read-only
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that verification wasn't actually updated
        self.location.refresh_from_db()
        self.assertFalse(self.location.is_verified)
        
    def test_serializer_verification_fields_readonly(self):
        """Test that verification fields are read-only in serializer"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Get location details
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verification fields should be present but read-only
        data = response.json()
        self.assertIn('is_verified', data)
        self.assertIn('verification_date', data)
        self.assertIn('verified_by', data)
        self.assertIn('times_reported', data)


class VerificationWorkflowTest(TestCase):
    """Test complete verification workflow scenarios"""
    
    def setUp(self):
        """Set up test scenario"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='contributor',
            password='pass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        
    def test_location_lifecycle_with_verification(self):
        """Test complete lifecycle from creation to verification"""
        self.client.force_authenticate(user=self.user)
        
        # Step 1: Create location
        create_data = {
            'name': 'New Observatory Site',
            'latitude': 34.0522,
            'longitude': -118.2437,
            'elevation': 500
        }
        
        response = self.client.post(
            '/api/v1/viewing-locations/',
            create_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        location_id = response.json()['id']
        
        # Step 2: Check initial verification status
        location = ViewingLocation.objects.get(id=location_id)
        self.assertFalse(location.is_verified)
        self.assertEqual(location.visitor_count, 0)
        
        # Step 3: Simulate visits and reviews (updating visitor count)
        location.visitor_count = 5
        location.last_visited = timezone.now()
        location.save()
        
        # Step 4: Admin verifies location
        location.is_verified = True
        location.verified_by = self.admin
        location.verification_date = timezone.now()
        location.verification_notes = 'Site visit confirmed. Good access road and parking.'
        location.save()
        
        # Step 5: Verify the complete state
        response = self.client.get(f'/api/v1/viewing-locations/{location_id}/')
        data = response.json()
        
        self.assertTrue(data['is_verified'])
        self.assertEqual(data['verified_by']['username'], 'admin')
        self.assertIsNotNone(data['verification_date'])
        self.assertEqual(data['visitor_count'], 5)
        self.assertIsNotNone(data['last_visited'])
        
    def test_highly_reported_locations(self):
        """Test handling of locations with many reports"""
        location = ViewingLocation.objects.create(
            name='Problematic Location',
            latitude=33.0,
            longitude=-117.0,
            added_by=self.user
        )
        
        # Simulate multiple reports
        location.times_reported = 10
        location.save()
        
        # Query for highly reported locations
        response = self.client.get('/api/v1/viewing-locations/?times_reported__gte=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertGreater(data['count'], 0)
        
        # All returned locations should have high report counts
        for loc in data['results']:
            self.assertGreaterEqual(loc['times_reported'], 5)