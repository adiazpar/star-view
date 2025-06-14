"""
Test Suite for Location Photo Upload System
==========================================

This test module validates the photo upload functionality including:
- Photo upload with various file types
- Primary photo designation
- Photo approval workflow
- Caption and metadata handling
- Permission checks for photo management
- Multiple photos per location

How to run these tests:
----------------------
# Run all photo upload tests:
python manage.py test stars_app.tests.checkpoint2.1.test_05_photo_uploads

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_05_photo_uploads.PhotoUploadTest

# Run with specific test:
python manage.py test stars_app.tests.checkpoint2.1.test_05_photo_uploads.PhotoUploadTest.test_upload_single_photo

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_05_photo_uploads
coverage report

Test Categories:
---------------
1. PhotoUploadTest - Tests basic photo upload functionality
2. PrimaryPhotoTest - Tests primary photo designation and management
3. PhotoPermissionsTest - Tests access control for photo operations
4. PhotoListingTest - Tests photo retrieval and filtering
5. PhotoMetadataTest - Tests EXIF data and metadata handling

Requirements:
------------
- Django test framework with file upload support
- PIL/Pillow for image handling (optional)
- Authenticated users for upload permissions
- Media storage configuration
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation, LocationPhoto
import io
from PIL import Image
import tempfile
import os


class PhotoUploadTest(TestCase):
    """Test basic photo upload functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='photographer', password='pass123')
        self.other_user = User.objects.create_user(username='other', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Photogenic Observatory',
            latitude=34.0522,
            longitude=-118.2437,
            added_by=self.user
        )
        
    def create_test_image(self, name='test.jpg', size=(100, 100), color='red'):
        """Helper to create test image file"""
        file = io.BytesIO()
        image = Image.new('RGB', size, color)
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(name, file.getvalue(), content_type='image/jpeg')
        
    def test_upload_single_photo(self):
        """Test uploading a single photo to a location"""
        self.client.force_authenticate(user=self.user)
        
        test_image = self.create_test_image()
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
            {
                'image': test_image,
                'caption': 'Night sky view from the main telescope'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Verify response data
        self.assertEqual(data['location'], self.location.id)
        self.assertEqual(data['uploaded_by'], 'photographer')
        self.assertEqual(data['caption'], 'Night sky view from the main telescope')
        self.assertFalse(data['is_primary'])  # Default should be False
        self.assertTrue(data['is_approved'])  # Auto-approved by default
        
        # Verify database
        photo = LocationPhoto.objects.get(id=data['id'])
        self.assertEqual(photo.location, self.location)
        self.assertEqual(photo.uploaded_by, self.user)
        
    def test_upload_without_authentication(self):
        """Test that unauthenticated users cannot upload photos"""
        test_image = self.create_test_image()
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
            {'image': test_image},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_upload_without_image(self):
        """Test error when no image file provided"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
            {'caption': 'No image here'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No image file provided', response.json()['detail'])
        
    def test_upload_multiple_photos(self):
        """Test uploading multiple photos to same location"""
        self.client.force_authenticate(user=self.user)
        
        # Upload 3 photos
        for i in range(3):
            test_image = self.create_test_image(f'test{i}.jpg')
            response = self.client.post(
                f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
                {
                    'image': test_image,
                    'caption': f'Photo {i}'
                },
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
        # Verify all photos were created
        self.assertEqual(LocationPhoto.objects.filter(location=self.location).count(), 3)
        
    def test_upload_with_primary_flag(self):
        """Test uploading a photo marked as primary"""
        self.client.force_authenticate(user=self.user)
        
        test_image = self.create_test_image()
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
            {
                'image': test_image,
                'caption': 'Primary photo',
                'is_primary': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertTrue(data['is_primary'])
        
        # Verify in database
        photo = LocationPhoto.objects.get(id=data['id'])
        self.assertTrue(photo.is_primary)


class PrimaryPhotoTest(TestCase):
    """Test primary photo designation and management"""
    
    def setUp(self):
        """Set up test data with multiple photos"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='owner', password='pass123')
        self.other_user = User.objects.create_user(username='contributor', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Multi-photo Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Create test photos
        self.photo1 = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='test1.jpg',
            caption='First photo',
            is_primary=True
        )
        
        self.photo2 = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.other_user,
            image='test2.jpg',
            caption='Second photo',
            is_primary=False
        )
        
        self.photo3 = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='test3.jpg',
            caption='Third photo',
            is_primary=False
        )
        
    def test_only_one_primary_photo(self):
        """Test that only one photo can be primary at a time"""
        # Initially photo1 is primary
        self.assertTrue(self.photo1.is_primary)
        
        # Make photo2 primary
        self.photo2.is_primary = True
        self.photo2.save()
        
        # Refresh photo1 and check it's no longer primary
        self.photo1.refresh_from_db()
        self.assertFalse(self.photo1.is_primary)
        self.assertTrue(self.photo2.is_primary)
        
    def test_set_primary_photo_endpoint(self):
        """Test the set_primary_photo API endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/set_primary_photo/',
            {'photo_id': self.photo3.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify photo3 is now primary
        self.photo3.refresh_from_db()
        self.assertTrue(self.photo3.is_primary)
        
        # Verify photo1 is no longer primary
        self.photo1.refresh_from_db()
        self.assertFalse(self.photo1.is_primary)
        
    def test_set_primary_photo_permission_uploader(self):
        """Test that photo uploader can set their photo as primary"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/set_primary_photo/',
            {'photo_id': self.photo2.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.photo2.refresh_from_db()
        self.assertTrue(self.photo2.is_primary)
        
    def test_set_primary_photo_permission_denied(self):
        """Test that users cannot set others' photos as primary unless location owner"""
        third_user = User.objects.create_user(username='third', password='pass123')
        self.client.force_authenticate(user=third_user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/set_primary_photo/',
            {'photo_id': self.photo2.id},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_set_nonexistent_photo_as_primary(self):
        """Test error handling for nonexistent photo"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/set_primary_photo/',
            {'photo_id': 999999},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_set_primary_without_photo_id(self):
        """Test error when photo_id not provided"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/set_primary_photo/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo_id is required', response.json()['detail'])


class PhotoPermissionsTest(TestCase):
    """Test access control for photo operations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.contributor = User.objects.create_user(username='contributor', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Permission Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.owner
        )
        
        # Create approved and unapproved photos
        self.approved_photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.contributor,
            image='approved.jpg',
            is_approved=True
        )
        
        self.unapproved_photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.contributor,
            image='unapproved.jpg',
            is_approved=False
        )
        
    def test_anyone_can_upload_photos(self):
        """Test that any authenticated user can upload photos"""
        random_user = User.objects.create_user(username='random', password='pass123')
        self.client.force_authenticate(user=random_user)
        
        # Create test image
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'blue')
        image.save(file, 'JPEG')
        file.seek(0)
        test_image = SimpleUploadedFile('test.jpg', file.getvalue())
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/upload_photo/',
            {'image': test_image},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_only_approved_photos_shown_publicly(self):
        """Test that only approved photos are shown in public listing"""
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/photos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should only show approved photo
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.approved_photo.id)


class PhotoListingTest(TestCase):
    """Test photo retrieval and filtering"""
    
    def setUp(self):
        """Set up test data with multiple photos"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Photo Gallery Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Create photos with different properties
        self.primary_photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='primary.jpg',
            caption='Primary photo',
            is_primary=True,
            is_approved=True
        )
        
        self.recent_photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='recent.jpg',
            caption='Recent photo',
            is_primary=False,
            is_approved=True
        )
        
        self.old_photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='old.jpg',
            caption='Old photo',
            is_primary=False,
            is_approved=True
        )
        # Manually set created_at to be older
        self.old_photo.created_at = self.old_photo.created_at.replace(year=2020)
        self.old_photo.save()
        
    def test_get_all_location_photos(self):
        """Test retrieving all photos for a location"""
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/photos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 3)
        
        # Verify ordering (primary first, then by created_at desc)
        self.assertEqual(data[0]['id'], self.primary_photo.id)
        self.assertTrue(data[0]['is_primary'])
        
    def test_location_includes_primary_photo(self):
        """Test that location detail includes primary photo"""
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check primary_photo field
        self.assertIsNotNone(data.get('primary_photo'))
        self.assertEqual(data['primary_photo']['id'], self.primary_photo.id)
        
        # Check photos array
        self.assertEqual(len(data['photos']), 3)
        
    def test_location_without_photos(self):
        """Test location with no photos"""
        empty_location = ViewingLocation.objects.create(
            name='No Photos Location',
            latitude=41.0,
            longitude=-106.0,
            added_by=self.user
        )
        
        response = self.client.get(f'/api/v1/viewing-locations/{empty_location.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIsNone(data['primary_photo'])
        self.assertEqual(len(data['photos']), 0)


class PhotoMetadataTest(TestCase):
    """Test EXIF data and metadata handling"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='photographer', password='pass123')
        
        self.location = ViewingLocation.objects.create(
            name='Metadata Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_photo_file_path_generation(self):
        """Test that photo files are stored in correct path structure"""
        photo = LocationPhoto(
            location=self.location,
            uploaded_by=self.user,
            image='test.jpg'
        )
        
        # Test the path function
        from stars_app.models.locationphoto import location_photo_path
        path = location_photo_path(photo, 'myimage.jpg')
        
        # Should be in format: location_photos/{location_id}/{uuid}.jpg
        self.assertTrue(path.startswith(f'location_photos/{self.location.id}/'))
        self.assertTrue(path.endswith('.jpg'))
        self.assertNotIn('myimage', path)  # Original name should be replaced
        
    def test_photo_metadata_fields(self):
        """Test metadata fields on photo model"""
        self.client.force_authenticate(user=self.user)
        
        # Create photo with metadata
        photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='test.jpg',
            caption='Test with metadata',
            camera_make='Canon',
            camera_model='EOS R5',
            taken_at='2024-01-15T20:00:00Z'
        )
        
        # Retrieve via API
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/photos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        photo_data = data[0]
        self.assertEqual(photo_data['camera_make'], 'Canon')
        self.assertEqual(photo_data['camera_model'], 'EOS R5')
        self.assertEqual(photo_data['taken_at'], '2024-01-15T20:00:00Z')
        
    def test_image_url_field(self):
        """Test that image_url property works correctly"""
        photo = LocationPhoto.objects.create(
            location=self.location,
            uploaded_by=self.user,
            image='photos/test.jpg',
            caption='URL test'
        )
        
        # The image_url property should return the URL
        self.assertIsNotNone(photo.image_url)
        self.assertIn('photos/test.jpg', photo.image_url)