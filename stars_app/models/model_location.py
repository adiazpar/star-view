# ----------------------------------------------------------------------------------------------------- #
# This model_location.py file defines the Location model:                                               #
#                                                                                                       #
# Purpose:                                                                                              #
# Represents a stargazing viewing location with coordinates, ratings, and quality metrics. This is      #
# the core model of the application, storing all information about places where users can stargaze.     #
#                                                                                                       #
# Key Features:                                                                                         #
# - Geographic data: latitude, longitude, elevation, and address information                            #
# - Quality scoring: Automatic calculation based on elevation and other factors                         #
# - Review aggregation: Tracks average ratings and visitor counts                                       #
# - Verification system: Staff can verify locations with notes and timestamps                           #
# - Automatic enrichment: Calls LocationService on save to fetch address and elevation data             #
#                                                                                                       #
# Service Integration:                                                                                  #
# The save() method automatically calls LocationService.initialize_location_data() for new locations    #
# to enrich data via Mapbox APIs (reverse geocoding, elevation, quality score calculation).             #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
from django.db import models
from django.contrib.auth.models import User
from stars_app.services.location_service import LocationService



class Location(models.Model):
    # Timestamps:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Basic information:
    name = models.CharField(max_length=200)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Geographic data:
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(default=0, help_text="Elevation in meters")

    # Address information (auto-populated via Mapbox):
    formatted_address = models.CharField(max_length=500, blank=True, null=True, help_text="Full formatted address from geocoding")
    administrative_area = models.CharField(max_length=200, blank=True, null=True, help_text="State/Province/Region")
    locality = models.CharField(max_length=200, blank=True, null=True, help_text="City/Town")
    country = models.CharField(max_length=200, blank=True, null=True)

    # Quality metrics:
    quality_score = models.FloatField(null=True, blank=True, help_text="Overall viewing quality score (0-100) based on elevation")

    # Rating aggregation:
    rating_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, help_text="Average rating (0.00-5.00)")

    # Verification (staff only):
    is_verified = models.BooleanField(default=False, help_text="Whether this location has been verified by staff")
    verification_date = models.DateTimeField(null=True, blank=True, help_text="When the location was verified")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_locations', help_text="Staff member who verified this location")
    verification_notes = models.TextField(blank=True, help_text="Staff notes about the verification process")

    # Usage tracking:
    times_reported = models.IntegerField(default=0, help_text="Number of times this location has been reported")
    last_visited = models.DateTimeField(null=True, blank=True, help_text="Last time someone reported visiting this location")
    visitor_count = models.IntegerField(default=0, help_text="Number of unique visitors who have reviewed this location")


    # Delegate to LocationService for data enrichment:
    def update_address_from_coordinates(self):
        return LocationService.update_address_from_coordinates(self)

    def update_elevation_from_mapbox(self):
        return LocationService.update_elevation_from_mapbox(self)

    def calculate_quality_score(self):
        return LocationService.calculate_quality_score(self)


    # Override save to automatically enrich location data for new locations:
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
            print(f"Error saving location: {e}")
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
