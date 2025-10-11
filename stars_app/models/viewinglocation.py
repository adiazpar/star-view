from django.db import models
from django.contrib.auth.models import User
from datetime import timezone
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django_project import settings
from .base import ViewingLocationBase
from stars_app.services.location_service import LocationService


# Viewing Location Model -------------------------------------------- #
class ViewingLocation(ViewingLocationBase):
    name = models.CharField(max_length=200)

    # New address fields:
    formatted_address = models.CharField(max_length=500, blank=True, null=True, help_text="Full formatted address from geocoding or user input")
    administrative_area = models.CharField(max_length=200, blank=True, null=True, help_text="State/Province/Region")
    locality = models.CharField(max_length=200, blank=True, null=True, help_text="City/Town")
    country = models.CharField(max_length=200, blank=True, null=True)

    quality_score = models.FloatField(null=True, blank=True, help_text="Overall viewing quality score (0-100) based on elevation")

    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Verification fields
    is_verified = models.BooleanField(default=False, help_text="Whether this location has been verified")
    verification_date = models.DateTimeField(null=True, blank=True, help_text="When the location was verified")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_locations', help_text="User who verified this location")
    verification_notes = models.TextField(blank=True, help_text="Notes about the verification process")
    
    # Quality control fields
    times_reported = models.IntegerField(default=0, help_text="Number of times this location has been reported")
    last_visited = models.DateTimeField(null=True, blank=True, help_text="Last time someone reported visiting this location")
    visitor_count = models.IntegerField(default=0, help_text="Number of unique visitors who have reviewed this location")

    # Delegate methods to services:
    def update_address_from_coordinates(self):
        """Updates address fields using Mapbox reverse geocoding"""
        return LocationService.update_address_from_coordinates(self)

    def update_elevation_from_mapbox(self):
        """Updates elevation using Mapbox Tilequery API"""
        return LocationService.update_elevation_from_mapbox(self)

    def calculate_quality_score(self):
        """Calculate overall quality score"""
        return LocationService.calculate_quality_score(self)

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
            models.Index(fields=['country'], name='country_idx'),
            models.Index(fields=['created_at'], name='created_at_idx'),
            models.Index(fields=['added_by'], name='added_by_idx'),
        ]
        ordering = ['-quality_score', '-created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
