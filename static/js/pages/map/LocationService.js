// API Service for handling all data fetching:
export class LocationService {
    static getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    static async getLocationStatus(locationId) {
        const response = await fetch(`/api/locations/${locationId}/favorite/`, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to get location status');
        return response.json();
    }

    static async toggleFavorite(locationID, currentlyFavorited) {
        const endpoint = currentlyFavorited ? 'unfavorite' : 'favorite';
        const response = await fetch(`/api/locations/${locationID}/${endpoint}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error(`Failed to ${endpoint} location`);
        return response.json();
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