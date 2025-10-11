import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from django.conf import settings


class LocationService:
    """Service for handling viewing location business logic"""

    @staticmethod
    def update_address_from_coordinates(location):
        """Updates address fields using Mapbox reverse geocoding"""
        try:
            mapbox_token = settings.MAPBOX_TOKEN
            
            url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                   f"{location.longitude},{location.latitude}.json"
                   f"?access_token={mapbox_token}&types=place,region,country")
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
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
            address_parts = []
            if location.locality:
                address_parts.append(location.locality)
            if location.administrative_area:
                address_parts.append(location.administrative_area)
            if location.country:
                address_parts.append(location.country)
            
            location.formatted_address = ", ".join(filter(None, address_parts))
            location.save(update_fields=[
                'formatted_address', 'administrative_area', 'locality', 'country'
            ])
            
            return True
            
        except Exception as e:
            print(f"Error updating address: {str(e)}")
            return False

    @staticmethod
    def update_elevation_from_mapbox(location):
        """Updates elevation using Mapbox Tilequery API"""
        try:
            mapbox_token = settings.MAPBOX_TOKEN
            
            url = (f"https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/tilequery/"
                   f"{location.longitude},{location.latitude}.json"
                   f"?&access_token={mapbox_token}")
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                elevation = next(
                    (feature['properties']['ele']
                     for feature in data['features']
                     if 'ele' in feature['properties']),
                    None
                )
                
                if elevation is not None:
                    location.elevation = float(elevation)
                    location.save(update_fields=['elevation'])
                    print(f"Updated elevation for {location.name} to {location.elevation}m")
                    return True
            
            print(f"No elevation data found for location: {location.name}")
            return False
            
        except Exception as e:
            print(f"Error updating elevation for {location.name}: {str(e)}")
            return False

    @staticmethod
    def calculate_quality_score(location):
        """Calculate overall quality score for a location based on elevation"""
        try:
            score = 0
            has_elevation = location.elevation and location.elevation > 0

            # Elevation score (only if elevation > 0)
            # Scale elevation from 0-4000m to 0-100 score
            if has_elevation:
                score = min(100, (location.elevation / 4000) * 100)

            location.quality_score = round(score, 1)
            location.save(update_fields=['quality_score'])
            return True

        except Exception as e:
            print(f"Error calculating quality score: {str(e)}")
            return False

    @staticmethod
    def initialize_location_data(location):
        """Initialize all location data after creation"""
        if getattr(settings, 'DISABLE_EXTERNAL_APIS', False):
            return
            
        try:
            LocationService.update_address_from_coordinates(location)
        except Exception as e:
            print(f"Warning: Could not update address: {e}")
            
        try:
            LocationService.update_elevation_from_mapbox(location)
        except Exception as e:
            print(f"Warning: Could not update elevation: {e}")

        try:
            LocationService.calculate_quality_score(location)
        except Exception as e:
            print(f"Warning: Could not calculate quality score: {e}")