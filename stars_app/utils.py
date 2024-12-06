from PIL import Image
import numpy as np
from django.conf import settings
import os
import math
import ephem
from datetime import datetime
from django.utils import timezone

# Email validation:
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

import logging

# ASTRONOMICAL COORDINATES ------------------------------------------ #
class AstronomicalCoordinates:
    """Handle astronomical coordinate conversions and meteor shower data"""

    def __init__(self):
        # IAU MDC meteor shower data with J2000.0 coordinates
        self.meteor_showers = {
            'Quadrantids': {
                'ra_hours': 15.33,      # Right Ascension: 15h 20m
                'dec_deg': 49.7,        # Declination: +49° 42'
                'peak_date': '01-03',   # January 3
                'drift_ra': 0,          # RA drift in degrees per day
                'drift_dec': 0,         # Dec drift in degrees per day
            },
            'Lyrids': {
                'ra_hours': 18.13,      # 18h 08m
                'dec_deg': 33.3,        # +33° 18'
                'peak_date': '04-22',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Eta Aquariids': {
                'ra_hours': 22.47,      # 22h 28m
                'dec_deg': -1.0,        # -01° 00'
                'peak_date': '05-06',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Delta Aquariids': {
                'ra_hours': 22.67,      # 22h 40m
                'dec_deg': -16.4,       # -16° 24'
                'peak_date': '07-30',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Perseids': {
                'ra_hours': 3.28,       # 03h 17m
                'dec_deg': 58.1,        # +58° 06'
                'peak_date': '08-12',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Orionids': {
                'ra_hours': 6.35,       # 06h 21m
                'dec_deg': 15.6,        # +15° 36'
                'peak_date': '10-21',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Leonids': {
                'ra_hours': 10.27,      # 10h 16m
                'dec_deg': 21.8,        # +21° 48'
                'peak_date': '11-17',
                'drift_ra': 0,
                'drift_dec': 0,
            },
            'Geminids': {
                'ra_hours': 7.55,       # 07h 33m
                'dec_deg': 32.4,        # +32° 24'
                'peak_date': '12-14',
                'drift_ra': 0,
                'drift_dec': 0,
            },
        }

    def _normalize_shower_name(self, name):
        """Normalize shower name for consistent matching"""
        if not isinstance(name, str):
            return ''
        return name.strip().lower().replace('-', ' ')

    def get_shower_coordinates(self, shower_name, date=None):
        """
        Get geographic coordinates for a meteor shower's radiant point
        at a specific date and time
        """
        if date is None:
            date = timezone.now()

        # Normalize the shower name
        normalized_name = self._normalize_shower_name(shower_name)

        # Find matching shower
        shower_data = None
        for known_name, data in self.meteor_showers.items():
            if self._normalize_shower_name(known_name) == normalized_name:
                shower_data = data
                break

        if not shower_data:
            print(f"No data found for shower: {shower_name} (normalized: {normalized_name})")
            print(f"Available showers: {list(self.meteor_showers.keys())}")
            return None

        # Create PyEphem observer at nominal location
        observer = ephem.Observer()
        observer.lat = '0'  # Equator
        observer.lon = '0'  # Prime meridian
        observer.date = date

        # Calculate shower radiant position
        ra = shower_data['ra_hours'] * 15  # Convert hours to degrees
        dec = shower_data['dec_deg']

        # Account for radiant drift if applicable
        peak_date = datetime.strptime(f"{date.year}-{shower_data['peak_date']}", "%Y-%m-%d")
        days_from_peak = (date - peak_date.replace(tzinfo=timezone.utc)).days

        ra += shower_data['drift_ra'] * days_from_peak
        dec += shower_data['drift_dec'] * days_from_peak

        # Convert to proper format for PyEphem
        radiant = ephem.Equatorial(math.radians(ra), math.radians(dec))

        # Convert to horizontal coordinates (azimuth/altitude)
        horizontal = ephem.Equatorial(radiant, epoch=date)

        # Calculate the best viewing locations
        viewing_locations = self._calculate_viewing_locations(ra, dec, date)

        return viewing_locations

    def _calculate_viewing_locations(self, ra_deg, dec_deg, date):
        """
        Calculate the optimal viewing location for the given celestial coordinates
        Returns a single optimal viewing location
        """
        # Convert RA to local sidereal time (LST)
        utc = ephem.Date(date)
        lst_hours = (ra_deg / 15 + (utc % 1) * 24) % 24

        # Calculate optimal longitude where the radiant is highest at midnight
        optimal_lon = (lst_hours - 12) * 15

        # For the latitude, we want locations where the radiant gets reasonably high in the sky
        optimal_lat = dec_deg

        # Keep coordinates in valid ranges
        optimal_lat = max(min(optimal_lat, 80), -80)  # Avoid poles
        optimal_lon = ((optimal_lon + 180) % 360) - 180  # Normalize to -180 to 180

        return [{
            'latitude': optimal_lat,
            'longitude': optimal_lon,
            'optimal': True
        }]

    def get_radiant_visibility(self, shower_name, latitude, longitude, date=None):
        """
        Calculate the visibility of a meteor shower from a specific location
        Returns visibility score and best viewing time
        """
        if date is None:
            date = timezone.now()

        shower_data = self.meteor_showers.get(shower_name)
        if not shower_data:
            return None

        observer = ephem.Observer()
        observer.lat = str(latitude)
        observer.lon = str(longitude)
        observer.date = date

        ra = shower_data['ra_hours'] * 15
        dec = shower_data['dec_deg']

        # Calculate radiant's altitude at different times
        best_altitude = 0
        best_time = None

        for hour in range(24):
            observer.date = date.replace(hour=hour)
            radiant = ephem.Equatorial(math.radians(ra), math.radians(dec))
            horizontal = ephem.Equatorial(radiant, epoch=observer.date)

            altitude = math.degrees(ephem.Equatorial(horizontal, epoch=observer.date).dec)

            if altitude > best_altitude:
                best_altitude = altitude
                best_time = hour

        return {
            'best_time': best_time,
            'max_altitude': best_altitude,
            'visibility_score': min(100, max(0, best_altitude * 2))  # 0-100 score
        }


# EMAIL VERIFICATION ------------------------------------------------ #
def is_valid_email(email):
    # Validate email format and domain:
    if not email:
        return False

    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
