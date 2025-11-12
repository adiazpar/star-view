# ----------------------------------------------------------------------------------------------------- #
# This model_badge.py file defines the Badge model:                                                     #
#                                                                                                       #
# Purpose:                                                                                              #
# Defines achievement badges that users can earn through various activities (visiting locations,        #
# writing reviews, gaining followers, etc.). Badges gamify user engagement and reward quality           #
# contributions to the stargazing community.                                                            #
#                                                                                                       #
# Key Features:                                                                                         #
# - Global badge definitions (created once, shared by all users)                                        #
# - 7 categories: Exploration, Contribution, Quality, Review, Community, Tenure, Special                #
# - Tiered progression system (1-5 tiers per category)                                                  #
# - Criteria-based unlocking (visit count, review count, follower count, etc.)                          #
# - Icon references for frontend display (/public/badges/{slug}.png)                                    #
# - Color coding for visual distinction                                                                 #
# - Rare badge flag for special/limited achievements                                                    #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models


class Badge(models.Model):
    # Badge categories for organization:
    CATEGORY_CHOICES = [
        ('EXPLORATION', 'Exploration'),      # Visiting locations
        ('CONTRIBUTION', 'Contribution'),    # Adding locations
        ('QUALITY', 'Quality'),              # Well-rated locations
        ('REVIEW', 'Review'),                # Writing reviews
        ('COMMUNITY', 'Community'),          # Social engagement
        ('TENURE', 'Time-Based'),            # Membership duration
        ('SPECIAL', 'Special/Rare'),         # Unique achievements
    ]

    # Criteria types for badge unlocking:
    CRITERIA_TYPES = [
        ('LOCATION_VISITS', 'Location Visits'),
        ('LOCATIONS_ADDED', 'Locations Added'),
        ('LOCATION_RATING', 'Location Quality Rating'),
        ('REVIEWS_WRITTEN', 'Reviews Written'),
        ('UPVOTES_RECEIVED', 'Upvotes Received'),
        ('HELPFUL_RATIO', 'Helpful Review Ratio'),
        ('COMMENTS_WRITTEN', 'Comments Written'),
        ('FOLLOWER_COUNT', 'Follower Count'),
        ('TENURE_DAYS', 'Days as Member'),
        ('SPECIAL_CONDITION', 'Special Condition'),
    ]

    # Basic Info
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)  # For icon filename: {slug}.png
    description = models.TextField()

    # Categorization
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    # Unlock Criteria
    criteria_type = models.CharField(max_length=30, choices=CRITERIA_TYPES)
    criteria_value = models.IntegerField()  # Threshold to unlock (e.g., 5 visits)
    criteria_secondary = models.IntegerField(null=True, blank=True)  # For complex criteria (e.g., helpful ratio %)

    # Display Properties
    tier = models.SmallIntegerField(default=1)  # 1-5 for progression badges
    color = models.CharField(max_length=20, default='blue')  # CSS color or hex
    is_rare = models.BooleanField(default=False)  # Special/limited badges
    icon_path = models.CharField(max_length=255)  # e.g., '/badges/explorer.png'

    # Ordering
    display_order = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'tier', 'display_order']
        indexes = [
            # Composite index covering category + criteria_type + ORDER BY criteria_value
            # This eliminates filesort operation in badge checking queries (25-50% faster)
            models.Index(fields=['category', 'criteria_type', 'criteria_value'], name='badge_query_idx'),
            # Explicit index on slug for faster lookups by slug (Pioneer, Photographer badges)
            models.Index(fields=['slug'], name='badge_slug_idx'),
        ]
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'

    # String representation for admin interface and debugging:
    def __str__(self):
        return f'{self.name} (Tier {self.tier})'
