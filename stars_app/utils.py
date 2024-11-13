from PIL import Image
import numpy as np
from django.conf import settings
import os
import math
import ephem
from datetime import datetime, timedelta
from django.utils import timezone

import logging
logger = logging.getLogger('stars_app')


# LIGHT POLLUTION --------------------------------------------------- #

class LightPollutionCalculator:
    def __init__(self, tiles_dir=settings.TILES_DIR):
        self.tiles_dir = tiles_dir

    def _get_tile_coords(self, lat, lon, zoom):
        # Convert lat/lon to tile coords:
        # Returns: tile_x, tile_y, zoom

        if lat < -85.0511 or lat > 85.0511:
            lat = min(max(lat, -85.0511), 85.0511)

        # We need to make sure longitude is in -180 to 180 range
        lon = ((lon + 180) % 360) - 180

        lat_rad = math.radians(lat)
        n = 2.0 ** zoom

        # Get tile coordinates:
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

        # Ensure tiles are within bounds:
        x_tile = min(max(x_tile, 0), n - 1)
        y_tile = min(max(y_tile, 0), n - 1)

        logger.debug(f"""
            Coordinate conversion:
            Input: lat={lat}, lon={lon}
            Zoom level: {zoom}
            Max tiles at this zoom: {n}x{n}
            Output tile coords: x={x_tile}, y={y_tile}
            """)

        return x_tile, y_tile, zoom

    def _get_pixel_coords(self, lat, lon, tile_x, tile_y, zoom):
        # Get exact pixel coordinates within a tile:
        # Returns: pixel_x, pixel_y

        n = 2.0 ** zoom
        lat_rad = math.radians(lat)

        # Calculate precise position within tile:
        x = ((lon + 180.0) / 360.0 * n - tile_x) * 256
        y = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n - tile_y) * 256

        # Ensure pixel coordinates are within tile bounds:
        pixel_x = min(max(int(x), 0), 255)
        pixel_y = min(max(int(y), 0), 255)

        logger.debug(f"""
            Pixel conversion:
            Within tile ({tile_x}, {tile_y}):
            Raw pixel position: x={x}, y={y}
            Bounded pixel coords: x={pixel_x}, y={pixel_y}
            """)

        return pixel_x, pixel_y

    def calculate_light_pollution(self, lat, lon, radius_km=10):
        # Calculate average light pollution value for an area
        try:
            # Validate input coordinates:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.error(f"Invalid coordinates: lat={lat}, lon={lon}")
                return None

            zoom = 8  # Use maximum zoom for best resolution
            tile_x, tile_y, zoom = self._get_tile_coords(lat, lon, zoom)
            pixel_x, pixel_y = self._get_pixel_coords(lat, lon, tile_x, tile_y, zoom)

            logger.debug(f"""
            Light pollution calculation:
            Location: {lat}°, {lon}°
            Tile: ({tile_x}, {tile_y}) at zoom {zoom}
            Pixel: ({pixel_x}, {pixel_y}) within tile
            """)

            # Load tile image
            tile_path = os.path.join(self.tiles_dir, str(zoom), str(tile_x), f"{tile_y}.png")

            if not os.path.exists(tile_path):
                # Tile not found at the provided tile path...
                return None

            with Image.open(tile_path) as img:
                # Convert to grayscale for light pollution intensity
                img_gray = img.convert('L')
                data = np.array(img_gray)

                # Calculate pixel radius based on zoom level and radius_km
                # At zoom level 8, one tile is approx 156km wide...
                km_per_pixel = 156 / 256
                pixel_radius = max(1, int(radius_km / km_per_pixel))

                # Create circular mask
                y, x = np.ogrid[-pixel_y:256 - pixel_y, -pixel_x:256 - pixel_x]
                mask = x * x + y * y <= pixel_radius * pixel_radius

                # Calculate average light pollution in the masked area
                if mask.any():
                    masked_data = data[mask]
                    mean_value = float(masked_data.mean())

                    MIN_OBSERVED = 5.0
                    MAX_OBSERVED = 6.0
                    normalized_value = ((mean_value - MIN_OBSERVED) / (MAX_OBSERVED - MIN_OBSERVED)) * 100

                    return normalized_value
                else:
                    # No pixels found in mask
                    return None

        except Exception as e:
            logger.error(f"Error in calculate_light_pollution: {str(e)}", exc_info=True)
            return None

    def calculate_quality_score(self, latitude, longitude, elevation=0, viewing_radius_km=10):
        try:
            # Get light pollution value for the location
            light_pollution = self.calculate_light_pollution(
                latitude,
                longitude,
                radius_km=viewing_radius_km
            )

            # Error checking light pollution value:
            if light_pollution is None or math.isnan(light_pollution):
                # Light pollution value is none:
                return 0

            light_score = 100 - light_pollution

            # Calculate dark sky area score
            # Sample points in a grid within viewing radius
            points = self._sample_area_points(
                latitude,
                longitude,
                2,
                num_points=4
            )

            dark_sky_scores = []
            for lat, lon in points:
                pollution = self.calculate_light_pollution(lat, lon, radius_km=1)
                if pollution is not None:
                    dark_sky_scores.append(100 - pollution)

            area_score = sum(dark_sky_scores) / len(dark_sky_scores) if dark_sky_scores else 0

            # Elevation bonus (higher is better)
            # Assume max practical elevation is 4000m for viewing
            # elevation_score = min(100, (elevation / 4000) * 100)
            elevation_score = 0

            # Weight the components
            # 50% light pollution at exact location
            # 30% average darkness of surrounding area
            # 20% elevation bonus
            final_score = (
                    0.5 * light_score +
                    0.3 * area_score +
                    0.1 * elevation_score
            )
            return round(final_score, 2)

        except Exception as e:
            logger.error(f"Error in calculate_quality_score: {str(e)}", exc_info=True)
            return 0

    def find_optimal_locations(self, region_bounds, min_distance_km=10):
        """Find optimal viewing locations in a region based on light pollution"""
        min_lat, max_lat, min_lon, max_lon = region_bounds
        optimal_locations = []

        # Grid search with minimum distance constraint
        lat_step = 0.1  # Approximately 11km
        lon_step = 0.1 / math.cos(math.radians((min_lat + max_lat) / 2))

        for lat in np.arange(min_lat, max_lat, lat_step):
            for lon in np.arange(min_lon, max_lon, lon_step):
                pollution_value = self.calculate_light_pollution(lat, lon)
                if pollution_value is not None:
                    # Check minimum distance from existing locations
                    too_close = False
                    for loc in optimal_locations:
                        dist = self.calculate_distance(lat, lon, loc['lat'], loc['lon'])
                        if dist < min_distance_km:
                            too_close = True
                            break

                    if not too_close:
                        optimal_locations.append({
                            'lat': lat,
                            'lon': lon,
                            'pollution_value': pollution_value
                        })

        # Sort by light pollution value (lower is better)
        return sorted(optimal_locations, key=lambda x: x['pollution_value'])

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def _sample_area_points(self, center_lat, center_lon, radius_km, num_points=16):
        points = []
        grid_size = int(math.sqrt(num_points))

        # Convert radius from km to degrees (approximate)
        radius_deg = radius_km / 111.32  # 1 degree ≈ 111.32 km

        # Create a grid of points
        for i in range(grid_size):
            for j in range(grid_size):
                # Calculate offset from center
                offset_lat = radius_deg * (2 * i / (grid_size - 1) - 1)
                offset_lon = radius_deg * (2 * j / (grid_size - 1) - 1) * math.cos(math.radians(center_lat))

                lat = center_lat + offset_lat
                lon = center_lon + offset_lon

                # Only include points within the radius
                if self.calculate_distance(center_lat, center_lon, lat, lon) <= radius_km:
                    points.append((lat, lon))

        return points


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
