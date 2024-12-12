import math
import ephem
from datetime import datetime
from django.utils import timezone

# Use the ephem service for moon data:
class MoonService:
    def __init__(self):
        self.moon = ephem.Moon()
        self.sun = ephem.Sun()      # PyCharm can't detect this class but it exists in ephem
        self.observer = ephem.Observer()

    def get_is_nighttime(self, latitude, longitude, time=None):
        """
        Determines if it's currently night at a given location.
        Uses astronomical twilight (-18 degrees) as the threshold.
        """

        self.observer.lat = str(latitude)
        self.observer.lon = str(longitude)

        if time is None:
            time = timezone.now()
        self.observer.date = time

        # Calculate sun's position
        self.sun.compute(self.observer)
        sun_altitude = math.degrees(float(self.sun.alt))

        # If sun is more than 18 degrees below horizon, it's astronomical night
        return sun_altitude < -18

    def get_next_twilight_times(self, latitude, longitude, time=None):
        """
        Calculate the next sunset and sunrise times (astronomical twilight).
        This helps us know when to schedule updates.
        """

        self.observer.lat = str(latitude)
        self.observer.lon = str(longitude)

        if time is None:
            time = timezone.now()
        self.observer.date = time

        # Calculate next sunset and sunrise (astronomical twilight)
        self.observer.horizon = '-18'  # 18 degrees below horizon

        next_sunset = ephem.Date(self.observer.next_setting(self.sun, use_center=True)).datetime()
        next_sunrise = ephem.Date(self.observer.next_rising(self.sun, use_center=True)).datetime()

        return {
            'next_sunset': timezone.make_aware(next_sunset),
            'next_sunrise': timezone.make_aware(next_sunrise)
        }

    def calculate_moon_data(self, latitude, longitude, elevation, time=None):
        """
        Calculate moon position and phase for a specific location and time.
        Returns illumination percentage and position data.
        """

        # Set up the observer at our viewing location:
        self.observer.lat = str(latitude)
        self.observer.lon = str(longitude)
        self.observer.elevation = elevation

        # Use provided time or current time:
        if time is None:
            time = datetime.now()
        self.observer.date = time

        # Calculate moon's position:
        self.moon.compute(self.observer)

        try:
            next_rise = ephem.Date(self.observer.next_rising(self.moon)).datetime()
            next_rise = timezone.make_aware(next_rise)
        except ephem.AlwaysUpError:
            # Moon is currently above horizon - get next setting first
            next_set = ephem.Date(self.observer.next_setting(self.moon)).datetime()
            next_set = timezone.make_aware(next_set)
            # Then we can get the next rise after that
            self.observer.date = next_set
            next_rise = ephem.Date(self.observer.next_rising(self.moon)).datetime()
            next_rise = timezone.make_aware(next_rise)
        except ephem.NeverUpError:
            # Handle case where moon never rises at this location
            next_rise = None

        try:
            next_set = ephem.Date(self.observer.next_setting(self.moon)).datetime()
            next_set = timezone.make_aware(next_set)
        except ephem.AlwaysUpError:
            # Moon never sets at this location (can happen near poles)
            next_set = None
        except ephem.NeverUpError:
            next_set = None

        return {
            'phase_percentage': self.moon.phase,
            'altitude': math.degrees(float(self.moon.alt)),
            'azimuth': math.degrees(float(self.moon.az)),
            'above_horizon': float(self.moon.alt) > 0,
            'illumination': self.moon.phase / 100.0,
            'next_rise': next_rise,
            'next_set': next_set,
        }

    def calculate_moon_impact(self, moon_data):
        """
        Calculate how much the moon impacts viewing conditions.
        Returns a score multiplier between 0 and 1 (1 = no impact, 0 = maximum impact)
        """

        impact_score = 1.0

        # Factor 1: Moon Phase Impact
        # Full moon has more impact than new moon
        phase_impact = 1 - (moon_data['phase_percentage'] / 100)

        # Factor 2: Moon Position Impact
        # Moon below horizon = no impact
        # Moon at zenith = maximum impact
        position_impact = 1.0
        if moon_data['above_horizon']:
            # Convert altitude to a 0-1 scale (0° = horizon, 90° = zenith)
            position_impact = 1 - (moon_data['altitude'] / 90)

        # Combine impacts (phase matters more when moon is above horizon)
        if moon_data['above_horizon']:
            impact_score = (phase_impact * 0.7) + (position_impact * 0.3)
        else:
            impact_score = 1.0  # No impact if moon is below horizon

        return impact_score