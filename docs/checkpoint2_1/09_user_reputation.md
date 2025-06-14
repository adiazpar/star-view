# User Reputation System

## Overview
This document details the implementation of a comprehensive user reputation system that tracks and rewards quality contributions to the platform. The system encourages positive behavior and helps identify trusted contributors.

## Why User Reputation Was Needed

### Previous State
- No recognition for quality contributors
- All users treated equally regardless of contribution
- No incentive for quality content
- Difficult to identify trusted users
- No gamification elements

### Problems Solved
- **Trust Issues**: No way to identify reliable contributors
- **Quality Incentive**: No reward for good contributions
- **Spam Prevention**: Spammers had same weight as quality users
- **Community Building**: No recognition system
- **Moderation Help**: Hard to identify who to trust

## Implementation Details

### UserProfile Model Additions

```python
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
```

### Reputation Calculation Algorithm

```python
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
    
    # Update counts and status
    self.verified_locations_count = verified_locations
    self.helpful_reviews_count = helpful_reviews
    self.quality_photos_count = photos
    self.reputation_score = score
    
    # Check if user should be trusted contributor (score >= 100)
    self.is_trusted_contributor = score >= 100
    
    return score
```

### Point System

| Action | Points | Description |
|--------|--------|-------------|
| Add Location | 10 | Each location added |
| Verified Location | 20 | Bonus when location verified |
| Write Review | 5 | Each review written |
| Helpful Review | 2 per net upvote | Upvotes minus downvotes |
| Upload Photo | 8 | Each approved photo |
| Create Tag | 15 | Each approved tag |

### Management Command

```python
class Command(BaseCommand):
    help = 'Update reputation scores for all users'
    
    def handle(self, *args, **options):
        for user in users:
            profile, created = UserProfile.objects.get_or_create(user=user)
            old_score = profile.reputation_score
            new_score = profile.calculate_reputation()
            profile.save()
            
            if old_score != new_score:
                self.stdout.write(
                    f'Updated {user.username}: {old_score} -> {new_score} '
                    f'(Trusted: {profile.is_trusted_contributor})'
                )
```

## Usage Examples

### Update All User Reputations
```bash
python manage.py update_reputation
```

### Update Specific User
```bash
python manage.py update_reputation --user john_doe
```

### View User Profile with Reputation
```bash
GET /api/v1/users/123/
```

Response:
```json
{
    "id": 123,
    "username": "john_doe",
    "profile": {
        "reputation_score": 245,
        "verified_locations_count": 5,
        "helpful_reviews_count": 12,
        "quality_photos_count": 15,
        "is_trusted_contributor": true,
        "created_at": "2023-01-15T10:00:00Z"
    }
}
```

## Trust Levels

### New User (0-25 points)
- Basic permissions
- Can add locations
- Can write reviews
- Learning the platform

### Active Contributor (26-99 points)
- All new user permissions
- Reviews carry more weight
- Can create tags
- Bulk import access (future)

### Trusted Contributor (100+ points)
- All previous permissions
- Automatic tag approval
- Priority support
- Moderation capabilities (future)
- Special badge/recognition

## Benefits

### For Users
- Recognition for contributions
- Gamification elements
- Clear progression path
- Community status

### For Platform Quality
- Incentivizes quality content
- Identifies reliable users
- Weights contributions by trust
- Reduces spam impact

### For Community
- Builds engaged user base
- Creates mentorship opportunities
- Recognizes valuable members
- Encourages participation

## Display and Recognition

### Profile Display
```python
class UserProfileSerializer(serializers.ModelSerializer):
    fields = [
        'reputation_score', 
        'verified_locations_count', 
        'helpful_reviews_count',
        'quality_photos_count', 
        'is_trusted_contributor'
    ]
```

### Visual Indicators
- Badge next to username
- Special profile border
- "Trusted Contributor" label
- Reputation score display

## Automatic Updates

### When to Recalculate
1. Location added/removed
2. Location verified
3. Review posted
4. Review voted on
5. Photo approved
6. Tag approved

### Update Strategies
- Batch updates via cron
- Real-time for key actions
- Weekly full recalculation
- On-demand via API

## Integration with Other Features

### Search and Filtering
```python
# Filter locations by trusted contributors
GET /api/v1/locations/?added_by_trusted=true
```

### Weighted Reviews
```python
# Reviews from trusted users count more
if review.user.userprofile.is_trusted_contributor:
    weight = 1.5
else:
    weight = 1.0
```

### Moderation Priority
- Reports from trusted users prioritized
- Trusted user content auto-approved
- Less likely to be flagged

## Future Enhancements

1. **Badges System**: Specific achievement badges
2. **Leaderboards**: Top contributors by category
3. **Seasonal Points**: Time-based multipliers
4. **Decay System**: Points decay without activity
5. **Specializations**: Expert in specific categories
6. **Mentorship**: Connect new users with trusted ones
7. **Rewards**: Physical/digital rewards for milestones
8. **API Rate Limits**: Higher limits for trusted users

## Preventing Gaming

### Anti-Abuse Measures
- Rate limiting on actions
- Quality checks on contributions
- Suspicious pattern detection
- Manual review triggers

### Quality Over Quantity
- Verified locations worth more
- Helpful reviews weighted
- Approved content only
- Community validation

## Analytics and Reporting

Track reputation metrics:
- Distribution of trust levels
- Average scores by cohort
- Contribution patterns
- Retention by reputation

This system creates a positive feedback loop where quality contributions are recognized and rewarded, leading to better content and a more engaged community.