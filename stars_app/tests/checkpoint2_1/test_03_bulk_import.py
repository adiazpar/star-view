"""
Test Suite for Bulk Location Import Feature
==========================================

This test module validates the bulk import functionality including:
- CSV file import with validation
- JSON data import
- Duplicate detection within imports
- Duplicate checking against existing database
- Dry run mode for validation
- Error handling and reporting

How to run these tests:
----------------------
# Run all bulk import tests:
python manage.py test stars_app.tests.checkpoint2.1.test_03_bulk_import

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_03_bulk_import.CSVImportTest

# Run with detailed output:
python manage.py test stars_app.tests.checkpoint2.1.test_03_bulk_import --verbosity=2

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_03_bulk_import
coverage report

Test Categories:
---------------
1. CSVImportTest - Tests CSV file import functionality
2. JSONImportTest - Tests JSON data import functionality
3. DuplicateDetectionTest - Tests duplicate detection logic
4. ValidationTest - Tests data validation and error handling
5. DryRunTest - Tests dry run mode behavior

Requirements:
------------
- Django test framework
- CSV and JSON parsing libraries
- Authenticated user for import permissions
- geopy for distance calculations
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation
import json
import csv
import io


class CSVImportTest(TestCase):
    """Test CSV file import functionality"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
    def create_csv_file(self, data):
        """Helper to create CSV file from data"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        content = output.getvalue().encode('utf-8')
        return SimpleUploadedFile('locations.csv', content, content_type='text/csv')
        
    def test_successful_csv_import(self):
        """Test importing valid CSV data"""
        csv_data = [
            {
                'name': 'Desert Observatory',
                'latitude': '33.5',
                'longitude': '-112.0',
                'elevation': '400',
                'formatted_address': 'Phoenix, AZ',
                'country': 'USA'
            },
            {
                'name': 'Mountain Viewpoint',
                'latitude': '34.5',
                'longitude': '-118.0',
                'elevation': '1500',
                'formatted_address': 'Los Angeles, CA',
                'country': 'USA'
            }
        ]
        
        csv_file = self.create_csv_file(csv_data)
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'file': csv_file,
                'format': 'csv',
                'dry_run': False
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total_valid_locations'], 2)
        self.assertEqual(data['duplicates_found'], 0)
        self.assertEqual(data['created_count'], 2)
        self.assertFalse(data['dry_run'])
        
        # Verify locations were created
        self.assertEqual(ViewingLocation.objects.count(), 2)
        
    def test_csv_with_missing_required_fields(self):
        """Test CSV import with missing required fields"""
        csv_data = [
            {
                'name': 'Incomplete Location',
                'latitude': '33.5'
                # Missing longitude
            }
        ]
        
        csv_file = self.create_csv_file(csv_data)
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'file': csv_file,
                'format': 'csv',
                'dry_run': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_csv_with_invalid_coordinates(self):
        """Test CSV import with invalid coordinate values"""
        csv_data = [
            {
                'name': 'Invalid Coords',
                'latitude': 'not-a-number',
                'longitude': '-112.0'
            }
        ]
        
        csv_file = self.create_csv_file(csv_data)
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'file': csv_file,
                'format': 'csv',
                'dry_run': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JSONImportTest(TestCase):
    """Test JSON data import functionality"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
    def test_successful_json_import(self):
        """Test importing valid JSON data"""
        json_data = [
            {
                'name': 'Beach Observatory',
                'latitude': 33.0,
                'longitude': -117.0,
                'elevation': 10,
                'formatted_address': 'San Diego, CA',
                'country': 'USA'
            },
            {
                'name': 'Lake Viewpoint',
                'latitude': 36.0,
                'longitude': -115.0,
                'elevation': 600,
                'locality': 'Las Vegas',
                'administrative_area': 'NV',
                'country': 'USA'
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': False,
                'data': json_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['total_valid_locations'], 2)
        self.assertEqual(data['created_count'], 2)
        
        # Verify locations were created with correct data
        beach = ViewingLocation.objects.get(name='Beach Observatory')
        self.assertEqual(beach.latitude, 33.0)
        self.assertEqual(beach.longitude, -117.0)
        self.assertEqual(beach.elevation, 10)
        
    def test_json_file_upload(self):
        """Test uploading JSON as a file"""
        json_data = [
            {
                'name': 'File Upload Test',
                'latitude': 40.0,
                'longitude': -105.0
            }
        ]
        
        json_content = json.dumps(json_data).encode('utf-8')
        json_file = SimpleUploadedFile('locations.json', json_content, content_type='application/json')
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'file': json_file,
                'format': 'json',
                'dry_run': False
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewingLocation.objects.count(), 1)
        
    def test_invalid_json_format(self):
        """Test handling of invalid JSON data"""
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'data': 'not-valid-json'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DuplicateDetectionTest(TestCase):
    """Test duplicate detection during import"""
    
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
        
    def test_duplicate_detection_within_import(self):
        """Test detecting duplicates within the import data itself"""
        import_data = [
            {
                'name': 'Location A',
                'latitude': 35.0,
                'longitude': -110.0
            },
            {
                'name': 'Location B',
                'latitude': 35.001,  # Very close to Location A
                'longitude': -110.001
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # First location should show duplicate in import
        first_result = data['results'][0]
        self.assertGreater(len(first_result['duplicates_in_import']), 0)
        self.assertEqual(first_result['duplicates_in_import'][0]['name'], 'Location B')
        
    def test_duplicate_detection_against_database(self):
        """Test detecting duplicates against existing database locations"""
        import_data = [
            {
                'name': 'Near Existing Location',
                'latitude': 40.001,  # Very close to existing
                'longitude': -105.001
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['duplicates_found'], 1)
        result = data['results'][0]
        self.assertTrue(result['is_duplicate'])
        self.assertGreater(len(result['existing_nearby']), 0)
        self.assertEqual(result['existing_nearby'][0]['name'], 'Existing Observatory')
        
    def test_duplicate_threshold_distance(self):
        """Test that duplicate detection respects distance threshold"""
        import_data = [
            {
                'name': 'Just Outside Threshold',
                'latitude': 40.01,  # ~1.1km away
                'longitude': -105.0
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should not be detected as duplicate (outside 0.5km threshold)
        self.assertEqual(data['duplicates_found'], 0)


class ValidationTest(TestCase):
    """Test data validation during import"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
    def test_coordinate_range_validation(self):
        """Test validation of coordinate ranges"""
        import_data = [
            {
                'name': 'Invalid Latitude',
                'latitude': 91.0,  # Invalid: > 90
                'longitude': 0.0
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        # Should still process but location creation would fail
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_missing_both_file_and_data(self):
        """Test error when neither file nor data provided"""
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()
        self.assertIn('Either \'file\' or \'data\' must be provided', str(errors))
        
    def test_both_file_and_data_provided(self):
        """Test error when both file and data provided"""
        csv_file = SimpleUploadedFile('test.csv', b'test', content_type='text/csv')
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'file': csv_file,
                'data': [{'name': 'test'}],
                'format': 'json'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DryRunTest(TestCase):
    """Test dry run mode behavior"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.force_authenticate(user=self.user)
        
    def test_dry_run_does_not_create_locations(self):
        """Test that dry run mode doesn't create any locations"""
        initial_count = ViewingLocation.objects.count()
        
        import_data = [
            {
                'name': 'Dry Run Test 1',
                'latitude': 45.0,
                'longitude': -90.0
            },
            {
                'name': 'Dry Run Test 2',
                'latitude': 46.0,
                'longitude': -91.0
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['dry_run'])
        self.assertEqual(data['total_valid_locations'], 2)
        self.assertNotIn('created_count', data)  # No creation in dry run
        
        # Verify no locations were created
        self.assertEqual(ViewingLocation.objects.count(), initial_count)
        
    def test_dry_run_still_checks_duplicates(self):
        """Test that dry run mode still performs duplicate checking"""
        # Create existing location
        existing = ViewingLocation.objects.create(
            name='Existing for Dry Run',
            latitude=50.0,
            longitude=-100.0,
            added_by=self.user
        )
        
        import_data = [
            {
                'name': 'Near Existing',
                'latitude': 50.001,
                'longitude': -100.001
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': True,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['duplicates_found'], 1)
        self.assertTrue(data['results'][0]['is_duplicate'])
        
    def test_non_dry_run_creates_and_returns_ids(self):
        """Test that non-dry run mode creates locations and returns IDs"""
        import_data = [
            {
                'name': 'Real Import 1',
                'latitude': 38.0,
                'longitude': -122.0
            },
            {
                'name': 'Real Import 2',
                'latitude': 37.0,
                'longitude': -121.0
            }
        ]
        
        response = self.client.post(
            '/api/v1/viewing-locations/bulk_import/',
            {
                'format': 'json',
                'dry_run': False,
                'data': import_data
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertFalse(data['dry_run'])
        self.assertEqual(data['created_count'], 2)
        self.assertEqual(len(data['created_ids']), 2)
        
        # Verify locations exist
        for location_id in data['created_ids']:
            self.assertTrue(ViewingLocation.objects.filter(id=location_id).exists())