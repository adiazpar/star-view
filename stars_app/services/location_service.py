# ----------------------------------------------------------------------------------------------------- #
# This location_service.py file handles automatic data enrichment for Location objects:                 #
#                                                                                                       #
# 1. Address Enrichment → Fetches city, state/region, and country from coordinates                      #
# 2. Elevation Data → Retrieves elevation in meters from Mapbox terrain API                             #
# 3. Quality Score → Calculates 0-100 stargazing quality score based on elevation                       #
# 4. Initialization → Orchestrates all enrichment operations when a location is created                 #
#                                                                                                       #
# Data Flow:                                                                                            #
# User creates location with coordinates → LocationService enriches with address, elevation, and        #
# quality score → Fully populated location ready for display                                            #
#                                                                                                       #
# Service Layer Pattern:                                                                                #
# This service separates business logic from data models, following Django best practices:              #
# - Models define data structure (what to store)                                                        #
# - Services define business logic (how to process data)                                                #
# - Views coordinate between user requests and services                                                 #
#                                                                                                       #
# External API Dependencies:                                                                            #
# - Mapbox Geocoding API: Reverse geocoding for addresses                                               #
# - Mapbox Tilequery API: Terrain elevation data                                                        #
# - Can be disabled via settings.DISABLE_EXTERNAL_APIS for testing                                      #
#                                                                                                       #
# Usage:                                                                                                #
# - Automatically called when Location.save() is triggered (new locations)                              #
# - Manually triggered via API endpoints for refreshing data                                            #
# - All methods are static and can be called independently                                              #
# ----------------------------------------------------------------------------------------------------- #

# Import tools:
import requests
from django.conf import settings


class LocationService:

    # Maximum elevation for quality score scaling:
    MAX_ELEVATION_METERS = 4000



    # ------------------------------------------------------------------------------------------------- #
    #                                                                                                   #
    #                                       HELPER METHODS                                              #
    #                                                                                                   #
    # ------------------------------------------------------------------------------------------------- #

    # ----------------------------------------------------------------------------- #
    # Makes Mapbox API requests with consistent error handling.                     #
    #                                                                               #
    # Args:   url (str): The Mapbox API URL to request                              #
    # Returns: Response JSON data if successful, None otherwise                     #
    # ----------------------------------------------------------------------------- #
    @staticmethod
    def _make_mapbox_request(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Error: Mapbox API request failed: {error}
            return None

        except ValueError as e:
            # Error: Invalid JSON response from Mapbox: {error}
            return None



    # ------------------------------------------------------------------------------------------------- #
    #                                                                                                   #
    #                                    SERVICE METHODS                                                #
    #                                                                                                   #
    # ------------------------------------------------------------------------------------------------- #

    # Updates address fields using Mapbox reverse geocoding:
    @staticmethod
    def update_address_from_coordinates(location):
        mapbox_token = settings.MAPBOX_TOKEN

        url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
               f"{location.longitude},{location.latitude}.json"
               f"?access_token={mapbox_token}&types=place,region,country")

        data = LocationService._make_mapbox_request(url)
        if not data or not data.get('features'):
            # Warning: No address data found for location: {location.name}
            return False

        # Process the response to extract address components
        for feature in data['features']:
            if 'place_type' in feature:
                if 'country' in feature['place_type']:
                    location.country = feature['text']
                elif 'region' in feature['place_type']:
                    location.administrative_area = feature['text']
                elif 'place' in feature['place_type']:
                    location.locality = feature['text']

        # Create formatted address
        address_parts = [
            part for part in [location.locality, location.administrative_area, location.country]
            if part
        ]

        location.formatted_address = ", ".join(address_parts)
        location.save(update_fields=[
            'formatted_address', 'administrative_area', 'locality', 'country'
        ])

        # Info: Updated address for {location.name}: {location.formatted_address}
        return True


    # Updates elevation using Mapbox Tilequery API:
    @staticmethod
    def update_elevation_from_mapbox(location):
        mapbox_token = settings.MAPBOX_TOKEN

        url = (f"https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/tilequery/"
               f"{location.longitude},{location.latitude}.json"
               f"?&access_token={mapbox_token}")

        data = LocationService._make_mapbox_request(url)
        if not data or not data.get('features'):
            # Warning: No elevation data found for location: {location.name}
            return False

        # Extract elevation from features
        elevation = next(
            (feature['properties']['ele']
             for feature in data['features']
             if 'properties' in feature and 'ele' in feature['properties']),
            None
        )

        if elevation is None:
            # Warning: No elevation property found for location: {location.name}
            return False

        location.elevation = float(elevation)
        location.save(update_fields=['elevation'])
        # Info: Updated elevation for {location.name} to {location.elevation}m
        return True


    # Calculate overall quality score for a location based on elevation.
    # Scales elevation from 0-MAX_ELEVATION_METERS to 0-100 score:
    @staticmethod
    def calculate_quality_score(location):
        try:
            if location.elevation and location.elevation > 0:
                score = min(100, (location.elevation / LocationService.MAX_ELEVATION_METERS) * 100)
            else:
                score = 0

            location.quality_score = round(score, 1)
            location.save(update_fields=['quality_score'])
            # Info: Calculated quality score for {location.name}: {location.quality_score}
            return True

        except Exception as e:
            # Error: Error calculating quality score for {location.name}: {error}
            return False


    # Initialize all location data after creation:
    @staticmethod
    def initialize_location_data(location):
        if getattr(settings, 'DISABLE_EXTERNAL_APIS', False):
            # Info: Skipping external API calls for {location.name} (APIs disabled)
            return

        # Update address from coordinates
        try:
            LocationService.update_address_from_coordinates(location)
        except Exception as e:
            # Warning: Could not update address for {location.name}: {error}
            pass

        # Update elevation from Mapbox
        try:
            LocationService.update_elevation_from_mapbox(location)
        except Exception as e:
            # Warning: Could not update elevation for {location.name}: {error}
            pass

        # Calculate quality score based on elevation
        try:
            LocationService.calculate_quality_score(location)
        except Exception as e:
            # Warning: Could not calculate quality score for {location.name}: {error}
            pass