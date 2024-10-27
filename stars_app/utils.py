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
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x_tile, y_tile, zoom

    def _get_pixel_coords(self, lat, lon, tile_x, tile_y, zoom):
        """Get exact pixel coordinates within a tile"""
        n = 2.0 ** zoom
        lat_rad = math.radians(lat)
        x = ((lon + 180.0) / 360.0 * n - tile_x) * 256
        y = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n - tile_y) * 256
        return int(x), int(y)

    def calculate_light_pollution(self, lat, lon, radius_km=10):
        try:
            """Calculate average light pollution value for an area"""
            zoom = 8  # Use maximum zoom for best resolution
            tile_x, tile_y, zoom = self._get_tile_coords(lat, lon, zoom)
            pixel_x, pixel_y = self._get_pixel_coords(lat, lon, tile_x, tile_y, zoom)

            logger.debug(f"Calculating light pollution for:")
            logger.debug(f"Lat/Lon: {lat}, {lon}")
            logger.debug(f"Tile coordinates: {tile_x}, {tile_y}, zoom: {zoom}")
            logger.debug(f"Pixel coordinates: {pixel_x}, {pixel_y}")

            # Load tile image
            tile_path = os.path.join(self.tiles_dir, str(zoom), str(tile_x), f"{tile_y}.png")
            logger.debug(f"Looking for tile at: {tile_path}")

            if not os.path.exists(tile_path):
                logger.warning(f"Tile not found at: {tile_path}")
                return None

            with Image.open(tile_path) as img:
                # Convert to grayscale for light pollution intensity
                img_gray = img.convert('L')
                data = np.array(img_gray)

                # Add debugging for pixel values
                logger.debug(f"Pixel value range in tile: min={data.min()}, max={data.max()}")
                logger.debug(f"Center pixel value: {data[pixel_y, pixel_x]}")

                # Calculate pixel radius based on zoom level and radius_km
                pixels_per_km = 256 / (40075 * math.cos(math.radians(lat)) / (2 ** zoom))
                pixel_radius = int(radius_km * pixels_per_km)

                # Create circular mask
                y, x = np.ogrid[-pixel_y:256 - pixel_y, -pixel_x:256 - pixel_x]
                mask = x * x + y * y <= pixel_radius * pixel_radius

                logger.debug(f"Mask shape: {mask.shape}")
                logger.debug(f"Number of pixels in mask: {np.sum(mask)}")

                # Calculate average light pollution in the masked area
                if mask.any():
                    masked_data = data[mask]
                    mean_value = float(masked_data.mean())
                    logger.debug(f"Mean value calculated: {mean_value}")
                    logger.debug(f"Values in sample: min={masked_data.min()}, max={masked_data.max()}")
                    return mean_value
                else:
                    logger.warning("No pixels found in mask")
                    return None

        except Exception as e:
            logger.error(f"Error in calculate_light_pollution: {str(e)}", exc_info=True)
            return None

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

    def calculate_quality_score(self, latitude, longitude, elevation=0, viewing_radius_km=10):
        try:
            logger.debug(f"\nCalculating quality score for location: {latitude}, {longitude}")

            # Get light pollution value for the location
            light_pollution = self.calculate_light_pollution(
                latitude,
                longitude,
                radius_km=viewing_radius_km
            )

            logger.debug(f"Raw light pollution value: {light_pollution}")

            # Extensive error checking for light pollution value
            if light_pollution is None:
                logger.warning("Light pollution value is None")
                return 0

            if not isinstance(light_pollution, (int, float)):
                logger.warning(f"Invalid light pollution value type: {type(light_pollution)}")
                return 0

            if math.isnan(light_pollution):
                logger.warning("Light pollution value is NaN")
                return 0

            # Normalize light pollution (0-255) to 0-100 scale and invert
            # (lower light pollution is better)
            # Invert and scale the score
            if light_pollution < 2:  # Very bright urban areas
                light_score = 0
            elif light_pollution < 5:  # Urban areas
                light_score = 20
            elif light_pollution < 8:  # Suburban areas
                light_score = 40
            elif light_pollution < 12:  # Rural areas
                light_score = 60
            elif light_pollution < 15:  # Dark rural areas
                light_score = 80
            else:  # Very dark areas
                light_score = 100

            logger.debug(f"Calculated light score: {light_score}")

            # Calculate dark sky area score
            # Sample points in a grid within viewing radius
            points = self._sample_area_points(
                latitude,
                longitude,
                viewing_radius_km
            )

            dark_sky_scores = []
            for lat, lon in points:
                pollution = self.calculate_light_pollution(lat, lon, radius_km=1)
                if pollution is not None:
                    if pollution >= 5:
                        dark_score = 0
                    elif pollution >= 4:
                        dark_score = 25
                    elif pollution >= 3:
                        dark_score = 50
                    elif pollution >= 2:
                        dark_score = 75
                    else:
                        dark_score = 100
                    dark_sky_scores.append(dark_score)

            area_score = sum(dark_sky_scores) / len(dark_sky_scores) if dark_sky_scores else 0
            logger.debug(f"Area score: {area_score}")

            # Elevation bonus (higher is better)
            # Assume max practical elevation is 4000m for viewing
            elevation_score = min(100, (elevation / 4000) * 100)
            logger.debug(f"Elevation score: {elevation_score}")

            # Weight the components
            # 50% light pollution at exact location
            # 30% average darkness of surrounding area
            # 20% elevation bonus
            final_score = (
                    0.5 * light_score +
                    0.3 * area_score +
                    0.2 * elevation_score
            )

            return round(final_score, 2)

        except Exception as e:
            logger.error(f"Error in calculate_quality_score: {str(e)}", exc_info=True)
            return 0

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