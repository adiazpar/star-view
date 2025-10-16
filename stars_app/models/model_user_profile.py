from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver
from .model_base import TimestampedModel


# User Profile Model ------------------------------------------------ #
class UserProfile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    
    # Reputation fields
    reputation_score = models.IntegerField(
        default=0,
        help_text="User's reputation score based on contributions"
    )
    verified_locations_count = models.IntegerField(
        default=0,
        help_text="Number of locations verified by this user"
    )
    helpful_reviews_count = models.IntegerField(
        default=0,
        help_text="Number of helpful reviews (based on votes)"
    )
    quality_photos_count = models.IntegerField(
        default=0,
        help_text="Number of approved photos uploaded"
    )
    is_trusted_contributor = models.BooleanField(
        default=False,
        help_text="Whether user is a trusted contributor"
    )

    @property
    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default_profile_pic.jpg'

    def __str__(self):
        return f'{self.user.username} Profile'
    
    def calculate_reputation(self):
        """Calculate user's reputation score based on contributions"""
        score = 0
        
        # Points for adding locations
        locations_added = self.user.viewinglocation_set.count()
        score += locations_added * 10
        
        # Bonus for verified locations
        verified_locations = self.user.viewinglocation_set.filter(is_verified=True).count()
        score += verified_locations * 20
        
        # Points for reviews
        from .model_location_review import LocationReview
        reviews = LocationReview.objects.filter(user=self.user).count()
        score += reviews * 5
        
        # Points for helpful reviews (more upvotes than downvotes)
        helpful_reviews = 0
        for review in LocationReview.objects.filter(user=self.user):
            upvotes = review.votes.filter(is_upvote=True).count()
            downvotes = review.votes.filter(is_upvote=False).count()
            if upvotes > downvotes:
                helpful_reviews += 1
                score += (upvotes - downvotes) * 2
        
        # Points for photos
        photos = self.user.uploaded_photos.filter(is_approved=True).count()
        score += photos * 8
        
        # Points for approved tags
        approved_tags = self.user.created_tags.filter(is_approved=True).count()
        score += approved_tags * 15
        
        # Update counts
        self.verified_locations_count = verified_locations
        self.helpful_reviews_count = helpful_reviews
        self.quality_photos_count = photos
        self.reputation_score = score
        
        # Check if user should be trusted contributor (score > 100)
        self.is_trusted_contributor = score >= 100
        
        return score


# Signal to automatically create/update UserProfile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Get or create profile if it doesn't exist for existing users
        UserProfile.objects.get_or_create(user=instance)
