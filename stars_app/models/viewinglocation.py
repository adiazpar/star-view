from django.db import models
from django.contrib.auth.models import User
from datetime import timezone
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django_project import settings
from .forecast import Forecast
from .defaultforecast import defaultforecast
from .base import ViewingLocationBase
from stars_app.services.location_service import LocationService
from stars_app.services.moon_phase_service import MoonPhaseService
from stars_app.managers import ViewingLocationManager


# Viewing Location Model -------------------------------------------- #
class ViewingLocation(ViewingLocationBase):
    name = models.CharField(max_length=200)

    # New address fields:
    formatted_address = models.CharField(max_length=500, blank=True, null=True, help_text="Full formatted address from geocoding or user input")
    administrative_area = models.CharField(max_length=200, blank=True, null=True, help_text="State/Province/Region")
    locality = models.CharField(max_length=200, blank=True, null=True, help_text="City/Town")
    country = models.CharField(max_length=200, blank=True, null=True)

    # Forecast:
    forecast = models.ForeignKey(Forecast, on_delete=models.CASCADE, null=True, blank=True)
    cloudCoverPercentage = models.FloatField(null=True)

    # Light pollution:
    light_pollution_value = models.FloatField(null=True, blank=True, help_text="Light pollution in magnitude per square arcsecond (higher values = darker skies)")

    quality_score = models.FloatField(null=True, blank=True, help_text="Overall viewing quality score (0-100) based on light pollution and elevation")

    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Moon Data:
    moon_phase = models.FloatField(null=True, blank=True, help_text="Current moon phase percentage (0-100)")
    moon_altitude = models.FloatField(null=True, blank=True, help_text="Moon's altitude above horizon in degrees")
    moon_impact_score = models.FloatField(null=True, blank=True, help_text="Score indicating moon's impact on viewing conditions (0-1)")
    next_moonrise = models.DateTimeField(null=True, blank=True)
    next_moonset = models.DateTimeField(null=True, blank=True)

    next_astronomical_dawn = models.DateTimeField(null=True, blank=True)
    next_astronomical_dusk = models.DateTimeField(null=True, blank=True)

    # Verification fields
    is_verified = models.BooleanField(default=False, help_text="Whether this location has been verified")
    verification_date = models.DateTimeField(null=True, blank=True, help_text="When the location was verified")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_locations', help_text="User who verified this location")
    verification_notes = models.TextField(blank=True, help_text="Notes about the verification process")
    
    # Quality control fields
    times_reported = models.IntegerField(default=0, help_text="Number of times this location has been reported")
    last_visited = models.DateTimeField(null=True, blank=True, help_text="Last time someone reported visiting this location")
    visitor_count = models.IntegerField(default=0, help_text="Number of unique visitors who have reviewed this location")
    
    # Categories and Tags
    categories = models.ManyToManyField(
        'LocationCategory',
        blank=True,
        related_name='locations',
        help_text="Categories this location belongs to"
    )
    tags = models.ManyToManyField(
        'LocationTag',
        blank=True,
        related_name='locations',
        help_text="Tags associated with this location"
    )

    # Custom manager
    objects = models.Manager()  # Default manager
    locations = ViewingLocationManager()  # Custom manager

    # Moon Phase methods:
    def get_moon_phase_name(self):
        """Get moon phase name and description"""
        return MoonPhaseService.get_moon_phase_name(self.moon_phase)

    # Delegate methods to services:
    def update_address_from_coordinates(self):
        """Updates address fields using Mapbox reverse geocoding"""
        return LocationService.update_address_from_coordinates(self)

    def update_light_pollution(self):
        """Update light pollution and quality score for this location"""
        return LocationService.update_light_pollution(self)

    def update_elevation_from_mapbox(self):
        """Updates elevation using Mapbox Tilequery API"""
        return LocationService.update_elevation_from_mapbox(self)

    def calculate_quality_score(self):
        """Calculate overall quality score"""
        return LocationService.calculate_quality_score(self)

    def getForecast(self, hours=10):
        """Get forecast data"""
        return LocationService.get_forecast(self, hours)

    def updateForecast(self):
        """Update forecast data"""
        return LocationService.update_forecast(self)

    # Save a location's data:
    def save(self, *args, **kwargs):
        try:
            is_new = not self.pk
            
            # First save to get the ID:
            super().save(*args, **kwargs)
            
            # If this is a new location or coordinates have changed
            if is_new or any(
                    field in kwargs.get('update_fields', [])
                    for field in ['latitude', 'longitude']
            ):
                print(f"Updating data for location {self.name}")
                LocationService.initialize_location_data(self)
                
        except Exception as e:
            print(f"Error saving viewing location: {e}")
            raise


    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude'], name='location_coords_idx'),
            models.Index(fields=['quality_score'], name='quality_score_idx'),
            models.Index(fields=['light_pollution_value'], name='light_pollution_idx'),
            models.Index(fields=['country'], name='country_idx'),
            models.Index(fields=['created_at'], name='created_at_idx'),
            models.Index(fields=['added_by'], name='added_by_idx'),
        ]
        ordering = ['-quality_score', '-created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
