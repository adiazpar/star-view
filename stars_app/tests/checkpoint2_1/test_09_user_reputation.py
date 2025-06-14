"""
Test Suite for User Reputation System
====================================

This test module validates the user reputation functionality including:
- Reputation score calculation algorithm
- Points for various contributions
- Trusted contributor status
- Reputation field tracking
- Management command for updates
- Integration with user activities

How to run these tests:
----------------------
# Run all reputation tests:
python manage.py test stars_app.tests.checkpoint2.1.test_09_user_reputation

# Run a specific test class:
python manage.py test stars_app.tests.checkpoint2.1.test_09_user_reputation.ReputationCalculationTest

# Run with specific test method:
python manage.py test stars_app.tests.checkpoint2.1.test_09_user_reputation.ReputationCalculationTest.test_points_for_adding_locations

# Run with coverage:
coverage run --source='.' manage.py test stars_app.tests.checkpoint2.1.test_09_user_reputation
coverage report

Test Categories:
---------------
1. ReputationFieldsTest - Tests reputation fields on UserProfile
2. ReputationCalculationTest - Tests point calculation algorithm
3. TrustedContributorTest - Tests trusted status threshold
4. ReputationTrackingTest - Tests reputation tracking fields
5. ManagementCommandTest - Tests update_reputation command

Requirements:
------------
- Django test framework
- UserProfile with reputation fields
- Various contribution models (locations, reviews, photos, tags)
- Management command for reputation updates
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from stars_app.models import (
    UserProfile, ViewingLocation, LocationReview, 
    ReviewVote, LocationPhoto, LocationTag
)
from io import StringIO
import sys


class ReputationFieldsTest(TestCase):
    """Test reputation fields on UserProfile model"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile = self.user.userprofile
        
    def test_default_reputation_values(self):
        """Test that new users have correct default reputation values"""
        self.assertEqual(self.profile.reputation_score, 0)
        self.assertEqual(self.profile.verified_locations_count, 0)
        self.assertEqual(self.profile.helpful_reviews_count, 0)
        self.assertEqual(self.profile.quality_photos_count, 0)
        self.assertFalse(self.profile.is_trusted_contributor)
        
    def test_reputation_fields_in_serializer(self):
        """Test that reputation fields are included in API response"""
        client = APIClient()
        
        # Get user profile via API
        response = client.get(f'/api/v1/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        profile_data = response.json()['profile']
        self.assertIn('reputation_score', profile_data)
        self.assertIn('verified_locations_count', profile_data)
        self.assertIn('helpful_reviews_count', profile_data)
        self.assertIn('quality_photos_count', profile_data)
        self.assertIn('is_trusted_contributor', profile_data)


class ReputationCalculationTest(TestCase):
    """Test reputation score calculation algorithm"""
    
    def setUp(self):
        """Create test users and data"""
        self.user = User.objects.create_user(username='contributor', password='pass123')
        self.profile = self.user.userprofile
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.other_user = User.objects.create_user(username='other', password='pass123')
        
    def test_points_for_adding_locations(self):
        """Test 10 points per location added"""
        # Add 3 locations
        for i in range(3):
            ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 30)  # 3 locations * 10 points
        
    def test_bonus_points_for_verified_locations(self):
        """Test 20 bonus points for verified locations"""
        # Create 2 regular and 1 verified location
        for i in range(2):
            ViewingLocation.objects.create(
                name=f'Regular Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            
        ViewingLocation.objects.create(
            name='Verified Location',
            latitude=42.0,
            longitude=-105.0,
            added_by=self.user,
            is_verified=True,
            verified_by=self.admin
        )
        
        score = self.profile.calculate_reputation()
        # 3 locations * 10 = 30, plus 1 verified * 20 = 20, total 50
        self.assertEqual(score, 50)
        self.assertEqual(self.profile.verified_locations_count, 1)
        
    def test_points_for_reviews(self):
        """Test 5 points per review written"""
        location = ViewingLocation.objects.create(
            name='Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.other_user
        )
        
        # Write 2 reviews
        for i in range(2):
            other_location = ViewingLocation.objects.create(
                name=f'Other Location {i}',
                latitude=41.0 + i,
                longitude=-106.0,
                added_by=self.other_user
            )
            LocationReview.objects.create(
                location=other_location,
                user=self.user,
                rating=4,
                comment=f'Review {i}'
            )
            
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 10)  # 2 reviews * 5 points
        
    def test_points_for_helpful_reviews(self):
        """Test 2 points per net upvote on reviews"""
        location = ViewingLocation.objects.create(
            name='Test Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.other_user
        )
        
        # Create review
        review = LocationReview.objects.create(
            location=location,
            user=self.user,
            rating=5,
            comment='Great location!'
        )
        
        # Add upvotes from other users
        for i in range(3):
            voter = User.objects.create_user(username=f'voter{i}', password='pass123')
            ReviewVote.objects.create(
                review=review,
                user=voter,
                is_upvote=True
            )
            
        # Add 1 downvote
        downvoter = User.objects.create_user(username='downvoter', password='pass123')
        ReviewVote.objects.create(
            review=review,
            user=downvoter,
            is_upvote=False
        )
        
        score = self.profile.calculate_reputation()
        # 1 review * 5 = 5, plus (3 upvotes - 1 downvote) * 2 = 4, total 9
        self.assertEqual(score, 9)
        self.assertEqual(self.profile.helpful_reviews_count, 1)
        
    def test_points_for_photos(self):
        """Test 8 points per approved photo"""
        location = ViewingLocation.objects.create(
            name='Photo Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.other_user
        )
        
        # Upload 3 approved photos
        for i in range(3):
            LocationPhoto.objects.create(
                location=location,
                uploaded_by=self.user,
                image=f'photo{i}.jpg',
                is_approved=True
            )
            
        # Upload 1 unapproved photo (shouldn't count)
        LocationPhoto.objects.create(
            location=location,
            uploaded_by=self.user,
            image='unapproved.jpg',
            is_approved=False
        )
        
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 24)  # 3 approved photos * 8 points
        self.assertEqual(self.profile.quality_photos_count, 3)
        
    def test_points_for_approved_tags(self):
        """Test 15 points per approved tag created"""
        # Create 2 approved tags
        for i in range(2):
            LocationTag.objects.create(
                name=f'Approved Tag {i}',
                slug=f'approved-tag-{i}',
                created_by=self.user,
                is_approved=True
            )
            
        # Create 1 unapproved tag (shouldn't count)
        LocationTag.objects.create(
            name='Unapproved Tag',
            slug='unapproved-tag',
            created_by=self.user,
            is_approved=False
        )
        
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 30)  # 2 approved tags * 15 points
        
    def test_complete_reputation_calculation(self):
        """Test calculation with all contribution types"""
        # Add location (10 points)
        location1 = ViewingLocation.objects.create(
            name='My Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.user
        )
        
        # Add verified location (10 + 20 = 30 points)
        location2 = ViewingLocation.objects.create(
            name='My Verified Location',
            latitude=41.0,
            longitude=-106.0,
            added_by=self.user,
            is_verified=True
        )
        
        # Write review (5 points)
        other_location = ViewingLocation.objects.create(
            name='Other Location',
            latitude=42.0,
            longitude=-107.0,
            added_by=self.other_user
        )
        review = LocationReview.objects.create(
            location=other_location,
            user=self.user,
            rating=5,
            comment='Great!'
        )
        
        # Get 2 upvotes (2 * 2 = 4 points)
        for i in range(2):
            voter = User.objects.create_user(username=f'voter{i}', password='pass123')
            ReviewVote.objects.create(review=review, user=voter, is_upvote=True)
            
        # Upload photo (8 points)
        LocationPhoto.objects.create(
            location=location1,
            uploaded_by=self.user,
            image='photo.jpg',
            is_approved=True
        )
        
        # Create approved tag (15 points)
        LocationTag.objects.create(
            name='My Tag',
            slug='my-tag',
            created_by=self.user,
            is_approved=True
        )
        
        score = self.profile.calculate_reputation()
        # Total: 10 + 30 + 5 + 4 + 8 + 15 = 72
        self.assertEqual(score, 72)


class TrustedContributorTest(TestCase):
    """Test trusted contributor status threshold"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(username='contributor', password='pass123')
        self.profile = self.user.userprofile
        
    def test_not_trusted_below_threshold(self):
        """Test user is not trusted contributor below 100 points"""
        # Add enough for 90 points (9 locations)
        for i in range(9):
            ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 90)
        self.assertFalse(self.profile.is_trusted_contributor)
        
    def test_trusted_at_threshold(self):
        """Test user becomes trusted contributor at 100 points"""
        # Add enough for exactly 100 points (10 locations)
        for i in range(10):
            ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 100)
        self.assertTrue(self.profile.is_trusted_contributor)
        
    def test_trusted_above_threshold(self):
        """Test user remains trusted contributor above 100 points"""
        # Add enough for 150 points
        for i in range(15):
            ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user
            )
            
        score = self.profile.calculate_reputation()
        self.assertEqual(score, 150)
        self.assertTrue(self.profile.is_trusted_contributor)


class ReputationTrackingTest(TestCase):
    """Test reputation tracking fields update correctly"""
    
    def setUp(self):
        """Create test user and data"""
        self.user = User.objects.create_user(username='tracker', password='pass123')
        self.profile = self.user.userprofile
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        
    def test_verified_locations_count(self):
        """Test verified_locations_count tracking"""
        # Create mix of verified and unverified locations
        for i in range(3):
            ViewingLocation.objects.create(
                name=f'Unverified {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user,
                is_verified=False
            )
            
        for i in range(2):
            ViewingLocation.objects.create(
                name=f'Verified {i}',
                latitude=41.0 + i,
                longitude=-106.0,
                added_by=self.user,
                is_verified=True,
                verified_by=self.admin
            )
            
        self.profile.calculate_reputation()
        self.assertEqual(self.profile.verified_locations_count, 2)
        
    def test_helpful_reviews_count(self):
        """Test helpful_reviews_count tracking"""
        # Create locations for reviews
        locations = []
        for i in range(3):
            loc = ViewingLocation.objects.create(
                name=f'Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.admin
            )
            locations.append(loc)
            
        # Create reviews with different vote patterns
        # Review 1: 3 upvotes, 1 downvote (helpful)
        review1 = LocationReview.objects.create(
            location=locations[0],
            user=self.user,
            rating=5,
            comment='Great!'
        )
        for i in range(3):
            voter = User.objects.create_user(username=f'up{i}', password='pass123')
            ReviewVote.objects.create(review=review1, user=voter, is_upvote=True)
        downvoter = User.objects.create_user(username='down1', password='pass123')
        ReviewVote.objects.create(review=review1, user=downvoter, is_upvote=False)
        
        # Review 2: 1 upvote, 2 downvotes (not helpful)
        review2 = LocationReview.objects.create(
            location=locations[1],
            user=self.user,
            rating=3,
            comment='OK'
        )
        upvoter = User.objects.create_user(username='up_single', password='pass123')
        ReviewVote.objects.create(review=review2, user=upvoter, is_upvote=True)
        for i in range(2):
            voter = User.objects.create_user(username=f'down{i+2}', password='pass123')
            ReviewVote.objects.create(review=review2, user=voter, is_upvote=False)
            
        # Review 3: No votes (not helpful)
        LocationReview.objects.create(
            location=locations[2],
            user=self.user,
            rating=4,
            comment='Nice'
        )
        
        self.profile.calculate_reputation()
        self.assertEqual(self.profile.helpful_reviews_count, 1)  # Only review1 is helpful
        
    def test_quality_photos_count(self):
        """Test quality_photos_count tracking"""
        location = ViewingLocation.objects.create(
            name='Photo Location',
            latitude=40.0,
            longitude=-105.0,
            added_by=self.admin
        )
        
        # Create mix of approved and unapproved photos
        for i in range(4):
            LocationPhoto.objects.create(
                location=location,
                uploaded_by=self.user,
                image=f'approved{i}.jpg',
                is_approved=True
            )
            
        for i in range(2):
            LocationPhoto.objects.create(
                location=location,
                uploaded_by=self.user,
                image=f'unapproved{i}.jpg',
                is_approved=False
            )
            
        self.profile.calculate_reputation()
        self.assertEqual(self.profile.quality_photos_count, 4)


class ManagementCommandTest(TestCase):
    """Test update_reputation management command"""
    
    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        
        # Give users some contributions
        for i in range(5):
            ViewingLocation.objects.create(
                name=f'User1 Location {i}',
                latitude=40.0 + i,
                longitude=-105.0,
                added_by=self.user1
            )
            
        for i in range(3):
            ViewingLocation.objects.create(
                name=f'User2 Location {i}',
                latitude=41.0 + i,
                longitude=-106.0,
                added_by=self.user2
            )
            
    def test_update_all_users(self):
        """Test updating reputation for all users"""
        # Capture command output
        out = StringIO()
        call_command('update_reputation', stdout=out)
        output = out.getvalue()
        
        # Check output mentions updates
        self.assertIn('Successfully updated', output)
        
        # Verify scores were calculated
        self.user1.userprofile.refresh_from_db()
        self.user2.userprofile.refresh_from_db()
        
        self.assertEqual(self.user1.userprofile.reputation_score, 50)  # 5 locations * 10
        self.assertEqual(self.user2.userprofile.reputation_score, 30)  # 3 locations * 10
        
    def test_update_specific_user(self):
        """Test updating reputation for specific user"""
        out = StringIO()
        call_command('update_reputation', user='user1', stdout=out)
        output = out.getvalue()
        
        # Check only user1 was updated
        self.assertIn('user1', output)
        self.assertNotIn('user2', output)
        
        # Verify only user1's score was updated
        self.user1.userprofile.refresh_from_db()
        self.assertEqual(self.user1.userprofile.reputation_score, 50)
        
        # user2 should still have default score
        self.user2.userprofile.refresh_from_db()
        self.assertEqual(self.user2.userprofile.reputation_score, 0)
        
    def test_update_nonexistent_user(self):
        """Test error handling for nonexistent user"""
        out = StringIO()
        err = StringIO()
        
        call_command('update_reputation', user='nonexistent', stdout=out, stderr=err)
        
        error_output = err.getvalue()
        self.assertIn('User nonexistent not found', error_output)
        
    def test_reputation_persistence(self):
        """Test that reputation scores persist after calculation"""
        # Calculate initial scores
        call_command('update_reputation')
        
        # Get initial scores
        self.user1.userprofile.refresh_from_db()
        initial_score = self.user1.userprofile.reputation_score
        
        # Add more contributions
        ViewingLocation.objects.create(
            name='New Location',
            latitude=45.0,
            longitude=-110.0,
            added_by=self.user1
        )
        
        # Update again
        call_command('update_reputation')
        
        # Verify score increased
        self.user1.userprofile.refresh_from_db()
        new_score = self.user1.userprofile.reputation_score
        
        self.assertEqual(new_score, initial_score + 10)