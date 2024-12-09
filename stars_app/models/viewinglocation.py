from django.db import models
from django.contrib.auth.models import User
from datetime import timezone
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .forecast import Forecast
from .defaultforecast import defaultforecast
from stars_app.services.light_pollution import LightPollutionService


# Viewing Location Model -------------------------------------------- #
class ViewingLocation(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(help_text="Elevation in meters")

    # New address fields
    formatted_address = models.CharField(max_length=500, blank=True, null=True,
                                         help_text="Full formatted address from geocoding or user input")
    administrative_area = models.CharField(max_length=200, blank=True, null=True,
                                           help_text="State/Province/Region")
    locality = models.CharField(max_length=200, blank=True, null=True,
                                help_text="City/Town")
    country = models.CharField(max_length=200, blank=True, null=True)

    # Forecast
    forecast = models.ForeignKey(
        Forecast,
        on_delete=models.CASCADE,
        default=defaultforecast
    )

    cloudCoverPercentage = models.FloatField(null=True)

    # Light pollution
    light_pollution_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Light pollution in magnitude per square arcsecond (higher values = darker skies)"
    )
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Overall viewing quality score (0-100) based on light pollution and elevation"
    )

    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # Address Methods:
    def update_address_from_coordinates(self):
        """Updates address fields using Mapbox reverse geocoding"""
        try:
            from django.conf import settings
            mapbox_token = settings.MAPBOX_TOKEN

            url = (f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
                   f"{self.longitude},{self.latitude}.json"
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
                        self.country = feature['text']
                    elif 'region' in feature['place_type']:
                        self.administrative_area = feature['text']
                    elif 'place' in feature['place_type']:
                        self.locality = feature['text']

            # Create formatted address
            address_parts = []
            if self.locality:
                address_parts.append(self.locality)
            if self.administrative_area:
                address_parts.append(self.administrative_area)
            if self.country:
                address_parts.append(self.country)

            self.formatted_address = ", ".join(filter(None, address_parts))
            return True

        except Exception as e:
            print(f"Error updating address: {str(e)}")
            return False

    # Add new method for light pollution updates
    def update_light_pollution(self):
        """Update light pollution and quality score for this location"""
        service = LightPollutionService()
        light_pollution = service.get_light_pollution(
            self.latitude,
            self.longitude
        )

        if light_pollution is not None:
            self.light_pollution_value = light_pollution
            self.quality_score = service.calculate_quality_score(light_pollution)
            self.save(update_fields=['light_pollution_value', 'quality_score'])
            return True
        return False

    def save(self, *args, **kwargs):
        # If this is a new location or coordinates have changed, update address
        if not self.pk or any(
                field in kwargs.get('update_fields', [])
                for field in ['latitude', 'longitude']
        ):
            self.update_address_from_coordinates()

        super().save(*args, **kwargs)

        # Then update light pollution if needed
        if not self.pk or any(
                field in kwargs.get('update_fields', [])
                for field in ['latitude', 'longitude']
        ) or self.light_pollution_value is None:
            self.update_light_pollution()

    # Forecast methods:
    def getForecast(self, hours=10):  # gets the forcasted cloud cover with 10 or the maximum the api will supply XXX will only work for the US
        base_url = "https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php"
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        end_time = (datetime.now(timezone.utc) + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "product": "time-series",
            "begin": start_time,
            "end": end_time,
            "sky": "sky"
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an error for bad status codes
            root = ET.fromstring(response.content)
            cloud_cover = []
            for value in root.findall(".//parameters/cloud-amount/value"):
                if value.text is not None:
                    cloud_cover.append(int(value.text))
            return cloud_cover[:hours]
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def updateForecast(self):
        if not self.forecast.forecast:
            forecast_data = self.getForecast()
            if not forecast_data:
                self.cloudCoverPercentage = -1
                self.forecast.forecast = []
                self.forecast.save()
                return
            self.forecast.forecast = forecast_data
            self.forecast.save()
        if self.cloudCoverPercentage == -1:  # if it is outside the US / NDF grid
            return
        currentTime = datetime.now().replace(tzinfo=ZoneInfo("America/Denver"))
        beginTime = self.forecast.createTime
        dateDelta = currentTime - beginTime
        days, seconds = dateDelta.days, dateDelta.seconds
        hours = int(days * 24 + seconds / 3600)
        if hours >= len(self.forecast.forecast):
            forecast_data = self.getForecast()
            if not forecast_data:
                self.cloudCoverPercentage = -1
                self.forecast.forecast = []
                self.forecast.save()
                return
            self.forecast.forecast = forecast_data
            self.forecast.save()
        if hours < len(self.forecast.forecast):
            self.cloudCoverPercentage = self.forecast.forecast[hours]
        else:
            self.cloudCoverPercentage = -1
        self.forecast.save()

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateForecast()
