from typing import List, Dict, Tuple
import math
from collections import defaultdict


class ClusteringService:
    """Service for clustering map locations for better performance and visualization"""
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth (in km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def get_zoom_cluster_radius(zoom_level: int) -> float:
        """Get clustering radius in km based on zoom level"""
        # Higher zoom = smaller radius (more detailed view)
        base_radius = 100  # km at zoom level 0
        # Use a more aggressive formula for high zoom levels
        if zoom_level >= 16:
            # For zoom 16+, use much smaller clustering radius (50m at zoom 18)
            return 0.05  # 50 meters
        else:
            return base_radius / (2 ** (zoom_level / 2))
    
    @staticmethod
    def cluster_locations(locations: List[Dict], zoom_level: int, 
                         bounds: Dict[str, float] = None) -> List[Dict]:
        """
        Cluster locations based on zoom level and optional bounds
        
        Args:
            locations: List of location dictionaries with lat, lng, and other properties
            zoom_level: Map zoom level (0-20)
            bounds: Optional dict with north, south, east, west bounds
            
        Returns:
            List of clusters and individual locations
        """
        if not locations:
            return []
        
        # Filter by bounds if provided
        if bounds:
            filtered_locations = []
            for loc in locations:
                lat, lng = loc['latitude'], loc['longitude']
                if (bounds['south'] <= lat <= bounds['north'] and 
                    bounds['west'] <= lng <= bounds['east']):
                    filtered_locations.append(loc)
            locations = filtered_locations
        
        # Get clustering radius for this zoom level
        cluster_radius = ClusteringService.get_zoom_cluster_radius(zoom_level)
        
        # Simple grid-based clustering
        clusters = []
        clustered_indices = set()
        
        for i, loc1 in enumerate(locations):
            if i in clustered_indices:
                continue
                
            # Start a new cluster
            cluster = {
                'type': 'cluster',
                'latitude': loc1['latitude'],
                'longitude': loc1['longitude'],
                'locations': [loc1],
                'count': 1,
                'avg_quality_score': loc1.get('quality_score', 0),
                'has_verified': loc1.get('is_verified', False),
                'bounds': {
                    'north': loc1['latitude'],
                    'south': loc1['latitude'],
                    'east': loc1['longitude'],
                    'west': loc1['longitude']
                }
            }
            
            clustered_indices.add(i)
            
            # Find nearby locations to add to cluster
            for j, loc2 in enumerate(locations):
                if j <= i or j in clustered_indices:
                    continue
                    
                distance = ClusteringService.haversine_distance(
                    loc1['latitude'], loc1['longitude'],
                    loc2['latitude'], loc2['longitude']
                )
                
                if distance <= cluster_radius:
                    cluster['locations'].append(loc2)
                    cluster['count'] += 1
                    cluster['avg_quality_score'] += loc2.get('quality_score', 0)
                    cluster['has_verified'] = cluster['has_verified'] or loc2.get('is_verified', False)
                    
                    # Update cluster bounds
                    cluster['bounds']['north'] = max(cluster['bounds']['north'], loc2['latitude'])
                    cluster['bounds']['south'] = min(cluster['bounds']['south'], loc2['latitude'])
                    cluster['bounds']['east'] = max(cluster['bounds']['east'], loc2['longitude'])
                    cluster['bounds']['west'] = min(cluster['bounds']['west'], loc2['longitude'])
                    
                    clustered_indices.add(j)
            
            # Calculate cluster center and average quality
            if cluster['count'] > 1:
                cluster['latitude'] = sum(loc['latitude'] for loc in cluster['locations']) / cluster['count']
                cluster['longitude'] = sum(loc['longitude'] for loc in cluster['locations']) / cluster['count']
                cluster['avg_quality_score'] = cluster['avg_quality_score'] / cluster['count']
                clusters.append(cluster)
            else:
                # Single location, not a cluster
                cluster['locations'][0]['type'] = 'location'
                clusters.append(cluster['locations'][0])
        
        return clusters
    
    @staticmethod
    def expand_cluster(cluster_id: str, locations: List[Dict]) -> List[Dict]:
        """
        Expand a cluster to show individual locations
        This would be called when user clicks on a cluster
        """
        # In a real implementation, cluster_id would help identify which cluster to expand
        # For now, we'll just return the locations as-is
        return [{'type': 'location', **loc} for loc in locations]