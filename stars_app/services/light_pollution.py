import requests
import numpy as np
from django.conf import settings
from django.core.cache import cache
import rasterio
from rasterio.warp import transform_geom
import math
from datetime import datetime, timedelta

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class LightPollutionService:
    """Service for handling light pollution data from multiple sources"""

    def __init__(self):
        # Set up session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.cache_timeout = 60 * 60 * 24  # 24 hours

    def get_light_pollution(self, latitude, longitude):
        """
        Get composite light pollution value from available sources.
        Returns value in mag/arcsec² (higher values = darker skies)
        """
        cache_key = f'light_pollution_{latitude}_{longitude}'
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        try:
            # Try VIIRS data first
            viirs_value = self._get_viirs_value(latitude, longitude)

            # Fall back to WAANSB if VIIRS fails or returns None
            if viirs_value is None:
                waansb_value = self._get_waansb_value(latitude, longitude)
                if waansb_value is not None:
                    cache.set(cache_key, waansb_value, self.cache_timeout)
                    return waansb_value
            else:
                cache.set(cache_key, viirs_value, self.cache_timeout)
                return viirs_value

            return None

        except Exception as e:
            print(f"Error getting light pollution data: {str(e)}")
            return None

    def _get_viirs_value(self, latitude, longitude):
        """Get light pollution data from VIIRS satellite measurements"""
        try:
            # Create bounding box (approximately 10km square)
            west = longitude - 0.05
            south = latitude - 0.05
            east = longitude + 0.05
            north = latitude + 0.05
            area = f"{west},{south},{east},{north}"

            # Request 5 days of data
            url = (
                f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
                f"{settings.NASA_FIRMS_KEY}/VIIRS_SNPP_NRT/{area}/5"
            )

            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = self._process_viirs_csv(response.text)
                if data:
                    return self._calculate_light_pollution(data)
            return None

        except Exception as e:
            print(f"Error fetching VIIRS data: {str(e)}")
            return None

    def _get_waansb_value(self, latitude, longitude):
        """Get light pollution value from World Atlas of Night Sky Brightness"""
        try:
            if not hasattr(settings, 'WAANSB_FILE_PATH'):
                return None

            with rasterio.open(settings.WAANSB_FILE_PATH) as dataset:
                row, col = dataset.index(longitude, latitude)
                value = dataset.read(1)[row, col]
                return self._convert_waansb_value(value)

        except Exception as e:
            print(f"Error reading WAANSB data: {str(e)}")
            return None

    def _process_viirs_csv(self, csv_data):
        """Process VIIRS CSV data to extract relevant measurements"""
        try:
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return None

            headers = lines[0].split(',')
            try:
                bright_idx = headers.index('bright_ti4')
                daynight_idx = headers.index('daynight')
                confidence_idx = headers.index('confidence')
            except ValueError:
                return None

            measurements = []
            for line in lines[1:]:
                if line:
                    parts = line.split(',')
                    if len(parts) >= len(headers):
                        if parts[daynight_idx] == 'N':  # Nighttime only
                            try:
                                brightness = float(parts[bright_idx])
                                confidence = float(parts[confidence_idx])
                                if confidence >= 80:
                                    measurements.append(brightness)
                            except (ValueError, IndexError):
                                continue

            return measurements if measurements else None

        except Exception as e:
            print(f"Error processing VIIRS CSV: {str(e)}")
            return None

    def _calculate_light_pollution(self, measurements):
        """Convert brightness measurements to magnitude per square arcsecond"""
        if not measurements:
            return None

        avg_brightness = sum(measurements) / len(measurements)
        if avg_brightness <= 0:
            return None

        # Convert to magnitude per square arcsecond
        mag_per_arcsec = 20.5 - 2.5 * math.log10(avg_brightness * 1e-9)
        return mag_per_arcsec

    def _convert_waansb_value(self, value):
        """Convert WAANSB stored value to magnitude per square arcsecond"""
        if value <= 0:
            return None
        return 20.5 - 2.5 * math.log10(value)

    def calculate_quality_score(self, mag_per_arcsec):
        """Calculate viewing quality score (0-100) from magnitude per square arcsecond"""
        if mag_per_arcsec is None:
            return None

        # Convert mag/arcsec² to quality score
        # 22+ = excellent, 21.5-22 = good, 20-21.5 = moderate, <20 = poor
        min_mag = 16  # Heavy light pollution
        max_mag = 22  # Excellent dark sky

        score = ((mag_per_arcsec - min_mag) / (max_mag - min_mag)) * 100
        return max(0, min(100, score))