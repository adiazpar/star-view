#utils.py

from PIL import Image
import numpy as np
from django.conf import settings
import os
import math

import logging
logger = logging.getLogger('stars_app')


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