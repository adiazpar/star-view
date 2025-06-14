from django.db import models
from django.db.models import Q, Avg, Count, Max, Min
from datetime import datetime, timedelta


class ViewingLocationManager(models.Manager):
    """Custom manager for ViewingLocation model with complex queries"""

    def by_quality_score(self, min_score=None):
        """Filter locations by minimum quality score"""
        queryset = self.get_queryset()
        if min_score is not None:
            queryset = queryset.filter(quality_score__gte=min_score)
        return queryset.order_by('-quality_score')

    def near_coordinates(self, latitude, longitude, radius_km=50):
        """Find locations within a radius of given coordinates"""
        # Simple bounding box calculation (for more precise, use PostGIS)
        lat_delta = radius_km / 111.0  # Rough km to degrees
        lng_delta = radius_km / (111.0 * abs(latitude))
        
        return self.get_queryset().filter(
            latitude__range=(latitude - lat_delta, latitude + lat_delta),
            longitude__range=(longitude - lng_delta, longitude + lng_delta)
        )

    def with_good_weather(self, max_cloud_cover=30):
        """Filter locations with good weather conditions"""
        return self.get_queryset().filter(
            Q(cloudCoverPercentage__lte=max_cloud_cover) |
            Q(cloudCoverPercentage__isnull=True)
        )

    def dark_sky_locations(self, min_light_pollution=20):
        """Filter locations with good dark sky conditions"""
        return self.get_queryset().filter(
            light_pollution_value__gte=min_light_pollution
        )

    def with_reviews(self):
        """Get locations that have reviews"""
        return self.get_queryset().annotate(
            review_count=Count('reviews')
        ).filter(review_count__gt=0)

    def top_rated(self, limit=10):
        """Get top rated locations by average rating"""
        return self.with_reviews().annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')[:limit]

    def recently_added(self, days=30):
        """Get recently added locations"""
        since_date = datetime.now() - timedelta(days=days)
        return self.get_queryset().filter(
            created_at__gte=since_date
        ).order_by('-created_at')

    def by_country(self, country):
        """Filter locations by country"""
        return self.get_queryset().filter(country__icontains=country)

    def search(self, query):
        """Search locations by name, address, or country"""
        return self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(formatted_address__icontains=query) |
            Q(locality__icontains=query) |
            Q(administrative_area__icontains=query) |
            Q(country__icontains=query)
        )


class CelestialEventManager(models.Manager):
    """Custom manager for CelestialEvent model"""

    def active_events(self):
        """Get currently active events"""
        now = datetime.now()
        return self.get_queryset().filter(
            start_time__lte=now,
            end_time__gte=now
        )

    def upcoming_events(self, days=30):
        """Get upcoming events within specified days"""
        now = datetime.now()
        end_date = now + timedelta(days=days)
        return self.get_queryset().filter(
            start_time__gte=now,
            start_time__lte=end_date
        ).order_by('start_time')

    def by_type(self, event_type):
        """Filter events by type"""
        return self.get_queryset().filter(event_type=event_type)

    def near_location(self, location, radius_km=100):
        """Find events near a viewing location"""
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * abs(location.latitude))
        
        return self.get_queryset().filter(
            latitude__range=(location.latitude - lat_delta, location.latitude + lat_delta),
            longitude__range=(location.longitude - lng_delta, location.longitude + lng_delta)
        )

    def meteor_showers(self):
        """Get meteor shower events"""
        return self.by_type('METEOR')

    def eclipses(self):
        """Get eclipse events"""
        return self.by_type('ECLIPSE')


class LocationReviewManager(models.Manager):
    """Custom manager for LocationReview model"""

    def recent_reviews(self, days=30):
        """Get recent reviews"""
        since_date = datetime.now() - timedelta(days=days)
        return self.get_queryset().filter(
            created_at__gte=since_date
        ).order_by('-created_at')

    def by_rating(self, min_rating=None, max_rating=None):
        """Filter reviews by rating range"""
        queryset = self.get_queryset()
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_rating is not None:
            queryset = queryset.filter(rating__lte=max_rating)
        return queryset

    def with_comments(self):
        """Get reviews that have comments"""
        return self.get_queryset().exclude(
            Q(comment__isnull=True) | Q(comment__exact='')
        )

    def top_voted(self):
        """Get reviews ordered by vote count"""
        return self.get_queryset().annotate(
            vote_score=Count('votes', filter=Q(votes__is_upvote=True)) -
                      Count('votes', filter=Q(votes__is_upvote=False))
        ).order_by('-vote_score')


class UserProfileManager(models.Manager):
    """Custom manager for UserProfile model"""

    def active_users(self, days=30):
        """Get profiles of users active within specified days"""
        since_date = datetime.now() - timedelta(days=days)
        return self.get_queryset().filter(
            user__last_login__gte=since_date
        )

    def with_profile_pictures(self):
        """Get profiles that have profile pictures"""
        return self.get_queryset().exclude(
            Q(profile_picture__isnull=True) | Q(profile_picture__exact='')
        )

    def top_contributors(self):
        """Get top contributors by location and review count"""
        return self.get_queryset().annotate(
            location_count=Count('user__viewinglocation_set'),
            review_count=Count('user__location_reviews')
        ).filter(
            Q(location_count__gt=0) | Q(review_count__gt=0)
        ).order_by('-location_count', '-review_count')