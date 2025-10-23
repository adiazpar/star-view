// API Service for handling all data fetching:
export class LocationService {
    static getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    static async getLocationStatus(locationId) {
        // Get location data which includes is_favorited field
        const response = await fetch(`/api/locations/${locationId}/`, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to get location status');
        const data = await response.json();
        return { is_favorited: data.is_favorited };
    }

    static async toggleFavorite(locationID, currentlyFavorited) {
        if (currentlyFavorited) {
            // Unfavorite: First get the favorite ID, then DELETE it
            const favoritesResponse = await fetch('/api/favorite-locations/', {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!favoritesResponse.ok) throw new Error('Failed to fetch favorites');

            const favorites = await favoritesResponse.json();
            const favorite = favorites.results ? favorites.results.find(f => f.location.id === locationID) : null;

            if (!favorite) throw new Error('Favorite not found');

            const response = await fetch(`/api/favorite-locations/${favorite.id}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            if (!response.ok) throw new Error('Failed to unfavorite location');
            return { success: true };
        } else {
            // Favorite: POST to create new favorite
            const response = await fetch('/api/favorite-locations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    location_id: locationID
                })
            });
            if (!response.ok) throw new Error('Failed to favorite location');
            return response.json();
        }
    }

    static async getLocations() {
        // Use optimized map_markers endpoint (97% smaller payload)
        const response = await fetch('/api/locations/map_markers/', {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to fetch viewing locations');
        // Returns simple array - no pagination wrapper
        return response.json();
    }
}