"""
Test Suite for Community Moderation System
=========================================

This test module validates the community moderation functionality including:
- Report submission for various issues
- Report types (duplicate, inaccurate, spam, etc.)
- Unique constraint preventing spam reports
- Admin-only report viewing
- Report status tracking
- Integration with location times_reported counter

How to run these tests:
----------------------
# Run all community moderation tests:
python manage.py test stars_app.tests.checkpoint2.1.test_08_community_moderation

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_08_community_moderation.ReportSubmissionTest

# Run with specific test method:
python manage.py test stars_app.tests.checkpoint2.1.test_08_community_moderation.ReportSubmissionTest.test_submit_inaccurate_report

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_08_community_moderation
coverage report

Test Categories:
---------------
1. ReportSubmissionTest - Tests submitting various report types
2. ReportTypesTest - Tests different report type behaviors
3. UniqueConstraintTest - Tests spam prevention mechanisms
4. AdminReportViewingTest - Tests admin access to reports
5. ReportWorkflowTest - Tests complete reporting workflow

Requirements:
------------
- Django test framework
- Authenticated users for report submission
- Admin users for report management
- LocationReport model with unique constraints
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import ViewingLocation, LocationReport
from django.utils import timezone
from datetime import datetime


class ReportSubmissionTest(TestCase):
    """Test submitting reports about locations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='reporter', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        self.location = ViewingLocation.objects.create(
            name='Problematic Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_submit_inaccurate_report(self):
        """Test submitting a report about inaccurate information"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'The coordinates are off by 2km. Actual location is further north.'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Verify response data
        self.assertEqual(data['report_type'], 'INACCURATE')
        self.assertEqual(data['location'], self.location.id)
        self.assertEqual(data['reported_by'], 'reporter')
        self.assertEqual(data['status'], 'PENDING')
        self.assertEqual(data['description'], 'The coordinates are off by 2km. Actual location is further north.')
        
        # Verify database
        report = LocationReport.objects.get(id=data['id'])
        self.assertEqual(report.location, self.location)
        self.assertEqual(report.reported_by, self.user)
        
        # Verify times_reported was incremented
        self.location.refresh_from_db()
        self.assertEqual(self.location.times_reported, 1)
        
    def test_submit_report_without_authentication(self):
        """Test that unauthenticated users cannot submit reports"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'SPAM',
                'description': 'This is spam'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_submit_report_missing_required_fields(self):
        """Test error when required fields are missing"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'description': 'Missing report type'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_submit_report_invalid_type(self):
        """Test error when invalid report type provided"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INVALID_TYPE',
                'description': 'Invalid report type'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_times_reported_increments(self):
        """Test that times_reported counter increments with each report"""
        initial_count = self.location.times_reported
        
        # Submit multiple reports from different users
        for i in range(3):
            user = User.objects.create_user(username=f'user{i}', password='pass123')
            self.client.force_authenticate(user=user)
            
            response = self.client.post(
                f'/api/v1/viewing-locations/{self.location.id}/report/',
                {
                    'report_type': 'INACCURATE',
                    'description': f'Report {i}'
                },
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
        self.location.refresh_from_db()
        self.assertEqual(self.location.times_reported, initial_count + 3)


class ReportTypesTest(TestCase):
    """Test different report type behaviors"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='reporter', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        self.location = ViewingLocation.objects.create(
            name='Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Create another location for duplicate reports
        self.other_location = ViewingLocation.objects.create(
            name='Other Location',
            latitude=40.001,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_duplicate_report_type(self):
        """Test DUPLICATE report type with duplicate_of field"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'DUPLICATE',
                'description': 'Same location as the other one',
                'duplicate_of_id': self.other_location.id
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['duplicate_of'], self.other_location.id)
        self.assertEqual(data['duplicate_of_name'], self.other_location.name)
        
    def test_spam_report_type(self):
        """Test SPAM report type"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'SPAM',
                'description': 'This is a fake location promoting a business'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['report_type'], 'SPAM')
        
    def test_closed_report_type(self):
        """Test CLOSED report type for inaccessible locations"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'CLOSED',
                'description': 'Gate is permanently locked. No public access anymore.'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['report_type'], 'CLOSED')
        
    def test_dangerous_report_type(self):
        """Test DANGEROUS report type for safety concerns"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'DANGEROUS',
                'description': 'Steep cliff with no barriers. Several accidents reported.'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['report_type'], 'DANGEROUS')
        
    def test_other_report_type(self):
        """Test OTHER report type for miscellaneous issues"""
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'OTHER',
                'description': 'Parking lot is often full. Suggest arriving early.'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['report_type'], 'OTHER')


class UniqueConstraintTest(TestCase):
    """Test spam prevention through unique constraints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='reporter', password='pass123')
        self.client.force_authenticate(user=self.user)
        
        self.location = ViewingLocation.objects.create(
            name='Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
    def test_cannot_submit_duplicate_report_type(self):
        """Test that users cannot submit same report type twice for same location"""
        # First report
        response1 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'First report'
            },
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second report with same type
        response2 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'Second report - should fail'
            },
            format='json'
        )
        
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already submitted this type of report', response2.json()['detail'])
        
    def test_can_submit_different_report_types(self):
        """Test that users can submit different report types for same location"""
        # Submit INACCURATE report
        response1 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'Coordinates are wrong'
            },
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Submit DANGEROUS report for same location
        response2 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'DANGEROUS',
                'description': 'Unsafe conditions'
            },
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both reports exist
        reports = LocationReport.objects.filter(location=self.location, reported_by=self.user)
        self.assertEqual(reports.count(), 2)
        
    def test_different_users_can_report_same_type(self):
        """Test that different users can submit same report type"""
        # First user report
        response1 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'User 1 report'
            },
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second user report
        user2 = User.objects.create_user(username='user2', password='pass123')
        self.client.force_authenticate(user=user2)
        
        response2 = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'User 2 report'
            },
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both reports exist
        reports = LocationReport.objects.filter(location=self.location, report_type='INACCURATE')
        self.assertEqual(reports.count(), 2)


class AdminReportViewingTest(TestCase):
    """Test admin access to reports"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.regular_user = User.objects.create_user(username='regular', password='pass123')
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        
        self.location = ViewingLocation.objects.create(
            name='Reported Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.regular_user
        )
        
        # Create some reports
        self.report1 = LocationReport.objects.create(
            location=self.location,
            reported_by=self.regular_user,
            report_type='INACCURATE',
            description='Wrong coordinates',
            status='PENDING'
        )
        
        self.report2 = LocationReport.objects.create(
            location=self.location,
            reported_by=self.regular_user,
            report_type='DANGEROUS',
            description='Safety hazard',
            status='REVIEWED',
            reviewed_by=self.admin_user,
            review_notes='Confirmed hazard exists',
            reviewed_at=timezone.now()
        )
        
    def test_admin_can_view_all_reports(self):
        """Test that admin users can view all reports for a location"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 2)
        
        # Check report details
        report_types = [report['report_type'] for report in data]
        self.assertIn('INACCURATE', report_types)
        self.assertIn('DANGEROUS', report_types)
        
        # Check reviewed report has additional info
        reviewed_report = next(r for r in data if r['report_type'] == 'DANGEROUS')
        self.assertEqual(reviewed_report['status'], 'REVIEWED')
        self.assertEqual(reviewed_report['reviewed_by'], 'admin')
        self.assertIsNotNone(reviewed_report['review_notes'])
        self.assertIsNotNone(reviewed_report['reviewed_at'])
        
    def test_regular_user_cannot_view_reports(self):
        """Test that regular users cannot view reports"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('do not have permission', response.json()['detail'])
        
    def test_unauthenticated_cannot_view_reports(self):
        """Test that unauthenticated users cannot view reports"""
        self.client.force_authenticate(user=None)
        
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReportWorkflowTest(TestCase):
    """Test complete reporting workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.reporter = User.objects.create_user(username='reporter', password='pass123')
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        
        self.location = ViewingLocation.objects.create(
            name='Workflow Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.reporter
        )
        
    def test_complete_report_lifecycle(self):
        """Test complete lifecycle from report submission to resolution"""
        # Step 1: User submits report
        self.client.force_authenticate(user=self.reporter)
        
        response = self.client.post(
            f'/api/v1/viewing-locations/{self.location.id}/report/',
            {
                'report_type': 'INACCURATE',
                'description': 'GPS coordinates are 500m off'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.json()['id']
        
        # Step 2: Verify report is pending
        report = LocationReport.objects.get(id=report_id)
        self.assertEqual(report.status, 'PENDING')
        self.assertIsNone(report.reviewed_by)
        self.assertIsNone(report.reviewed_at)
        
        # Step 3: Admin reviews report
        report.status = 'REVIEWED'
        report.reviewed_by = self.admin
        report.review_notes = 'Verified coordinates are incorrect'
        report.reviewed_at = timezone.now()
        report.save()
        
        # Step 4: Admin marks as resolved after fixing
        report.status = 'RESOLVED'
        report.review_notes += '\nCorrected coordinates in system.'
        report.save()
        
        # Step 5: Verify final state
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/v1/viewing-locations/{self.location.id}/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resolved_report = response.json()[0]
        
        self.assertEqual(resolved_report['status'], 'RESOLVED')
        self.assertIn('Corrected coordinates', resolved_report['review_notes'])
        
    def test_report_status_options(self):
        """Test all possible report statuses"""
        statuses_and_types = [
            ('PENDING', 'DUPLICATE'),
            ('REVIEWED', 'INACCURATE'),
            ('RESOLVED', 'SPAM'),
            ('DISMISSED', 'OTHER'),
        ]
        
        for status, report_type in statuses_and_types:
            report = LocationReport.objects.create(
                location=self.location,
                reported_by=self.reporter,
                report_type=report_type,
                description=f'Test {status}',
                status=status
            )
            
            self.assertEqual(report.status, status)
            
    def test_highly_reported_location_filtering(self):
        """Test finding locations with many reports"""
        # Create multiple reports
        for i in range(5):
            user = User.objects.create_user(username=f'reporter{i}', password='pass123')
            LocationReport.objects.create(
                location=self.location,
                reported_by=user,
                report_type='INACCURATE',
                description=f'Report {i}'
            )
            self.location.times_reported += 1
            self.location.save()
            
        # Filter for highly reported locations
        highly_reported = ViewingLocation.objects.filter(times_reported__gte=5)
        self.assertIn(self.location, highly_reported)