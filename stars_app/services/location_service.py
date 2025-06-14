import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from stars_app.services.light_pollution import LightPollutionService


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
    def update_light_pollution(location):
        """Update light pollution and quality score for this location"""
        service = LightPollutionService()
        light_pollution = service.get_light_pollution(
            location.latitude,
            location.longitude
        )
        
        if light_pollution is not None:
            location.light_pollution_value = light_pollution
            location.quality_score = service.calculate_quality_score(light_pollution)
            location.save(update_fields=['light_pollution_value', 'quality_score'])
            return True
        return False

    @staticmethod
    def calculate_quality_score(location):
        """Calculate overall quality score for a location"""
        try:
            score = 0
            has_elevation = location.elevation and location.elevation > 0
            
            # Base weights
            weights = {
                'light_pollution': 0.3,
                'cloud_cover': 0.3,
                'elevation': 0.2 if has_elevation else 0,
                'moon': 0.2
            }
            
            # Redistribute elevation weight if not present
            if not has_elevation:
                weights['light_pollution'] += 0.1
                weights['cloud_cover'] += 0.1
            
            # Light pollution score (higher mag/arcsec² is better)
            if location.light_pollution_value:
                lp_score = min(100, max(0, (location.light_pollution_value - 16) * (100/6)))
                score += lp_score * weights['light_pollution']
            
            # Cloud cover score (lower is better)
            if location.cloudCoverPercentage is not None:
                cloud_score = 100 - location.cloudCoverPercentage
                score += cloud_score * weights['cloud_cover']
            
            # Elevation score (only if elevation > 0)
            if has_elevation:
                elevation_score = min(100, (location.elevation / 4000) * 100)
                score += elevation_score * weights['elevation']
            
            # Moon impact score
            if location.moon_impact_score is not None:
                moon_score = location.moon_impact_score * 100
                score += moon_score * weights['moon']
            
            location.quality_score = round(score, 1)
            location.save(update_fields=['quality_score'])
            return True
            
        except Exception as e:
            print(f"Error calculating quality score: {str(e)}")
            return False

    @staticmethod
    def get_forecast(location, hours=10):
        """Get forecast data for a location"""
        base_url = "https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php"
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        end_time = (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
        
        params = {
            "lat": location.latitude,
            "lon": location.longitude,
            "product": "time-series",
            "begin": start_time,
            "end": end_time,
            "sky": "sky"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            cloud_cover = []
            for value in root.findall(".//parameters/cloud-amount/value"):
                if value.text is not None:
                    cloud_cover.append(int(value.text))
            return cloud_cover[:hours]
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    @staticmethod
    def update_forecast(location):
        """Update forecast data for a location"""
        if not location.forecast.forecast:
            forecast_data = LocationService.get_forecast(location)
            if not forecast_data:
                location.cloudCoverPercentage = -1
                location.forecast.forecast = []
                location.forecast.save()
                return
            location.forecast.forecast = forecast_data
            location.forecast.save()
            
        if location.cloudCoverPercentage == -1:
            return
            
        currentTime = datetime.now().replace(tzinfo=ZoneInfo("America/Denver"))
        beginTime = location.forecast.createTime
        dateDelta = currentTime - beginTime
        days, seconds = dateDelta.days, dateDelta.seconds
        hours = int(days * 24 + seconds / 3600)
        
        if hours >= len(location.forecast.forecast):
            forecast_data = LocationService.get_forecast(location)
            if not forecast_data:
                location.cloudCoverPercentage = -1
                location.forecast.forecast = []
                location.forecast.save()
                return
            location.forecast.forecast = forecast_data
            location.forecast.save()
            
        if hours < len(location.forecast.forecast):
            location.cloudCoverPercentage = location.forecast.forecast[hours]
        else:
            location.cloudCoverPercentage = -1
        location.forecast.save()

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
            LocationService.update_light_pollution(location)
        except Exception as e:
            print(f"Warning: Could not update light pollution: {e}")
            
        try:
            LocationService.update_forecast(location)
        except Exception as e:
            print(f"Warning: Could not update forecast: {e}")
            
        try:
            LocationService.calculate_quality_score(location)
        except Exception as e:
            print(f"Warning: Could not calculate quality score: {e}")